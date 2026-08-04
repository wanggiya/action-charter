"""Deterministic, read-only PostGIS layer verification."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import psycopg
from psycopg import sql
from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
    validate_identifier,
)


class PostGISVerificationError(RuntimeError):
    """Raised when deterministic validation cannot run."""


class ValidationCheck(BaseModel):
    """One deterministic validation assertion."""

    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    expected: bool | int | str | None
    actual: bool | int | str | None


class LayerExtent(BaseModel):
    """PostGIS layer extent."""

    model_config = ConfigDict(extra="forbid")

    min_x: float
    min_y: float
    max_x: float
    max_y: float


class LayerStatistics(BaseModel):
    """Facts read from one PostGIS geometry table."""

    model_config = ConfigDict(extra="forbid")

    row_count: int = Field(ge=0)
    null_geometry_count: int = Field(ge=0)
    invalid_geometry_count: int = Field(ge=0)
    geometry_types: list[str]
    extent: LayerExtent | None


class PostGISValidationResult(BaseModel):
    """Secret-free result from deterministic verification."""

    model_config = ConfigDict(extra="forbid")

    status: str
    passed: bool

    target_schema: str
    target_table: str

    table_exists: bool
    geometry_column_exists: bool
    geometry_column: str | None

    row_count: int | None
    srid: int | None
    geometry_type: str | None
    invalid_geometry_count: int | None
    null_geometry_count: int | None
    extent: LayerExtent | None

    checks: list[ValidationCheck]
    warnings: list[str]


class PostGISReader(Protocol):
    """Narrow read-only database interface."""

    def table_exists(
        self,
        schema: str,
        table: str,
    ) -> bool:
        """Return whether the relation exists."""

    def geometry_metadata(
        self,
        schema: str,
        table: str,
    ) -> tuple[str, str, int] | None:
        """Return geometry column, declared type, and SRID."""

    def statistics(
        self,
        schema: str,
        table: str,
        geometry_column: str,
    ) -> LayerStatistics:
        """Return deterministic geometry statistics."""

    def close(self) -> None:
        """Release database resources."""


def _read_password(path: Path) -> str:
    try:
        password = path.read_text(
            encoding="utf-8"
        ).strip()
    except OSError as exc:
        raise PostGISVerificationError(
            "PostGIS credential file is unavailable"
        ) from exc

    if not password:
        raise PostGISVerificationError(
            "PostGIS credential file is empty"
        )

    return password


class PsycopgPostGISReader:
    """Read-only PostGIS implementation using fixed SQL."""

    def __init__(self, settings: MCPSettings) -> None:
        password = _read_password(
            settings.postgres_password_file
        )

        try:
            self._connection = psycopg.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                dbname=settings.postgres_database,
                user=settings.postgres_user,
                password=password,
                connect_timeout=5,
            )

            # Every transaction from this connection is read-only.
            self._connection.read_only = True
        except psycopg.Error:
            raise PostGISVerificationError(
                "PostGIS connection failed; "
                "connection details were redacted"
            ) from None

    def table_exists(
        self,
        schema: str,
        table: str,
    ) -> bool:
        relation = f"{schema}.{table}"

        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT to_regclass(%s)",
                (relation,),
            )
            row = cursor.fetchone()

        return row is not None and row[0] is not None

    def geometry_metadata(
        self,
        schema: str,
        table: str,
    ) -> tuple[str, str, int] | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    f_geometry_column,
                    type,
                    srid
                FROM geometry_columns
                WHERE f_table_schema = %s
                  AND f_table_name = %s
                ORDER BY f_geometry_column
                """,
                (schema, table),
            )

            rows = cursor.fetchall()

        if not rows:
            return None

        if len(rows) != 1:
            raise PostGISVerificationError(
                "MVP validation requires exactly one "
                "registered geometry column"
            )

        geometry_column, geometry_type, srid = rows[0]

        return (
            str(geometry_column),
            str(geometry_type).upper(),
            int(srid),
        )

    def statistics(
        self,
        schema: str,
        table: str,
        geometry_column: str,
    ) -> LayerStatistics:
        query = sql.SQL(
            """
            SELECT
                count(*)::bigint,
                count(*) FILTER (
                    WHERE {geometry} IS NULL
                )::bigint,
                count(*) FILTER (
                    WHERE {geometry} IS NOT NULL
                      AND NOT ST_IsValid({geometry})
                )::bigint,
                array_remove(
                    array_agg(
                        DISTINCT GeometryType({geometry})
                    ),
                    NULL
                ),
                ST_XMin(ST_Extent({geometry})),
                ST_YMin(ST_Extent({geometry})),
                ST_XMax(ST_Extent({geometry})),
                ST_YMax(ST_Extent({geometry}))
            FROM {schema}.{table}
            """
        ).format(
            geometry=sql.Identifier(geometry_column),
            schema=sql.Identifier(schema),
            table=sql.Identifier(table),
        )

        with self._connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

        if row is None:
            raise PostGISVerificationError(
                "PostGIS statistics query returned no result"
            )

        (
            row_count,
            null_count,
            invalid_count,
            geometry_types,
            min_x,
            min_y,
            max_x,
            max_y,
        ) = row

        extent = None

        if all(
            value is not None
            for value in (min_x, min_y, max_x, max_y)
        ):
            extent = LayerExtent(
                min_x=float(min_x),
                min_y=float(min_y),
                max_x=float(max_x),
                max_y=float(max_y),
            )

        normalized_types = sorted(
            str(value).upper()
            for value in (geometry_types or [])
        )

        return LayerStatistics(
            row_count=int(row_count),
            null_geometry_count=int(null_count),
            invalid_geometry_count=int(invalid_count),
            geometry_types=normalized_types,
            extent=extent,
        )

    def close(self) -> None:
        self._connection.close()


def _check(
    name: str,
    *,
    passed: bool,
    expected: bool | int | str | None,
    actual: bool | int | str | None,
) -> ValidationCheck:
    return ValidationCheck(
        name=name,
        passed=passed,
        expected=expected,
        actual=actual,
    )


def validate_postgis_layer(
    *,
    target_schema: str,
    target_table: str,
    settings: MCPSettings,
    expected_row_count: int | None = None,
    expected_srid: int | None = None,
    expected_geometry_type: str | None = None,
    reader: PostGISReader | None = None,
) -> PostGISValidationResult:
    """Validate one allowlisted PostGIS layer without modifying it."""
    validate_identifier(
        target_schema,
        label="target_schema",
    )
    validate_identifier(
        target_table,
        label="target_table",
    )

    if target_schema not in settings.allowed_schemas:
        allowed = ", ".join(
            sorted(settings.allowed_schemas)
        )

        raise PostGISVerificationError(
            f"target schema {target_schema!r} is not allowed; "
            f"allowed: {allowed}"
        )

    if expected_row_count is not None and expected_row_count < 0:
        raise ValueError(
            "expected_row_count must be non-negative"
        )

    if expected_srid is not None and expected_srid <= 0:
        raise ValueError(
            "expected_srid must be positive"
        )

    expected_type = (
        expected_geometry_type.upper()
        if expected_geometry_type is not None
        else None
    )

    active_reader = reader
    owns_reader = reader is None

    try:
        if active_reader is None:
            active_reader = PsycopgPostGISReader(settings)

        exists = active_reader.table_exists(
            target_schema,
            target_table,
        )

        checks = [
            _check(
                "table_exists",
                passed=exists,
                expected=True,
                actual=exists,
            )
        ]

        if not exists:
            return PostGISValidationResult(
                status="validation_failed",
                passed=False,
                target_schema=target_schema,
                target_table=target_table,
                table_exists=False,
                geometry_column_exists=False,
                geometry_column=None,
                row_count=None,
                srid=None,
                geometry_type=None,
                invalid_geometry_count=None,
                null_geometry_count=None,
                extent=None,
                checks=checks,
                warnings=["Target table does not exist."],
            )

        metadata = active_reader.geometry_metadata(
            target_schema,
            target_table,
        )

        geometry_exists = metadata is not None

        checks.append(
            _check(
                "geometry_column_exists",
                passed=geometry_exists,
                expected=True,
                actual=geometry_exists,
            )
        )

        if metadata is None:
            return PostGISValidationResult(
                status="validation_failed",
                passed=False,
                target_schema=target_schema,
                target_table=target_table,
                table_exists=True,
                geometry_column_exists=False,
                geometry_column=None,
                row_count=None,
                srid=None,
                geometry_type=None,
                invalid_geometry_count=None,
                null_geometry_count=None,
                extent=None,
                checks=checks,
                warnings=[
                    "No registered PostGIS geometry column exists."
                ],
            )

        (
            geometry_column,
            declared_geometry_type,
            srid,
        ) = metadata

        statistics = active_reader.statistics(
            target_schema,
            target_table,
            geometry_column,
        )

        actual_geometry_type = (
            statistics.geometry_types[0]
            if len(statistics.geometry_types) == 1
            else ",".join(statistics.geometry_types)
        )

        checks.append(
            _check(
                "row_count_positive",
                passed=statistics.row_count > 0,
                expected="greater_than_zero",
                actual=statistics.row_count,
            )
        )

        if expected_row_count is not None:
            checks.append(
                _check(
                    "row_count_matches_expected",
                    passed=(
                        statistics.row_count
                        == expected_row_count
                    ),
                    expected=expected_row_count,
                    actual=statistics.row_count,
                )
            )

        checks.append(
            _check(
                "srid_is_positive",
                passed=srid > 0,
                expected="positive_integer",
                actual=srid,
            )
        )

        if expected_srid is not None:
            checks.append(
                _check(
                    "srid_matches_expected",
                    passed=srid == expected_srid,
                    expected=expected_srid,
                    actual=srid,
                )
            )

        checks.append(
            _check(
                "single_geometry_type",
                passed=len(statistics.geometry_types) == 1,
                expected=declared_geometry_type,
                actual=actual_geometry_type,
            )
        )

        checks.append(
            _check(
                "geometry_type_matches_metadata",
                passed=(
                    len(statistics.geometry_types) == 1
                    and actual_geometry_type
                    == declared_geometry_type
                ),
                expected=declared_geometry_type,
                actual=actual_geometry_type,
            )
        )

        if expected_type is not None:
            checks.append(
                _check(
                    "geometry_type_matches_expected",
                    passed=actual_geometry_type == expected_type,
                    expected=expected_type,
                    actual=actual_geometry_type,
                )
            )

        checks.append(
            _check(
                "invalid_geometry_count",
                passed=(
                    statistics.invalid_geometry_count == 0
                ),
                expected=0,
                actual=statistics.invalid_geometry_count,
            )
        )

        checks.append(
            _check(
                "null_geometry_count",
                passed=(
                    statistics.null_geometry_count == 0
                ),
                expected=0,
                actual=statistics.null_geometry_count,
            )
        )

        checks.append(
            _check(
                "extent_exists",
                passed=statistics.extent is not None,
                expected=True,
                actual=statistics.extent is not None,
            )
        )

        passed = all(check.passed for check in checks)

        warnings: list[str] = []

        if not passed:
            warnings.append(
                "One or more deterministic checks failed."
            )

        return PostGISValidationResult(
            status=(
                "validation_passed"
                if passed
                else "validation_failed"
            ),
            passed=passed,
            target_schema=target_schema,
            target_table=target_table,
            table_exists=True,
            geometry_column_exists=True,
            geometry_column=geometry_column,
            row_count=statistics.row_count,
            srid=srid,
            geometry_type=actual_geometry_type,
            invalid_geometry_count=(
                statistics.invalid_geometry_count
            ),
            null_geometry_count=(
                statistics.null_geometry_count
            ),
            extent=statistics.extent,
            checks=checks,
            warnings=warnings,
        )

    except PostGISVerificationError:
        raise
    except Exception:
        raise PostGISVerificationError(
            "PostGIS validation failed; "
            "database details were redacted"
        ) from None
    finally:
        if owns_reader and active_reader is not None:
            active_reader.close()