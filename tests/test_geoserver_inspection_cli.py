import json

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.geoserver_inspection import GeoServerInspectionResult


def test_cli_emits_bounded_result(monkeypatch):
    import geoagent_harness.geoserver_inspection as module
    monkeypatch.setattr(module, "inspect_geoserver_layer", lambda **kwargs: GeoServerInspectionResult(status="not_found", workspace="agent_sandbox", datastore="postgis", layer="current_layer", workspace_exists=True, datastore_exists=True, warnings=["Feature type and published layer do not exist."]))
    result = CliRunner().invoke(app, ["inspect-geoserver-layer", "--layer", "current_layer"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["geoserver_modified"] is False
