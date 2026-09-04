"""Bounded, read-only inspection of one allowlisted PostGIS table."""

from __future__ import annotations

from typing import Protocol

import psycopg
from psycopg import IsolationLevel, sql

from geoagent_harness.mcp_server.settings import MCPSettings, validate_identifier
from geoagent_harness.postgis_inspection.schemas import (
    PostGISColumn,
    PostGISGeometryColumn,
    PostGISInspectionRequest,
    PostGISInspectionResult,
    PostGISKey,
)
from geoagent_harness.verifier.postgis import LayerExtent, _read_password

MAX_COLUMNS = 256
MAX_KEYS = 256
MAX_GEOMETRY_COLUMNS = 8
MAX_GEOMETRY_TYPES = 32
STATEMENT_TIMEOUT_MS = 10_000


class PostGISInspectionError(RuntimeError):
    """Raised when bounded inspection cannot complete safely."""


class PostGISInspectionReader(Protocol):
    def table_exists(self, schema: str, table: str) -> bool: ...
    def columns(self, schema: str, table: str) -> list[PostGISColumn]: ...
    def keys(self, schema: str, table: str) -> list[tuple[str, str, list[str]]]: ...
    def geometry_metadata(self, schema: str, table: str) -> list[tuple[str, str, int]]: ...
    def row_count(self, schema: str, table: str) -> int: ...
    def geometry_statistics(self, schema: str, table: str, column: str) -> tuple[list[str], int, int, LayerExtent | None]: ...
    def close(self) -> None: ...


class PsycopgPostGISInspectionReader:
    """Fixed-query reader with a read-only transaction and timeout."""

    def __init__(self, settings: MCPSettings) -> None:
        try:
            self._connection = psycopg.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                dbname=settings.postgres_database,
                user=settings.postgres_user,
                password=_read_password(settings.postgres_password_file),
                connect_timeout=5,
            )
            self._connection.read_only = True
            self._connection.isolation_level = (
                IsolationLevel.REPEATABLE_READ
            )
            self._connection.execute(
                "SELECT set_config('statement_timeout', %s, false)",
                (str(STATEMENT_TIMEOUT_MS),),
            )
        except (psycopg.Error, RuntimeError):
            raise PostGISInspectionError(
                "PostGIS inspection connection failed; connection details were redacted"
            ) from None

    def table_exists(self, schema: str, table: str) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass(%s)", (f"{schema}.{table}",))
            row = cursor.fetchone()
        return row is not None and row[0] is not None

    def columns(self, schema: str, table: str) -> list[PostGISColumn]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT ordinal_position, column_name, data_type, is_nullable
                   FROM information_schema.columns
                   WHERE table_schema = %s AND table_name = %s
                   ORDER BY ordinal_position LIMIT %s""",
                (schema, table, MAX_COLUMNS + 1),
            )
            rows = cursor.fetchall()
        if len(rows) > MAX_COLUMNS:
            raise PostGISInspectionError("PostGIS column metadata exceeds the inspection bound")
        return [PostGISColumn(ordinal_position=int(r[0]), name=str(r[1]), data_type=str(r[2]), nullable=r[3] == "YES") for r in rows]

    def keys(self, schema: str, table: str) -> list[tuple[str, str, list[str]]]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT c.contype, c.conname,
                          array_agg(a.attname ORDER BY u.ordinality)
                   FROM pg_catalog.pg_constraint AS c
                   JOIN pg_catalog.pg_class AS t ON t.oid = c.conrelid
                   JOIN pg_catalog.pg_namespace AS n ON n.oid = t.relnamespace
                   JOIN unnest(c.conkey) WITH ORDINALITY AS u(attnum, ordinality) ON TRUE
                   JOIN pg_catalog.pg_attribute AS a ON a.attrelid = t.oid AND a.attnum = u.attnum
                   WHERE n.nspname = %s AND t.relname = %s AND c.contype IN ('p', 'u')
                   GROUP BY c.contype, c.conname ORDER BY c.contype, c.conname LIMIT %s""",
                (schema, table, MAX_KEYS + 1),
            )
            rows = cursor.fetchall()
        if len(rows) > MAX_KEYS:
            raise PostGISInspectionError("PostGIS key metadata exceeds the inspection bound")
        return [(str(r[0]), str(r[1]), [str(v) for v in r[2]]) for r in rows]

    def geometry_metadata(self, schema: str, table: str) -> list[tuple[str, str, int]]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT f_geometry_column, type, srid FROM geometry_columns
                   WHERE f_table_schema = %s AND f_table_name = %s
                   ORDER BY f_geometry_column LIMIT %s""",
                (schema, table, MAX_GEOMETRY_COLUMNS + 1),
            )
            rows = cursor.fetchall()
        if len(rows) > MAX_GEOMETRY_COLUMNS:
            raise PostGISInspectionError("PostGIS geometry metadata exceeds the inspection bound")
        return [(str(r[0]), str(r[1]).upper(), int(r[2])) for r in rows]

    def row_count(self, schema: str, table: str) -> int:
        query = sql.SQL("SELECT count(*)::bigint FROM {}.{}").format(sql.Identifier(schema), sql.Identifier(table))
        with self._connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
        if row is None:
            raise PostGISInspectionError("PostGIS count query returned no result")
        return int(row[0])

    def geometry_statistics(self, schema: str, table: str, column: str) -> tuple[list[str], int, int, LayerExtent | None]:
        query = sql.SQL("""SELECT array_remove(array_agg(DISTINCT GeometryType({g})), NULL),
            count(*) FILTER (WHERE {g} IS NULL)::bigint,
            count(*) FILTER (WHERE {g} IS NOT NULL AND NOT ST_IsValid({g}))::bigint,
            ST_XMin(ST_Extent({g})), ST_YMin(ST_Extent({g})),
            ST_XMax(ST_Extent({g})), ST_YMax(ST_Extent({g}))
            FROM {s}.{t}""").format(g=sql.Identifier(column), s=sql.Identifier(schema), t=sql.Identifier(table))
        with self._connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
        if row is None:
            raise PostGISInspectionError("PostGIS geometry query returned no result")
        types = sorted(str(v).upper() for v in (row[0] or []))
        if len(types) > MAX_GEOMETRY_TYPES:
            raise PostGISInspectionError("Observed geometry types exceed the inspection bound")
        extent = None
        if all(v is not None for v in row[3:7]):
            extent = LayerExtent(min_x=float(row[3]), min_y=float(row[4]), max_x=float(row[5]), max_y=float(row[6]))
        return types, int(row[1]), int(row[2]), extent

    def close(self) -> None:
        self._connection.close()


def inspect_postgis_table(*, request: PostGISInspectionRequest, settings: MCPSettings, reader: PostGISInspectionReader | None = None) -> PostGISInspectionResult:
    """Inspect one exact allowlisted relation without accepting arbitrary SQL."""
    validate_identifier(request.target_schema, label="target_schema")
    validate_identifier(request.target_table, label="target_table")
    if request.target_schema not in settings.allowed_schemas:
        raise PostGISInspectionError(f"target schema {request.target_schema!r} is not allowed; allowed: {', '.join(sorted(settings.allowed_schemas))}")
    active = reader
    owns_reader = reader is None
    try:
        if active is None:
            active = PsycopgPostGISInspectionReader(settings)
        if not active.table_exists(request.target_schema, request.target_table):
            return PostGISInspectionResult(status="not_found", target_schema=request.target_schema, target_table=request.target_table, table_exists=False, columns=[], primary_key=None, unique_keys=[], geometry_columns=[], warnings=["Target table does not exist."])
        columns = active.columns(request.target_schema, request.target_table)
        raw_keys = active.keys(request.target_schema, request.target_table)
        primary = next((PostGISKey(name=n, columns=c) for kind, n, c in raw_keys if kind == "p"), None)
        unique = [PostGISKey(name=n, columns=c) for kind, n, c in raw_keys if kind == "u"]
        geometries = []
        for name, declared_type, srid in active.geometry_metadata(request.target_schema, request.target_table):
            types, nulls, invalid, extent = active.geometry_statistics(request.target_schema, request.target_table, name)
            geometries.append(PostGISGeometryColumn(name=name, declared_type=declared_type, srid=srid, observed_types=types, null_count=nulls, invalid_count=invalid, extent=extent))
        return PostGISInspectionResult(status="inspected", target_schema=request.target_schema, target_table=request.target_table, table_exists=True, row_count=active.row_count(request.target_schema, request.target_table), columns=columns, primary_key=primary, unique_keys=unique, geometry_columns=geometries, warnings=[])
    except psycopg.Error:
        raise PostGISInspectionError("PostGIS inspection failed; database details were redacted") from None
    finally:
        if owns_reader and active is not None:
            active.close()
