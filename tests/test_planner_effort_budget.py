"""Limits count failed attempts, share discovery/repair allowances, and preserve state."""
import json
from types import SimpleNamespace

import pytest

from tests.test_planner_conversation import project, Client, turn, read, plan
from tests.test_recipe_discovery import request, final_plan
from geoagent_harness.planner.effort_budget import EffortBudget
from geoagent_harness.model import ModelClientError
from geoagent_harness.model.schemas import ModelRequest, ChatMessage, ModelResult
from geoagent_harness.model.settings import ModelSettingsError


def test_generation_discovery_and_repair_share_four_calls(project):
    bad=final_plan();bad['plan']['steps'][0]['arguments']['path']='missing.csv'
    client=Client(request('search',query='csv'),request('inspect',recipe_id='recipe_inspect_csv'),bad,final_plan())
    result=turn(project,client,'Inspect sample_orders.csv')
    budget=result['context_usage']['effort_budget']
    assert budget['model_calls']==4 and budget['tool_calls']==2
    assert budget['prompt_bytes_total']>result['context_usage']['model_request']['prompt_bytes']
    assert budget['prompt_tokens'] is None and not budget['token_usage_complete']
    assert len(client.requests)==4
    assert result['planner_result'] and not result['execution_performed']


def test_timeout_consumes_attempt_and_is_not_retried(project):
    client=Client(ModelClientError.timeout())
    with pytest.raises(ModelClientError) as caught:turn(project,client)
    receipt=caught.value.planner_diagnostics['effort_budget']
    assert receipt['model_calls']==1 and receipt['stopping_reason']=='model_timeout'
    assert len(client.requests)==1 and read(project)['revision']==0


def test_late_reply_is_discarded_without_commit(project,monkeypatch):
    import geoagent_harness.planner.effort_budget as module
    clock=[0.0]
    monkeypatch.setattr(module,'monotonic',lambda:clock[0])
    monkeypatch.setenv('PLANNER_TURN_TIMEOUT_SECONDS','10')
    class Slow(Client):
        def complete(self,request):
            result=super().complete(request)
            clock[0]=11.0
            return result
    client=Slow({'message':'Ready','plan':plan()})
    with pytest.raises(ModelClientError) as caught:turn(project,client)
    assert caught.value.code=='planner_budget_exhausted'
    assert caught.value.planner_diagnostics['effort_budget']['stopping_reason']=='deadline'
    assert client.requests[0].timeout_seconds==10
    assert read(project)['revision']==0


def test_remaining_time_and_real_token_accounting(monkeypatch):
    import geoagent_harness.planner.effort_budget as module
    clock=[0.0];monkeypatch.setattr(module,'monotonic',lambda:clock[0]);monkeypatch.setenv('PLANNER_TURN_TIMEOUT_SECONDS','20')
    budget=EffortBudget();seen=[]
    def complete(request):
        seen.append(request.timeout_seconds);clock[0]+=3
        return ModelResult(model='fixture',content='{}',prompt_tokens=10,completion_tokens=4)
    client=SimpleNamespace(complete=complete)
    req=ModelRequest(messages=[ChatMessage(role='user',content='test')])
    for _ in range(4):budget.complete(client,req,lambda r:4)
    assert seen==[20,17,14,11]
    assert budget.receipt()['prompt_tokens']==40
    with pytest.raises(ModelClientError):budget.complete(client,req,lambda r:4)
    assert len(seen)==4 and budget.receipt()['stopping_reason']=='model_call_limit'


@pytest.mark.parametrize('value',['nan','inf','0','-1','2401','bad'])
def test_invalid_deadline_is_configuration_error(monkeypatch,value):
    monkeypatch.setenv('PLANNER_TURN_TIMEOUT_SECONDS',value)
    with pytest.raises(ModelSettingsError):EffortBudget()


def test_model_transport_honors_remaining_timeout_without_exposing_it_as_model_input():
    import httpx
    from geoagent_harness.model.client import SharedModelClient
    from geoagent_harness.model.settings import ModelSettings
    observed=[]
    def reply(request):
        observed.append(request)
        return httpx.Response(200,json={'model':'fixture','choices':[{'message':{'content':'{}'}}],'usage':{'prompt_tokens':5,'completion_tokens':2}})
    client=SharedModelClient(ModelSettings(base_url='http://fixture/v1',model='fixture',timeout_seconds=120,max_tokens=100),transport=httpx.MockTransport(reply))
    result=client.complete(ModelRequest(messages=[ChatMessage(role='user',content='test')],timeout_seconds=3))
    assert observed[0].extensions['timeout']['read']==3
    assert 'timeout_seconds' not in json.loads(observed[0].content)
    assert result.prompt_tokens==5 and result.completion_tokens==2
