import json

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.postgis_promotion_plan import (
    PostGISPromotionPlanError,
)


def test_cli_emits_non_executing_plan(monkeypatch):
    import geoagent_harness.postgis_promotion_plan as module
    class Result:
        plan_sha256 = "a" * 64

        def model_dump(self, *, mode):
            return {
                "schema_version": "1.0",
                "plan_sha256": self.plan_sha256,
                "execution_performed": False,
            }

    expected = Result()
    monkeypatch.setattr(module, "plan_postgis_promotion", lambda **kwargs: expected)
    result = CliRunner().invoke(app, [
        "plan-postgis-promotion", "--plan-id", "checkpoint15d-promotion-v1",
        "--reference-table", "reference_layer",
        "--candidate-table", "candidate_layer",
        "--archive-table", "reference_archive",
    ])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["plan_sha256"] == expected.plan_sha256
    assert payload["execution_performed"] is False


def test_cli_planning_failure_exits_two(monkeypatch):
    import geoagent_harness.postgis_promotion_plan as module

    def fail(**kwargs):
        raise PostGISPromotionPlanError("not compatible")

    monkeypatch.setattr(module, "plan_postgis_promotion", fail)
    result = CliRunner().invoke(app, [
        "plan-postgis-promotion", "--plan-id", "checkpoint15d-promotion-v1"
    ])
    assert result.exit_code == 2
    assert "not compatible" in result.stderr
