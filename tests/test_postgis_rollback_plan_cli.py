import json

from typer.testing import CliRunner

from geoagent_harness.cli import app


class FakeStorageResult:
    def model_dump(self, *, mode):
        return {"planning_performed": True, "database_modified": False}


def test_cli_plans_and_persists_without_database_mutation(monkeypatch):
    import geoagent_harness.postgis_rollback_plan as module

    monkeypatch.setattr(module, "plan_postgis_rollback", lambda **kwargs: object())
    monkeypatch.setattr(
        module, "persist_postgis_rollback_plan", lambda *args, **kwargs: FakeStorageResult()
    )
    result = CliRunner().invoke(app, [
        "plan-postgis-rollback", "package/VERIFICATION.json",
        "--execution-file", "package/EXECUTION.json",
        "--plan-file", "PLAN.json",
    ])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {"planning_performed": True, "database_modified": False}
