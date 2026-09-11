from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.geoserver_inspection import (
    GeoServerInspectionError, GeoServerInspectionRequest, inspect_geoserver_layer,
)
from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.skill_registry import load_skill_registry


class FakeReader:
    def __init__(self, values): self.values, self.paths, self.closed = values, [], False
    def read(self, path): self.paths.append(path); return self.values.get(path)
    def close(self): self.closed = True


@pytest.fixture
def settings(tmp_path: Path):
    return MCPSettings(input_root=tmp_path / "in", output_root=tmp_path / "out", allowed_geoserver_workspaces=frozenset({"agent_sandbox"}), allowed_geoserver_datastores=frozenset({"postgis"}))


def test_inspects_exact_publication_without_mutation(settings):
    reader = FakeReader({
        "workspaces/agent_sandbox.json": {"workspace": {"name": "agent_sandbox"}},
        "workspaces/agent_sandbox/datastores/postgis.json": {"dataStore": {"name": "postgis"}},
        "workspaces/agent_sandbox/datastores/postgis/featuretypes/current_layer.json": {"featureType": {"name": "current_layer", "nativeName": "current_layer", "enabled": True, "advertised": True, "srs": "EPSG:4326"}},
        "workspaces/agent_sandbox/layers/current_layer.json": {"layer": {"name": "current_layer", "enabled": True, "advertised": True, "defaultStyle": {"name": "point"}}},
    })
    result = inspect_geoserver_layer(request=GeoServerInspectionRequest(workspace="agent_sandbox", datastore="postgis", layer="current_layer"), settings=settings, reader=reader)
    assert result.status == "inspected"
    assert result.feature_type.srs == "EPSG:4326"
    assert result.published_layer.default_style == "point"
    assert result.geoserver_modified is False
    assert result.arbitrary_rest_path_accepted is False
    assert all(path.endswith(".json") for path in reader.paths)


def test_layer_uses_feature_type_state_when_layer_flags_are_omitted(settings):
    reader = FakeReader({
        "workspaces/agent_sandbox.json": {"workspace": {"name": "agent_sandbox"}},
        "workspaces/agent_sandbox/datastores/postgis.json": {"dataStore": {"name": "postgis"}},
        "workspaces/agent_sandbox/datastores/postgis/featuretypes/current_layer.json": {
            "featureType": {"name": "current_layer", "nativeName": "current_layer", "enabled": True, "advertised": False}
        },
        "workspaces/agent_sandbox/layers/current_layer.json": {
            "layer": {"name": "current_layer", "defaultStyle": {"name": "point"}}
        },
    })
    result = inspect_geoserver_layer(
        request=GeoServerInspectionRequest(workspace="agent_sandbox", datastore="postgis", layer="current_layer"),
        settings=settings, reader=reader,
    )
    assert result.published_layer.enabled is True
    assert result.published_layer.advertised is False


def test_missing_workspace_stops_further_reads(settings):
    reader = FakeReader({})
    result = inspect_geoserver_layer(request=GeoServerInspectionRequest(workspace="agent_sandbox", datastore="postgis", layer="current_layer"), settings=settings, reader=reader)
    assert result.status == "not_found"
    assert reader.paths == ["workspaces/agent_sandbox.json"]


def test_allowlists_and_identifiers_fail_closed(settings):
    with pytest.raises(GeoServerInspectionError, match="workspace"):
        inspect_geoserver_layer(request=GeoServerInspectionRequest(workspace="other", datastore="postgis", layer="current_layer"), settings=settings, reader=FakeReader({}))
    with pytest.raises(ValueError, match="layer"):
        inspect_geoserver_layer(request=GeoServerInspectionRequest(workspace="agent_sandbox", datastore="postgis", layer="../rest"), settings=settings, reader=FakeReader({}))


def test_request_forbids_url_and_method():
    with pytest.raises(ValidationError):
        GeoServerInspectionRequest.model_validate({"workspace": "agent_sandbox", "datastore": "postgis", "layer": "current_layer", "url": "http://evil", "method": "DELETE"})


def test_mismatched_response_identity_fails_closed(settings):
    reader = FakeReader({
        "workspaces/agent_sandbox.json": {"workspace": {"name": "other"}},
    })
    with pytest.raises(GeoServerInspectionError, match="identity"):
        inspect_geoserver_layer(request=GeoServerInspectionRequest(workspace="agent_sandbox", datastore="postgis", layer="current_layer"), settings=settings, reader=reader)


def test_skill_is_registered_read_only():
    skill = load_skill_registry(Path(__file__).resolve().parents[1]).get_skill("inspect_geoserver_layer")
    assert skill.access.value == "read_only"
    assert skill.approval_required is False
