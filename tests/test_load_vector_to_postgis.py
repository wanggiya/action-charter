from pathlib import Path

import geopandas as gpd
import pytest

from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.skills.load_vector_to_postgis.service import (
    LoadVectorError,
    load_vector_to_postgis,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = PROJECT_ROOT / "data" / "input"
SAMPLE = INPUT_ROOT / "sample_points.geojson"


class FakeAdapter:
    def __init__(
        self,
        *,
        schema_exists: bool = True,
        table_exists: bool = False,
    ) -> None:
        self._schema_exists = schema_exists
        self._table_exists = table_exists
        self.written = False
        self.closed = False
        self.schema: str | None = None
        self.table: str | None = None
        self.row_count: int | None = None

    def schema_exists(self, schema: str) -> bool:
        return self._schema_exists

    def table_exists(
        self,
        schema: str,
        table: str,
    ) -> bool:
        return self._table_exists

    def write(
        self,
        frame: gpd.GeoDataFrame,
        *,
        schema: str,
        table: str,
    ) -> None:
        self.written = True
        self.schema = schema
        self.table = table
        self.row_count = len(frame)

    def close(self) -> None:
        self.closed = True


def make_settings(
    tmp_path: Path,
    *,
    writes: bool,
    overwrite: bool = False,
) -> MCPSettings:
    return MCPSettings(
        input_root=INPUT_ROOT,
        output_root=tmp_path / "output",
        enable_write_tools=writes,
        allow_overwrite=overwrite,
        allowed_schemas=frozenset({"agent_sandbox"}),
    )


def test_write_disabled_fails_closed(
    tmp_path: Path,
) -> None:
    adapter = FakeAdapter()

    with pytest.raises(
        LoadVectorError,
        match="write tools are disabled",
    ):
        load_vector_to_postgis(
            path=SAMPLE,
            target_schema="agent_sandbox",
            target_table="sample_points",
            settings=make_settings(
                tmp_path,
                writes=False,
            ),
            adapter=adapter,
        )

    assert adapter.written is False


def test_unapproved_schema_is_rejected(
    tmp_path: Path,
) -> None:
    adapter = FakeAdapter()

    with pytest.raises(
        LoadVectorError,
        match="not allowed",
    ):
        load_vector_to_postgis(
            path=SAMPLE,
            target_schema="public",
            target_table="sample_points",
            settings=make_settings(
                tmp_path,
                writes=True,
            ),
            adapter=adapter,
        )

    assert adapter.written is False


def test_missing_schema_is_rejected(
    tmp_path: Path,
) -> None:
    adapter = FakeAdapter(schema_exists=False)

    with pytest.raises(
        LoadVectorError,
        match="does not exist",
    ):
        load_vector_to_postgis(
            path=SAMPLE,
            target_schema="agent_sandbox",
            target_table="sample_points",
            settings=make_settings(
                tmp_path,
                writes=True,
            ),
            adapter=adapter,
        )

    assert adapter.written is False


def test_existing_table_is_rejected(
    tmp_path: Path,
) -> None:
    adapter = FakeAdapter(table_exists=True)

    with pytest.raises(
        LoadVectorError,
        match="overwrite is disabled",
    ):
        load_vector_to_postgis(
            path=SAMPLE,
            target_schema="agent_sandbox",
            target_table="sample_points",
            settings=make_settings(
                tmp_path,
                writes=True,
            ),
            adapter=adapter,
        )

    assert adapter.written is False


def test_destructive_replacement_remains_blocked(
    tmp_path: Path,
) -> None:
    adapter = FakeAdapter(table_exists=True)

    with pytest.raises(
        LoadVectorError,
        match="destructive replacement",
    ):
        load_vector_to_postgis(
            path=SAMPLE,
            target_schema="agent_sandbox",
            target_table="sample_points",
            settings=make_settings(
                tmp_path,
                writes=True,
                overwrite=True,
            ),
            adapter=adapter,
        )

    assert adapter.written is False


def test_new_table_is_loaded_pending_validation(
    tmp_path: Path,
) -> None:
    adapter = FakeAdapter()

    result = load_vector_to_postgis(
        path=SAMPLE,
        target_schema="agent_sandbox",
        target_table="sample_points",
        settings=make_settings(
            tmp_path,
            writes=True,
        ),
        adapter=adapter,
    )

    assert result.status == "loaded_pending_validation"
    assert result.validation_required is True
    assert result.target_schema == "agent_sandbox"
    assert result.target_table == "sample_points"
    assert result.row_count == 2
    assert result.srid == 4326

    assert adapter.written is True
    assert adapter.schema == "agent_sandbox"
    assert adapter.table == "sample_points"
    assert adapter.row_count == 2


@pytest.mark.parametrize(
    "table",
    [
        "Bad-Name",
        "public.sample",
        "sample;drop_table",
        "1sample",
        "sample points",
    ],
)
def test_unsafe_table_identifier_is_rejected(
    tmp_path: Path,
    table: str,
) -> None:
    adapter = FakeAdapter()

    with pytest.raises(ValueError, match="target_table"):
        load_vector_to_postgis(
            path=SAMPLE,
            target_schema="agent_sandbox",
            target_table=table,
            settings=make_settings(
                tmp_path,
                writes=True,
            ),
            adapter=adapter,
        )

    assert adapter.written is False