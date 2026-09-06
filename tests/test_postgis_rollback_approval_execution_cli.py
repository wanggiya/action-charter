import json
from typer.testing import CliRunner
from geoagent_harness.cli import app
class Fake:
    def model_dump(self,*,mode): return {"ok":True}
def test_approval_cli(monkeypatch):
    import geoagent_harness.postgis_rollback_approval as module
    monkeypatch.setattr(module,"create_postgis_rollback_approval",lambda **kwargs:object()); monkeypatch.setattr(module,"persist_postgis_rollback_approval",lambda *args,**kwargs:Fake())
    result=CliRunner().invoke(app,["record-postgis-rollback-approval","ROLLBACK_PLAN.json","--approver","Jay","--reason","Restore"])
    assert result.exit_code==0 and json.loads(result.stdout)=={"ok":True}
def test_execution_cli(monkeypatch):
    import geoagent_harness.postgis_rollback_execution as module
    monkeypatch.setattr(module,"execute_postgis_rollback",lambda **kwargs:object()); monkeypatch.setattr(module,"persist_postgis_rollback_execution",lambda *args,**kwargs:Fake())
    result=CliRunner().invoke(app,["execute-postgis-rollback","ROLLBACK_PLAN.json","--approval-file","APPROVAL.json","--confirm-rollback-plan-sha256","a"*64,"--confirm-approval-sha256","b"*64])
    assert result.exit_code==0 and json.loads(result.stdout)=={"ok":True}
