import json

from typer.testing import CliRunner

from geoagent_harness.cli import app


class FakeResult:
    def model_dump(self, *, mode):
        return {
            "schema_version": "1.0",
            "approval_id": "postgis-promotion-approval-test",
            "plan_sha256": "a" * 64,
            "approval_recorded": True,
            "execution_performed": False,
            "database_modified": False,
        }


def test_cli_records_without_execution(monkeypatch):
    import geoagent_harness.postgis_promotion_approval as module

    monkeypatch.setattr(module, "load_postgis_promotion_plan_result", lambda *a, **k: object())
    monkeypatch.setattr(module, "create_postgis_promotion_approval", lambda **k: object())
    monkeypatch.setattr(module, "persist_postgis_promotion_approval", lambda *a, **k: FakeResult())
    result = CliRunner().invoke(app, [
        "record-postgis-promotion-approval", "plan.json",
        "--approver", "Jay Qi", "--reason", "Approve exact plan.",
    ])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["approval_recorded"] is True
    assert payload["execution_performed"] is False
    assert payload["database_modified"] is False


def test_cli_rejects_nonpositive_validity():
    result = CliRunner().invoke(app, [
        "record-postgis-promotion-approval", "plan.json",
        "--approver", "Jay Qi", "--reason", "Approve exact plan.",
        "--valid-for-minutes", "0",
    ])
    assert result.exit_code == 2
    assert "must be positive" in result.stderr
