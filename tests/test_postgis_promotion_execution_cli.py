import json

from typer.testing import CliRunner

from geoagent_harness.cli import app


class FakeResult:
    def model_dump(self, *, mode):
        return {"transaction_committed": True, "database_modified": True}


def test_cli_executes_and_persists(monkeypatch):
    import geoagent_harness.postgis_promotion_execution as module

    monkeypatch.setattr(module, "execute_postgis_promotion", lambda **kwargs: object())
    monkeypatch.setattr(module, "persist_postgis_promotion_execution", lambda *args, **kwargs: FakeResult())
    result = CliRunner().invoke(app, [
        "execute-postgis-promotion", "PLAN.json",
        "--approval-file", "package/APPROVAL.json",
        "--confirm-plan-sha256", "a" * 64,
        "--confirm-approval-sha256", "b" * 64,
    ])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["transaction_committed"] is True
    assert payload["database_modified"] is True
