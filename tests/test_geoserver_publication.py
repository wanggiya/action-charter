from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from geoagent_harness.geoserver_inspection import GeoServerInspectionRequest
from geoagent_harness.geoserver_publication import (
    GeoServerPublicationError,
    GeoServerPublicationPlanRequest,
    create_geoserver_publication_approval,
    execute_geoserver_publication,
    plan_geoserver_publication,
    publication_approval_sha256,
    verify_geoserver_publication,
)
from geoagent_harness.mcp_server.settings import MCPSettings


class FakeClient:
    def __init__(self, *, enabled=True, advertised=False, ignore_feature_update=False):
        self.feature_enabled = True
        self.feature_advertised = False
        self.feature_enabled = enabled
        self.feature_advertised = advertised
        self.ignore_feature_update = ignore_feature_update
        self.paths = []
        self.puts = []

    def read(self, path):
        self.paths.append(path)
        if path == "workspaces/geoagent_test.json":
            return {"workspace": {"name": "geoagent_test"}}
        if path == "workspaces/geoagent_test/datastores/actioncharter_postgis.json":
            return {"dataStore": {"name": "actioncharter_postgis"}}
        if path.endswith("/featuretypes/checkpoint3e_sample_points.json"):
            return {"featureType": {"name": "checkpoint3e_sample_points", "nativeName": "checkpoint3e_sample_points", "enabled": self.feature_enabled, "advertised": self.feature_advertised, "srs": "EPSG:4326"}}
        if path.endswith("/layers/checkpoint3e_sample_points.json"):
            return {"layer": {"name": "checkpoint3e_sample_points", "defaultStyle": {"name": "point"}}}
        return None

    def set_feature_type(self, *, workspace, datastore, layer, enabled, advertised):
        self.puts.append(("feature_type", workspace, datastore, layer, enabled, advertised))
        if not self.ignore_feature_update or not advertised:
            self.feature_enabled, self.feature_advertised = enabled, advertised

    def close(self):
        pass


@pytest.fixture
def settings(tmp_path: Path):
    return MCPSettings(
        input_root=tmp_path / "in", output_root=tmp_path / "out",
        allowed_geoserver_workspaces=frozenset({"geoagent_test"}),
        allowed_geoserver_datastores=frozenset({"actioncharter_postgis"}),
    )


@pytest.fixture
def target_request():
    return GeoServerPublicationPlanRequest(
        plan_id="publish-checkpoint3e",
        target=GeoServerInspectionRequest(
            workspace="geoagent_test", datastore="actioncharter_postgis",
            layer="checkpoint3e_sample_points",
        ),
    )


def approved(plan):
    now = datetime(2026, 9, 10, tzinfo=timezone.utc)
    return create_geoserver_publication_approval(
        plan_result=plan, decision="approved", approver="operator",
        reason="Publish exact reviewed layer.", now=now,
        expires_at=now + timedelta(minutes=30),
    )


def test_plan_is_read_only_and_digest_bound(settings, target_request):
    client = FakeClient()
    result = plan_geoserver_publication(request=target_request, settings=settings, reader=client)
    assert result.plan.operation == "enable_and_advertise_existing_layer"
    assert result.plan.rest_method == "PUT"
    assert result.plan.geoserver_modified is False
    assert client.puts == []


def test_plan_rejects_already_published_layer(settings, target_request):
    with pytest.raises(GeoServerPublicationError, match="not ready"):
        plan_geoserver_publication(request=target_request, settings=settings, reader=FakeClient(enabled=True, advertised=True))


def test_execution_requires_write_gate(settings, target_request):
    client = FakeClient()
    plan = plan_geoserver_publication(request=target_request, settings=settings, reader=client)
    approval = approved(plan)
    with pytest.raises(GeoServerPublicationError, match="disabled"):
        execute_geoserver_publication(
            plan_result=plan, approval=approval, settings=settings,
            confirm_plan_sha256=plan.plan_sha256,
            confirm_approval_sha256=publication_approval_sha256(approval), client=client,
        )


def test_execution_revalidates_and_performs_one_authoritative_put(settings, target_request):
    client = FakeClient()
    plan = plan_geoserver_publication(request=target_request, settings=settings, reader=client)
    approval = approved(plan)
    writable = settings.model_copy(update={"enable_write_tools": True})
    result = execute_geoserver_publication(
        plan_result=plan, approval=approval, settings=writable,
        confirm_plan_sha256=plan.plan_sha256,
        confirm_approval_sha256=publication_approval_sha256(approval), client=client,
        now=datetime(2026, 9, 10, 0, 10, tzinfo=timezone.utc),
    )
    assert client.puts == [
        ("feature_type", "geoagent_test", "actioncharter_postgis", "checkpoint3e_sample_points", True, True),
    ]
    assert result.status == "published"
    assert result.after.feature_type.advertised is True
    assert result.after.published_layer.enabled is True
    assert result.after.published_layer.advertised is True
    assert result.arbitrary_rest_path_accepted is False


def test_failed_validation_is_compensated_and_reported(settings, target_request):
    client = FakeClient(ignore_feature_update=True)
    plan = plan_geoserver_publication(request=target_request, settings=settings, reader=client)
    approval = approved(plan)
    result = execute_geoserver_publication(
        plan_result=plan, approval=approval,
        settings=settings.model_copy(update={"enable_write_tools": True}),
        confirm_plan_sha256=plan.plan_sha256,
        confirm_approval_sha256=publication_approval_sha256(approval), client=client,
        now=datetime(2026, 9, 10, 0, 10, tzinfo=timezone.utc),
    )
    assert result.status == "rolled_back"
    assert result.compensation_succeeded is True
    assert result.geoserver_modified is False
    assert result.after.feature_type.advertised is False
    assert result.after.published_layer.enabled is True
    assert result.after.published_layer.advertised is False


def test_execution_rejects_state_drift(settings, target_request):
    client = FakeClient()
    plan = plan_geoserver_publication(request=target_request, settings=settings, reader=client)
    approval = approved(plan)
    client.feature_advertised = True
    writable = settings.model_copy(update={"enable_write_tools": True})
    with pytest.raises(GeoServerPublicationError, match="changed"):
        execute_geoserver_publication(
            plan_result=plan, approval=approval, settings=writable,
            confirm_plan_sha256=plan.plan_sha256,
            confirm_approval_sha256=publication_approval_sha256(approval), client=client,
            now=datetime(2026, 9, 10, 0, 10, tzinfo=timezone.utc),
        )
    assert client.puts == []


def test_independent_verification(settings, target_request):
    client = FakeClient()
    plan = plan_geoserver_publication(request=target_request, settings=settings, reader=client)
    approval = approved(plan)
    writable = settings.model_copy(update={"enable_write_tools": True})
    execution = execute_geoserver_publication(
        plan_result=plan, approval=approval, settings=writable,
        confirm_plan_sha256=plan.plan_sha256,
        confirm_approval_sha256=publication_approval_sha256(approval), client=client,
        now=datetime(2026, 9, 10, 0, 10, tzinfo=timezone.utc),
    )
    verification = verify_geoserver_publication(
        execution=execution, plan_result=plan, settings=settings,
        reader=client,
        now=datetime(2026, 9, 10, 0, 11, tzinfo=timezone.utc),
    )
    assert verification.status == "verified"
    assert verification.execution_claim_trusted is False
    assert verification.geoserver_modified is False


def test_denial_and_wrong_digest_fail_closed(settings, target_request):
    client = FakeClient()
    plan = plan_geoserver_publication(request=target_request, settings=settings, reader=client)
    now = datetime(2026, 9, 10, tzinfo=timezone.utc)
    denial = create_geoserver_publication_approval(
        plan_result=plan, decision="denied", approver="operator",
        reason="Not ready.", now=now,
    )
    writable = settings.model_copy(update={"enable_write_tools": True})
    with pytest.raises(GeoServerPublicationError, match="not approved"):
        execute_geoserver_publication(
            plan_result=plan, approval=denial, settings=writable,
            confirm_plan_sha256=plan.plan_sha256,
            confirm_approval_sha256=publication_approval_sha256(denial), client=client,
        )
    approval = approved(plan)
    with pytest.raises(GeoServerPublicationError, match="plan digest"):
        execute_geoserver_publication(
            plan_result=plan, approval=approval, settings=writable,
            confirm_plan_sha256="0" * 64,
            confirm_approval_sha256=publication_approval_sha256(approval), client=client,
        )
