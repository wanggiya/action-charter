"""Recover exact saved scope independently of the global inventory window."""
import os
import pytest
from geoagent_harness.interface_api.workflow_runs import RunRequest,run_action,_write,_directory
from geoagent_harness.interface_api.server import InterfaceApiError

CHAT='a'*32;PLAN='b'*64

def record(index,chat=CHAT,plan=PLAN,started='2026-10-27T10:00:00+00:00'):
    return {'run_id':f'{index:032x}','conversation_id':chat,'plan_sha256':plan,'status':'completed',
            'started_at':started,'steps':[],'result':{'verified':True}}

def lookup(root,**changes):
    return run_action(RunRequest(action='latest',conversation_id=CHAT,confirmed_plan_sha256=PLAN,**changes),project_root=root)

def test_exact_run_survives_more_than_fifty_unrelated_recent_receipts(tmp_path):
    directory=_directory(tmp_path);wanted=record(1);_write(directory,wanted)
    os.utime(directory/(wanted['run_id']+'.json'),(1,1))
    for i in range(2,58):_write(directory,record(i,chat='c'*32))
    assert wanted['run_id'] not in {r['run_id'] for r in run_action(RunRequest(action='list'),project_root=tmp_path)['records']}
    before={p.name:p.read_bytes() for p in directory.glob('*.json')}
    recovered=lookup(tmp_path)
    assert recovered['record']==wanted and not recovered['execution_performed'] and not recovered['approval_performed']
    assert before=={p.name:p.read_bytes() for p in directory.glob('*.json')}

def test_lookup_selects_newest_start_not_mtime_and_never_other_chat_or_plan(tmp_path):
    directory=_directory(tmp_path)
    for r in (record(1),record(2,started='2026-10-27T11:00:00+00:00'),record(3,chat='c'*32,started='2026-10-27T12:00:00+00:00'),record(4,plan='d'*64,started='2026-10-27T13:00:00+00:00')):_write(directory,r)
    os.utime(directory/(record(1)['run_id']+'.json'),None)
    assert lookup(tmp_path)['record']['run_id']==record(2)['run_id']
    assert run_action(RunRequest(action='latest',conversation_id='e'*32,confirmed_plan_sha256=PLAN),project_root=tmp_path)['record'] is None
    for missing in ({'conversation_id':CHAT},{'confirmed_plan_sha256':PLAN},{}):
        with pytest.raises(InterfaceApiError,match='exact conversation and plan'):
            run_action(RunRequest(action='latest',**missing),project_root=tmp_path)

def test_lookup_does_not_reconcile_unrelated_running_receipts(tmp_path):
    directory=_directory(tmp_path);other=record(2,chat='c'*32);other['status']='running'
    _write(directory,other);_write(directory,record(1))
    path=directory/(other['run_id']+'.json');before=path.read_bytes()
    assert lookup(tmp_path)['record']['run_id']==record(1)['run_id']
    assert path.read_bytes()==before

def test_corrupt_or_over_budget_lookup_is_unavailable_not_missing(tmp_path,monkeypatch):
    directory=_directory(tmp_path);path=directory/(record(1)['run_id']+'.json');path.write_text('broken')
    with pytest.raises(InterfaceApiError,match='unreadable receipt'):lookup(tmp_path)
    path.unlink();_write(directory,record(1))
    import geoagent_harness.interface_api.workflow_runs as module
    ticks=iter([0,4]);monkeypatch.setattr(module.time,'monotonic',lambda:next(ticks,4))
    with pytest.raises(InterfaceApiError,match='exceeded its budget'):lookup(tmp_path)


@pytest.mark.parametrize('foreign',[False,True])
def test_terminal_reuses_scoped_lookup_without_execution_or_authority(foreign):
    from geoagent_harness.chat.workspace import Workspace
    from geoagent_harness.chat.client import ChatError
    recovered=record(1,chat='c'*32 if foreign else CHAT)
    class Client:
        def __init__(self):self.calls=[]
        def post(self,path,payload):
            self.calls.append((path,payload))
            assert payload['action']=='latest'
            return {'record':recovered}
    client=Client();workspace=Workspace(client,CHAT)
    workspace.state={'planner_result':{'plan_sha256':PLAN}}
    if foreign:
        with pytest.raises(ChatError,match='does not match'):workspace.execute('/run')
    else:
        assert recovered['run_id'] in workspace.execute('/run')
        assert workspace.last_run==recovered
    assert workspace.authorization is None
    assert client.calls==[('/api/v1/workflow/runs',{'action':'latest','conversation_id':CHAT,'confirmed_plan_sha256':PLAN})]
