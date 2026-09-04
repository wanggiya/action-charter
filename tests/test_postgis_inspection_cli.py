import json

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.postgis_inspection import PostGISInspectionResult


def test_cli_emits_inspection(monkeypatch):
    import geoagent_harness.postgis_inspection as module

    monkeypatch.setattr(module, "inspect_postgis_table", lambda **kwargs: PostGISInspectionResult(status="inspected", target_schema="agent_sandbox", target_table="sample", table_exists=True, row_count=2, columns=[], primary_key=None, unique_keys=[], geometry_columns=[], warnings=[]))
    result = CliRunner().invoke(app, ["inspect-postgis-table", "--table", "sample"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "inspected"
    assert payload["database_modified"] is False


def test_cli_missing_table_exits_one(monkeypatch):
    import geoagent_harness.postgis_inspection as module

    monkeypatch.setattr(module, "inspect_postgis_table", lambda **kwargs: PostGISInspectionResult(status="not_found", target_schema="agent_sandbox", target_table="missing", table_exists=False, columns=[], primary_key=None, unique_keys=[], geometry_columns=[], warnings=[]))
    result = CliRunner().invoke(app, ["inspect-postgis-table", "--table", "missing"])
    assert result.exit_code == 1

