from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.postgis_inspection import PostGISColumn, PostGISInspectionRequest
from geoagent_harness.postgis_promotion_plan import (
    PostGISPromotionPlanError,
    PostGISPromotionPlanRequest,
    plan_postgis_promotion,
    postgis_promotion_plan_sha256,
)


class FakeReader:
    def __init__(self, *, candidate_rows=2, archive_exists=False):
        self.candidate_rows = candidate_rows
        self.archive_exists = archive_exists
        self.closed = False

    def table_exists(self, schema, table):
        return self.archive_exists if table == "reference_archive" else True

    def columns(self, schema, table):
        return [PostGISColumn(ordinal_position=1, name="id", data_type="integer", nullable=False)]

    def keys(self, schema, table):
        return [("p", f"{table}_pkey", ["id"])]

    def geometry_metadata(self, schema, table):
        return []

    def row_count(self, schema, table):
        return self.candidate_rows if table == "candidate_layer" else 2

    def geometry_statistics(self, schema, table, column):
        raise AssertionError("no geometry columns")

    def close(self):
        self.closed = True


@pytest.fixture
def settings(tmp_path: Path) -> MCPSettings:
    return MCPSettings(
        input_root=tmp_path / "input",
        output_root=tmp_path / "output",
        allowed_schemas=frozenset({"agent_sandbox"}),
    )


def request() -> PostGISPromotionPlanRequest:
    relation = lambda table: PostGISInspectionRequest(
        target_schema="agent_sandbox", target_table=table
    )
    return PostGISPromotionPlanRequest(
        plan_id="checkpoint15d-promotion-v1",
        reference=relation("reference_layer"),
        candidate=relation("candidate_layer"),
        archive=relation("reference_archive"),
    )


def test_compatible_evidence_creates_digest_bound_plan(settings):
    result = plan_postgis_promotion(
        request=request(), settings=settings, reader=FakeReader()
    )
    plan = result.plan
    assert result.plan_sha256 == postgis_promotion_plan_sha256(plan)
    assert plan.assessment.compatible is True
    assert plan.archive.table_exists is False
    assert plan.approval_required_step_ids == [
        "step_4_archive_reference", "step_5_promote_candidate"
    ]
    assert [item.operation for item in plan.operations] == [
        "reverify_assessment", "lock_relations", "verify_archive_absent",
        "archive_reference", "promote_candidate", "validate_promoted_relation",
    ]
    assert plan.transaction_required is True
    assert plan.rollback_required is True
    assert plan.approval_created is False
    assert plan.execution_performed is False
    assert plan.database_modified is False


def test_plan_digest_is_stable(settings):
    first = plan_postgis_promotion(
        request=request(), settings=settings, reader=FakeReader()
    )
    second = plan_postgis_promotion(
        request=request(), settings=settings, reader=FakeReader()
    )
    assert first == second


def test_operation_choreography_cannot_be_reordered(settings):
    result = plan_postgis_promotion(
        request=request(), settings=settings, reader=FakeReader()
    )
    payload = result.plan.model_dump(mode="json")
    payload["operations"][3], payload["operations"][4] = (
        payload["operations"][4],
        payload["operations"][3],
    )
    from geoagent_harness.postgis_promotion_plan import PostGISPromotionPlan

    with pytest.raises(ValidationError, match="choreography"):
        PostGISPromotionPlan.model_validate(payload)


def test_changed_evidence_fails_closed(settings):
    with pytest.raises(PostGISPromotionPlanError, match="compatible"):
        plan_postgis_promotion(
            request=request(),
            settings=settings,
            reader=FakeReader(candidate_rows=3),
        )


def test_existing_archive_fails_closed(settings):
    with pytest.raises(PostGISPromotionPlanError, match="already exists"):
        plan_postgis_promotion(
            request=request(),
            settings=settings,
            reader=FakeReader(archive_exists=True),
        )


def test_relations_must_be_distinct():
    payload = request().model_dump(mode="json")
    payload["archive"] = payload["reference"]
    with pytest.raises(ValidationError, match="must be distinct"):
        PostGISPromotionPlanRequest.model_validate(payload)


def test_request_forbids_sql():
    payload = request().model_dump(mode="json")
    payload["sql"] = "ALTER TABLE anything"
    with pytest.raises(ValidationError, match="sql"):
        PostGISPromotionPlanRequest.model_validate(payload)


def test_unapproved_archive_schema_is_rejected(settings):
    payload = request().model_dump(mode="json")
    payload["archive"]["target_schema"] = "public"
    with pytest.raises(RuntimeError, match="not allowed"):
        plan_postgis_promotion(
            request=PostGISPromotionPlanRequest.model_validate(payload),
            settings=settings,
            reader=FakeReader(),
        )
