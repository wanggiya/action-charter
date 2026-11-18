"""Reported communication tokens stay bounded, partial, read-only and content-free."""
import json

import pytest

from geoagent_harness.platform.model_gateway import telemetry as d

ID='a'*32
PARENT='b'*32
RUN='c'*32
SUBMISSION='d'*32


def parent(**changes):
    return {'id':PARENT,'kind':'turn','conversation_id':ID,'status':'completed',
        'started_at':'2026-11-16T10:00:00+00:00','submission_id':SUBMISSION,
        'workflow_run_id':RUN,'workflow_status':'completed','observed_model_calls':2,
        'resources':{'elapsed_seconds':100},**changes}


def call(identity='e'*32,**changes):
    return {'id':identity,'kind':'call','parent_id':PARENT,'conversation_id':ID,
        'status':'completed','started_at':'2026-11-16T10:00:01+00:00','error_code':None,
        'role':'planner','phase':'planner_generation','provider_profile_id':'local',
        'model':'fixture','prompt_tokens':11,'completion_tokens':7,
        'network_dispatch':'attempted','resources':{'elapsed_seconds':1},**changes}


def summary(records,**kwargs):return d.reported_model_usage(records,**kwargs)['scopes'][0]


def test_scopes_roles_and_model_time_never_add_parent_intervals_or_duplicate_calls():
    first=call();second=call('f'*32,role='critic',model='fixture-other',provider_profile_id='gateway',
        prompt_tokens=13,completion_tokens=5,resources={'elapsed_seconds':2},phase='planner_correction')
    value=d.reported_model_usage([parent(),first,second,first])
    scopes=value['scopes'];assert [s['kind'] for s in scopes]==['chat','submission','workflow']
    for s in scopes:
        assert (s['reported_input_tokens'],s['reported_output_tokens'])==(24,12)
        assert s['recorded_calls']==2 and s['model_call_seconds']==3
        assert s['end_to_end_output_tokens_per_second']==4
        assert s['calls_with_both_counts']==2 and s['coverage']=='reported_for_visible_calls'
        assert s['correction_calls']==1 and len(s['by_role_model'])==2
    assert value['lifetime_usage'] is False
    assert 'total' not in json.dumps(value).lower()


def test_partial_counts_are_preserved_independently_with_unknown_denominator():
    value=summary([parent(),call(),call('f'*32,prompt_tokens=None,completion_tokens=17)])
    assert value['reported_input_tokens']==11 and value['reported_output_tokens']==24
    assert value['calls_with_reported_input']==1 and value['calls_with_reported_output']==2
    assert value['calls_with_both_counts']==1 and value['calls_with_unknown_usage']==1
    assert value['coverage']=='partial'


@pytest.mark.parametrize('invalid',[None,-1,True,1.5,2**40])
def test_invalid_or_missing_counts_never_become_zero(invalid):
    value=summary([call(prompt_tokens=invalid,completion_tokens=invalid,
        resources={'elapsed_seconds':float('nan')})])
    assert value['reported_input_tokens'] is None and value['reported_output_tokens'] is None
    assert value['model_call_seconds'] is None and value['end_to_end_output_tokens_per_second'] is None
    assert value['coverage']=='partial'
    json.dumps(value,allow_nan=False)


def test_known_zero_is_distinct_from_missing_and_zero_duration_never_divides():
    value=summary([call(prompt_tokens=0,completion_tokens=0,resources={'elapsed_seconds':0})])
    assert value['reported_input_tokens']==value['reported_output_tokens']==0
    assert value['model_call_seconds']==0 and value['end_to_end_output_tokens_per_second'] is None
    assert value['coverage']=='reported_for_visible_calls'


def test_pre_send_refusal_is_separate_from_timed_out_unknown_consumption():
    blocked=call(status='failed',network_dispatch='not_attempted',error_code='model_data_class_blocked',prompt_tokens=None,completion_tokens=None)
    alone=summary([blocked]);assert alone['coverage']=='not_sent'
    assert alone['not_sent_calls']==1 and alone['calls_with_unknown_usage']==0
    assert alone['reported_input_tokens'] is None
    timed=call('f'*32,status='failed',error_code='model_timeout',prompt_tokens=None,completion_tokens=None)
    both=summary([blocked,timed])
    assert both['recorded_calls']==2 and both['not_sent_calls']==1
    assert both['timeout_calls']==1 and both['model_call_failures']==1
    assert both['calls_with_unknown_usage']==1 and both['coverage']=='partial'


def test_absent_call_records_and_storage_failure_remain_visible():
    value=summary([parent(observed_model_calls=3),call()])
    assert value['missing_call_records']==2 and value['calls_with_unknown_usage']==2
    assert value['collection_incomplete'] and value['coverage']=='partial'
    assert value['reported_input_tokens']==11
    lost=summary([parent(observed_model_calls=1,storage_available=False),call()])
    assert lost['calls_with_both_counts']==1 and lost['coverage']=='partial'


def test_empty_scopes_never_claim_zero_spend():
    value=summary([])
    assert value['coverage']=='no_recorded_calls'
    assert value['reported_input_tokens'] is None and value['reported_output_tokens'] is None


def test_unknown_content_is_not_copied_to_summary():
    value=d.reported_model_usage([call(messages='private-data',secret='private-credential',response='private-result')])
    text=json.dumps(value)
    assert all(s not in text for s in ('private-data','private-credential','private-result'))


def test_read_is_chat_bounded_and_never_writes_or_calls_model(tmp_path,monkeypatch):
    from geoagent_harness.platform.model_gateway.client import SharedModelClient
    monkeypatch.setattr(SharedModelClient,'complete',lambda *a,**k:pytest.fail('reading must not call model'))
    assert d.store(tmp_path,'turn',parent(observed_model_calls=1))
    assert d.store(tmp_path,'call',call())
    assert d.store(tmp_path,'call',call('f'*32,conversation_id='1'*32,prompt_tokens=999))
    before=d.read(tmp_path,ID)
    after=d.read(tmp_path,ID)
    assert before==after
    value=before['reported_model_usage'];assert value['retained_records']==2
    assert value['scopes'][0]['reported_input_tokens']==11 and not value['records_truncated']
    assert not before['execution_performed'] and not before['authority_granted']


def test_recent_record_limit_is_explicit_not_lifetime_usage(tmp_path):
    assert d.store(tmp_path,'turn',parent(observed_model_calls=105))
    for n in range(105):assert d.store(tmp_path,'call',call(f'{n:032x}'))
    value=d.read(tmp_path,ID)['reported_model_usage']
    assert value['records_truncated'] and value['returned_records']==100 and value['retained_records']==106
    assert value['scopes'][0]['recorded_calls']==100
    assert value['scopes'][0]['reported_input_tokens']==1100
    assert not value['lifetime_usage']


def test_cli_json_uses_same_summary(tmp_path):
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from typer.testing import CliRunner
    from geoagent_harness.apps.cli.main import app
    from geoagent_harness.apps.http.server import _handler
    assert d.store(tmp_path,'call',call(parent_id=None))
    server=ThreadingHTTPServer(('127.0.0.1',0),_handler(tmp_path))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        args=['chat','--api-url',f'http://127.0.0.1:{server.server_port}','diagnostics',ID]
        result=CliRunner().invoke(app,[*args,'--json'])
        assert result.exit_code==0,result.stdout
        assert json.loads(result.stdout)['reported_model_usage']==d.read(tmp_path,ID)['reported_model_usage']
        readable=CliRunner().invoke(app,args)
        assert readable.exit_code==0 and 'Reported model tokens' in readable.stdout
        assert 'Input / context: 11' in readable.stdout and 'Generated output: 7' in readable.stdout
        assert 'Total' not in readable.stdout
    finally:server.shutdown();server.server_close();thread.join(timeout=2)
