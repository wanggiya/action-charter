import json
from types import SimpleNamespace

import pytest

from geoagent_harness.interface_api.execution_assistance import assist
from geoagent_harness.interface_api.workflow_runs import RunRequest
from geoagent_harness.model import ModelResult
from geoagent_harness.tabular.analytical_service import profile_table


@pytest.fixture
def recorded(tmp_path,monkeypatch):
    monkeypatch.setenv('MODEL_NAME','fixture')
    (tmp_path/'data/input').mkdir(parents=True)
    (tmp_path/'data/input/visits.csv').write_text('id,code,value\nprivate-person,1,2\nprivate-other,2,4\n')
    (tmp_path/'data/input/codes.csv').write_text('code,description\n1,Emergency\n2,Urgent\n')
    outcome=profile_table(tmp_path,'visits.csv',{'codebook_path':'codes.csv'})
    record={'run_id':'a'*32,'plan_sha256':'b'*64,'conversation_id':'c'*32,'status':'completed',
        'steps':[{'step_id':'step_1','skill_id':'inspect_csv','status':'completed','outcome':outcome}]}
    request=RunRequest(action='execution_assistance',run_id='a'*32,confirmed_plan_sha256='b'*64,
        conversation_id='c'*32,step_id='step_1',assistant_question='Check the value summary and definitions')
    return tmp_path,record,request


class Client:
    def __init__(self,replies):self.replies=list(replies);self.requests=[]
    def complete(self,request):
        self.requests.append(request)
        return ModelResult(model='fixture',content=json.dumps(self.replies.pop(0)))


def test_helper_performs_one_scoped_read_then_explains_without_writes(recorded):
    root,record,request=recorded
    original=json.dumps(record,sort_keys=True)
    client=Client([{'message':'Read numeric summary','action':'read_profile','profile_columns':['value'],'numeric_columns':['value']},
                   {'message':'Recorded mean is 3; definitions are supplied, not clinically verified.','action':'explain'}])
    response=assist(root,record,request,model_client=client)
    assert response['model_calls']==2 and response['tool_calls']==1
    assert response['observations'][0]['profiles'][0]['numeric']['mean']==3
    assert response['workflow_changed'] is response['data_written'] is response['approval_performed'] is False
    assert json.dumps(record,sort_keys=True)==original
    assert not (root/'data/output').exists()
    assert 'private-person' not in ''.join(m.content for r in client.requests for m in r.messages)


def test_helper_rejects_repeated_reads_and_unknown_columns(recorded):
    root,record,request=recorded
    with pytest.raises(ValueError,match='repeated'):
        assist(root,record,request,model_client=Client([{'message':'read','action':'read_profile'}, {'message':'again','action':'read_profile'}]))
    with pytest.raises(Exception):
        assist(root,record,request,model_client=Client([{'message':'read','action':'read_profile','profile_columns':['unavailable']}]))


def test_helper_scope_and_untrusted_tool_payload_reject(recorded):
    root,record,request=recorded
    client=Client([])
    with pytest.raises(ValueError,match='matching'):
        assist(root,record,request.model_copy(update={'conversation_id':'d'*32}),model_client=client)
    assert not client.requests
    with pytest.raises(ValueError):
        assist(root,record,request,model_client=Client([{'message':'run it','action':'execute','command':'python arbitrary.py'}]))


def test_failed_step_can_receive_advice_but_not_be_reexecuted(recorded):
    root,record,request=recorded
    record['status']='failed';record['steps'][0]['status']='failed'
    answer=assist(root,record,request,model_client=Client([{'message':'Review the mapping and propose a corrected plan.','action':'propose_revision'}]))
    assert answer['suggested_action']=='propose_revision' and answer['tool_calls']==0
    with pytest.raises(ValueError,match='unavailable'):
        assist(root,record,request,model_client=Client([{'message':'read','action':'read_profile'}]))


def test_run_api_persists_assistance_and_reopen_uses_receipt(recorded,monkeypatch):
    from geoagent_harness.interface_api import workflow_runs,execution_assistance
    root,record,request=recorded
    directory=workflow_runs._directory(root);workflow_runs._write(directory,record)
    calls=[]
    def answer(*args):
        calls.append(True)
        return {'message':'Recorded advice only.','execution_performed':False,'approval_performed':False}
    monkeypatch.setattr(execution_assistance,'assist',answer)
    first=workflow_runs.run_action(request,project_root=root)
    second=workflow_runs.run_action(request,project_root=root)
    stored=json.loads((directory/(record['run_id']+'.json')).read_text())
    assert stored['execution_assistance']['message']==first['message']
    assert second['cached'] and len(calls)==1
    assert stored['status']=='completed' and stored['steps']==record['steps']
