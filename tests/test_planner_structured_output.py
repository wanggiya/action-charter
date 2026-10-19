"""Provider constraints, safe syntax findings and bounded truncation recovery."""
import json
from dataclasses import replace

import httpx
import pytest
from pydantic import ValidationError

from tests.test_planner_conversation import project, Client, turn, read, plan
from tests.test_calculation_planner_repair import PROMPT, ready
from geoagent_harness.model import SharedModelClient, ModelClientError
from geoagent_harness.model.schemas import ModelRequest, ChatMessage, ModelResult
from geoagent_harness.model.settings import ModelSettings, load_model_settings, ModelSettingsError
from geoagent_harness.interface_api.conversation import Reply
from geoagent_harness.planner.agent import PlannerAgentError, _schema_findings
from geoagent_harness.planner.decoder_schema import decoder_schema


def test_schema_is_sent_to_provider_and_old_json_mode_remains_supported():
    seen=[]
    def reply(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"message":"Which column?","plan":null}'},'finish_reason':'stop'}]})
    settings=ModelSettings(base_url='http://fixture/v1',model='fixture',timeout_seconds=10,max_tokens=1000)
    request=ModelRequest(messages=[ChatMessage(role='user',content='Return JSON')],json_mode=True,response_schema=Reply.model_json_schema())
    transport=httpx.MockTransport(reply)
    result=SharedModelClient(settings,transport=transport).complete(request)
    assert seen[0]['response_format']['type']=='json_schema'
    assert seen[0]['response_format']['json_schema']['schema']==Reply.model_json_schema()
    assert result.response_format=='json_schema'
    result=SharedModelClient(replace(settings,response_format='json_object'),transport=transport).complete(request)
    assert seen[-1]['response_format']=={'type':'json_object'} and result.response_format=='json_object'
    assert len(seen)==2


@pytest.mark.parametrize('detail',['response_format unsupported','Failed to initialize samplers: failed to parse grammar'])
def test_schema_rejection_does_not_silently_retry_or_downgrade(detail):
    seen=[]
    def reject(request):
        seen.append(request)
        return httpx.Response(400,json={'error':detail})
    settings=ModelSettings(base_url='http://fixture/v1',model='fixture',timeout_seconds=10,max_tokens=1000)
    client=SharedModelClient(settings,transport=httpx.MockTransport(reject))
    with pytest.raises(ModelClientError) as caught:
        client.complete(ModelRequest(messages=[ChatMessage(role='user',content='Return JSON')],response_schema=Reply.model_json_schema()))
    assert len(seen)==1 and caught.value.code=='model_response_format_rejected'


def test_response_format_setting_is_explicit_and_validated():
    assert load_model_settings({'MODEL_NAME':'fixture'}).response_format=='json_schema'
    assert load_model_settings({'MODEL_NAME':'fixture','MODEL_RESPONSE_FORMAT':'json_object'}).response_format=='json_object'
    with pytest.raises(ModelSettingsError):load_model_settings({'MODEL_NAME':'fixture','MODEL_RESPONSE_FORMAT':'guess'})


def test_conversation_passes_the_actual_allowlisted_reply_schema_to_both_attempts(project):
    client=Client({'message':'bad','plan':'not an object'},ready())
    result=turn(project,client,PROMPT)
    for request in client.requests:
        baseline=decoder_schema(json.loads(request.messages[0].content)['required_json_schema'])
        proposal,exchange=request.response_schema['anyOf']
        assert proposal['properties']['plan']=={'$ref':'#/$defs/WorkflowPlan'}
        assert exchange['properties']['plan']=={'type':'null'}
        assert exchange['properties']['workflow_action']==baseline['properties']['workflow_action']
        assert not {'workflow_action','recipe_uses','recipe_discovery'} & set(proposal['properties'])
        assert proposal['additionalProperties'] is False
        branches=request.response_schema['$defs']['PlanStep']['anyOf']
        known=set()
        for branch in branches:
            skill=branch['properties']['skill']
            known.update(skill.get('enum', [skill.get('const')]))
        assert known==set(result['supported_skill_ids'])
        assert {'inspect_csv','calculate_csv_columns','export_csv'}.issubset({b['properties']['skill'].get('const') for b in branches})
    assert result['context_usage']['model_request']['response_schema_bytes']>0
    assert result['context_usage']['effort_budget']['model_calls']==2


def test_calculation_decoder_namespaces_recursive_arguments_and_excludes_dual_sources(project):
    client=Client(ready())
    turn(project,client,PROMPT)
    schema=client.requests[0].response_schema
    branches=schema['$defs']['PlanStep']['anyOf']
    calculation=next(b for b in branches if b['properties']['skill'].get('const')=='calculate_csv_columns')
    arguments=calculation['properties']['arguments']['anyOf']
    assert len(arguments)==2 and 'arguments' in calculation['required']
    for args in arguments:
        assert args['additionalProperties'] is False
        assert ('path' in args['properties']) != ('source_step' in args['properties'])
        assert ('path' in args['required']) != ('source_step' in args['required'])
        assert 'missing_policy' in args['required'] and 'calculations' in args['required']
        assert 'target_path' not in args['required']
        assert 'allOf' not in args
    derived=schema['$defs']['operation_calculate_csv_columns_DerivedColumn']
    assert derived['properties']['expression']['$ref']=='#/$defs/operation_calculate_csv_columns_Expression'
    expression=schema['$defs']['operation_calculate_csv_columns_Expression']
    assert len(expression['oneOf'])==5
    export=next(b for b in branches if b['properties']['skill'].get('const')=='export_csv')
    assert all(('path' in a['properties']) != ('source_step' in a['properties']) for a in export['properties']['arguments']['anyOf'])
    steps=schema['$defs']['WorkflowPlan']['properties']['steps']
    assert steps['minItems']==steps['maxItems']==2
    assert [step['properties']['skill']['const'] for step in steps['prefixItems']]==['inspect_csv','calculate_csv_columns']


@pytest.mark.parametrize('raw',['{"plan":', '```json\n{}\n```', '<think>private reasoning</think>{}', '{"plan":NaN}', '{"message":"Ready","plan":[]}'])
def test_malformed_or_wrong_type_responses_never_become_canned_plans(project,raw):
    class Raw(Client):
        def complete(self,request):
            self.requests.append(request.model_copy(deep=True))
            return ModelResult(model='fixture',content=raw,finish_reason='stop',response_format='json_schema')
    client=Raw()
    with pytest.raises(PlannerAgentError) as caught:turn(project,client,PROMPT)
    assert len(client.requests)==2 and read(project)['revision']==0
    diagnostic=caught.value.planner_diagnostics
    assert diagnostic['response_bytes']==len(raw.encode())
    assert diagnostic['finish_reason']=='stop' and diagnostic['response_format']=='json_schema'
    assert 'private reasoning' not in json.dumps(diagnostic)


def test_invalid_json_is_described_as_response_syntax_not_plan_field_type():
    with pytest.raises(ValidationError) as caught:Reply.model_validate_json('{"plan":')
    findings=_schema_findings(caught.value)
    assert findings[0].startswith('response:') and 'complete valid JSON object' in findings[0]
    with pytest.raises(ValidationError) as caught:Reply.model_validate_json('{"message":"Ready","plan":"{}"}')
    findings=_schema_findings(caught.value)
    assert findings[0].startswith('plan:') and 'never a quoted JSON string' in findings[0]


def test_truncated_discovery_is_not_dispatched_and_gets_one_correction(project):
    class Truncated(Client):
        def complete(self,request):
            if not self.requests:
                self.requests.append(request.model_copy(deep=True))
                return ModelResult(model='fixture',content=json.dumps({'message':'search','recipe_discovery':{'action':'search','query':'csv'}}),finish_reason='length',completion_tokens=1024)
            return super().complete(request)
    client=Truncated(ready())
    result=turn(project,client,PROMPT)
    assert result['context_usage']['effort_budget']['model_calls']==2
    assert result['context_usage']['effort_budget']['tool_calls']==0
    assert json.loads(client.requests[1].messages[-1].content)['failure_kind']=='output_truncated'


def test_repeated_truncation_preserves_existing_plan_even_if_json_is_valid(project):
    first=turn(project,Client(ready()),PROMPT)
    class Truncated(Client):
        def complete(self,request):
            self.requests.append(request.model_copy(deep=True))
            return ModelResult(model='fixture',content=json.dumps(ready()),finish_reason='length',completion_tokens=1024)
    client=Truncated()
    with pytest.raises(PlannerAgentError) as caught:turn(project,client,PROMPT,revision=1)
    assert caught.value.reason=='output_truncated'
    assert caught.value.planner_diagnostics['finish_reason']=='length'
    assert caught.value.planner_diagnostics['completion_tokens']==1024
    assert read(project)['planner_result']==first['planner_result']
    assert len(client.requests)==2


def test_decoder_preserves_structure_and_property_names_but_runtime_keeps_bounds():
    original={'type':'object','properties':{'title':{'type':'string','minLength':2},'pattern':{'type':'string','pattern':'^[a-z]+$'}},'required':['title'],'additionalProperties':False}
    converted=decoder_schema(original)
    assert converted=={'type':'object','properties':{'title':{'type':'string'},'pattern':{'type':'string'}},'required':['title'],'additionalProperties':False}
    assert original['properties']['title']['minLength']==2
    assert 'pattern' in original['properties']['pattern']
    source=Reply.model_json_schema()
    assert source['$defs']['PlanStep']['properties']['step_id']['pattern']
    assert 'pattern' not in decoder_schema(source)['$defs']['PlanStep']['properties']['step_id']
    with pytest.raises(ValidationError):Reply.model_validate({'message':'Ready','plan':{'summary':'Invalid identifier','steps':[{'step_id':'wrong','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'sample_orders.csv'}}]}})


@pytest.mark.parametrize(('reason','code'),[('output_truncated','planner_output_truncated'),(None,'planner_invalid_json')])
def test_http_json_and_length_failures_report_specific_safe_diagnostics(project,monkeypatch,reason,code):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from geoagent_harness.interface_api.server import _handler
    import geoagent_harness.interface_api.conversation as service
    original=service.conversation_turn
    class Broken(Client):
        def complete(self,request):
            self.requests.append(request.model_copy(deep=True))
            return ModelResult(model='fixture',content='{"message":"Ready","plan":',finish_reason='length' if reason else 'stop',completion_tokens=1024,response_format='json_schema')
    client=Broken()
    monkeypatch.setattr(service,'conversation_turn',lambda request,*,project_root:original(request,project_root=project_root,model_client=client))
    server=ThreadingHTTPServer(('127.0.0.1',0),_handler(project));thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        connection=HTTPConnection(*server.server_address)
        connection.request('POST','/api/v1/planner/conversation',json.dumps({'action':'turn','conversation_id':'b'*32,'message':PROMPT}),{'Content-Type':'application/json','Origin':'http://localhost:5173'})
        response=connection.getresponse();body=json.loads(response.read());connection.close()
        assert response.status==422 and body['code']==code
        assert body['planner_diagnostics']['response_format']=='json_schema'
        assert body['planner_diagnostics']['response_shape']=='invalid_json'
        assert len(client.requests)==2
        assert not body['execution_performed'] and not body['plan_saved']
        if reason:assert 'MODEL_MAX_TOKENS' in body['retry_guidance']
        else:assert body['schema_findings'][0].startswith('response:')
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)


def test_registry_binds_required_gates_without_granting_authority(project):
    proposed=ready()
    step=proposed['plan']['steps'][0]
    step['requires_approval']=False;step['validation_required']=False
    result=turn(project,Client(proposed),PROMPT)
    canonical=result['planner_result']['plan']['steps'][0]
    assert canonical['requires_approval'] and canonical['validation_required']
    assert result['context_usage']['required_gate_bindings']==['step_1']
    assert not result['approval_performed'] and not result['execution_performed']
    assert not (project/'approvals').exists() and not (project/'data/output').exists()


def test_compact_calculation_contract_keeps_all_expression_variants_and_limits():
    from geoagent_harness.planner.prompt_scope import compact_calculation_schema
    from geoagent_harness.tabular.schemas import CalculateColumns
    source=CalculateColumns.model_json_schema();compact=compact_calculation_schema(source)
    assert len(json.dumps(compact))<len(json.dumps(source))*0.6
    assert compact['$defs']['DerivedColumn']['properties']['expression']=={'$ref':'#/$defs/Expression'}
    assert {ref['$ref'] for ref in compact['$defs']['Expression']['oneOf']}=={'#/$defs/Column','#/$defs/Number','#/$defs/Binary','#/$defs/Compare','#/$defs/Conditional'}
    assert compact['properties']['calculations']['maxItems']==5
    assert compact['allOf']==source['allOf']
    assert compact['$defs']['Binary']['properties']['left']=={'$ref':'#/$defs/Expression'}


def test_reuse_constraints_are_root_only_and_do_not_mutate_the_base():
    from geoagent_harness.planner.reuse_claims import constrain_reuse_claims
    base={'type':'object','additionalProperties':False,'properties':{
        'reused_recipe_ids':{'type':'array','items':{'type':'string'}},
        'arguments':{'type':'object','properties':{'reused_recipe_ids':{'type':'string'}}},
    }}
    empty=constrain_reuse_claims(base,[])
    assert 'reused_recipe_ids' not in empty['properties']
    assert empty['properties']['arguments']==base['properties']['arguments']
    assert 'reused_recipe_ids' in base['properties']
    constrained=constrain_reuse_claims({'anyOf':[base,base]},['recipe_inspect_csv'])
    assert all(branch['properties']['reused_recipe_ids']['items']['enum']==['recipe_inspect_csv'] for branch in constrained['anyOf'])
