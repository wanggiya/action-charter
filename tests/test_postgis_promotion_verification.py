from datetime import datetime, timezone
from pathlib import Path

from geoagent_harness.postgis_inspection import PostGISInspectionResult
from geoagent_harness.postgis_promotion_verification import (
    PostGISPromotionVerificationResult,
    load_postgis_promotion_verification,
    persist_postgis_promotion_verification,
)


def missing(table: str) -> PostGISInspectionResult:
    return PostGISInspectionResult(
        status="not_found", target_schema="agent_sandbox",
        target_table=table, table_exists=False, columns=[],
        primary_key=None, unique_keys=[], geometry_columns=[],
        warnings=["Target table does not exist."],
    )


def result() -> PostGISPromotionVerificationResult:
    return PostGISPromotionVerificationResult(
        verification_id="postgis-promotion-verification-20260905t120000z-1234abcd",
        execution_id="postgis-promotion-execution-20260905t110000z-1234abcd",
        execution_sha256="a" * 64, plan_id="checkpoint15g-v1",
        plan_sha256="b" * 64, status="failed",
        findings=["promoted_relation_mismatch", "archived_relation_mismatch"],
        promoted_relation=missing("reference_layer"),
        archived_relation=missing("reference_archive"),
    )


def test_verification_storage_round_trip(tmp_path: Path):
    value=result(); root=tmp_path/"verification"
    path=persist_postgis_promotion_verification(value,verification_root=root)
    assert load_postgis_promotion_verification(path,verification_root=root)==value


def test_verification_result_is_non_mutating():
    value=result()
    assert value.database_modified is False
    assert value.execution_claim_trusted is False
