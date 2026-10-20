"""Verified result reads share exact durable run scope and safe CSV bounds."""
import hashlib
import json
from pathlib import Path
import pytest
from typer.testing import CliRunner
from tests.test_tabular_workflow import project
from geoagent_harness.interface_api.workflow_runs import RunRequest,run_action,_directory,_write
from geoagent_harness.interface_api.server import InterfaceApiError
from geoagent_harness.cli import app


def recorded(project,content=b'id,value\n001,10\n002,20\n'):
    path=project/'data/output/result.csv';path.write_bytes(content)
    identity='a'*32;sha='b'*64;chat='c'*32
    record={'run_id':identity,'plan_sha256':sha,'conversation_id':chat,'status':'completed',
        'steps':[{'step_id':'step_1','skill_id':'calculate_csv_columns','status':'validated_success',
          'outcome':{'output':{'path':'data/output/result.csv','sha256':hashlib.sha256(content).hexdigest()}}}]}
    _write(_directory(project),record)
    request=RunRequest(action='preview',run_id=identity,confirmed_plan_sha256=sha,conversation_id=chat,step_id='step_1')
    return path,record,request


def test_verified_csv_read_and_cli_share_service_without_execution(project,tmp_path):
    path,record,request=recorded(project)
    result=run_action(request,project_root=project)
    assert result['verified_at_read'] and not result['execution_performed'] and not result['approval_performed']
    assert result['preview']==[{'id':'001','value':'10'},{'id':'002','value':'20'}]
    request_path=tmp_path/'preview.json';request_path.write_text(request.model_dump_json())
    cli=CliRunner().invoke(app,['workflow-runs','--project-root',str(project),'--request-file',str(request_path)])
    assert cli.exit_code==0,cli.output
    assert json.loads(cli.stdout)==result
    assert path.read_bytes()==b'id,value\n001,10\n002,20\n'
    assert not (project/'approvals').exists()


@pytest.mark.parametrize('change',[{'confirmed_plan_sha256':'d'*64},{'conversation_id':'d'*32},{'step_id':'step_2'}])
def test_preview_scope_cannot_be_substituted(project,change):
    _,_,request=recorded(project)
    with pytest.raises(InterfaceApiError,match='match|completed'):
        run_action(request.model_copy(update=change),project_root=project)


def test_changed_missing_or_linked_artifact_cannot_replace_recorded_result(project,tmp_path):
    path,_,request=recorded(project)
    path.write_text('id,value\n001,999\n')
    with pytest.raises(InterfaceApiError,match='changed since execution'):run_action(request,project_root=project)
    path.unlink()
    with pytest.raises(InterfaceApiError,match='unavailable'):run_action(request,project_root=project)
    outside=tmp_path/'elsewhere.csv';outside.write_text('id,value\n001,10\n002,20\n');path.symlink_to(outside)
    with pytest.raises(InterfaceApiError,match='unsafe'):run_action(request,project_root=project)


def test_completed_input_csv_can_be_previewed_but_queued_steps_cannot(project):
    _,record,request=recorded(project)
    step=record['steps'][0];source=project/'data/input/sample_orders.csv'
    step.update(skill_id='inspect_csv',status='completed',outcome={'source':'data/input/sample_orders.csv','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    _write(_directory(project),record)
    assert run_action(request,project_root=project)['row_count']==6
    step['status']='queued';_write(_directory(project),record)
    with pytest.raises(InterfaceApiError,match='completed'):run_action(request,project_root=project)


def test_preview_row_cell_and_byte_limits_are_explicit(project):
    content=('id,text\n'+''.join(f'{i},'+('x'*500)+'\n' for i in range(1500))).encode()
    _,_,request=recorded(project,content)
    result=run_action(request,project_root=project)
    assert result['row_count']==1500 and 0<len(result['preview'])<1000
    assert result['preview_truncated'] and result['cells_truncated']
    assert len(result['preview'][0]['text'])==160
    assert len(json.dumps(result['preview'],ensure_ascii=False).encode())<=128000


def test_arbitrary_client_paths_are_not_accepted(project):
    _,_,request=recorded(project)
    with pytest.raises(ValueError):RunRequest.model_validate({**request.model_dump(),'path':'/etc/passwd'})


@pytest.mark.parametrize('filename',['tabbed.csv','tabbed.TSV'])
def test_preview_preserves_recorded_delimiter_instead_of_guessing_from_extension(project,filename):
    _,record,request=recorded(project)
    content=b'id\tvalue\n001\t10\n'
    path=project/'data/input'/filename;path.write_bytes(content)
    record['steps'][0].update(skill_id='inspect_csv',status='completed',arguments={'delimiter':'\t'},
        outcome={'source':f'data/input/{filename}','source_sha256':hashlib.sha256(content).hexdigest()})
    _write(_directory(project),record)
    result=run_action(request,project_root=project)
    assert result['columns']==['id','value'] and result['preview']==[{'id':'001','value':'10'}]


def test_malformed_artifact_metadata_is_rejected(project):
    _,record,request=recorded(project)
    record['steps'][0]['outcome']['output']='not an artifact'
    _write(_directory(project),record)
    with pytest.raises(InterfaceApiError,match='valid artifact identity'):
        run_action(request,project_root=project)


def test_preview_io_does_not_hold_execution_progress_lock(project,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from geoagent_harness.interface_api import result_preview,workflow_runs
    _,_,request=recorded(project)
    original=result_preview.read_bytes
    def probe():
        acquired=workflow_runs._LOCK.acquire(blocking=False)
        if acquired:workflow_runs._LOCK.release()
        return acquired
    def checked_read(*args,**kwargs):
        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(probe).result(timeout=2),'Preview I/O must not block run progress/cancellation'
        return original(*args,**kwargs)
    monkeypatch.setattr(result_preview,'read_bytes',checked_read)
    assert run_action(request,project_root=project)['verified_at_read']


@pytest.mark.parametrize('aggregation,expected',[('count',[2,1]),('sum',[30,5]),('mean',[15,5]),('min',[10,5]),('max',[20,5])])
def test_chart_summary_uses_complete_verified_artifact(project,aggregation,expected):
    from geoagent_harness.interface_api.workflow_runs import ChartAnalysis
    path,_,request=recorded(project,b'region,value\nNorth,10\nNorth,20\nSouth,5\n')
    request.analysis=ChartAnalysis(group_by='region',value='value',aggregation=aggregation)
    result=run_action(request,project_root=project)
    chart=result['chart_analysis']
    assert [row['value'] for row in chart['preview']]==expected
    assert chart['source_row_count']==3 and chart['scope']=='complete_verified_artifact'
    assert not result['execution_performed'] and not result['approval_performed']
    path.write_text('region,value\nNorth,999\n')
    with pytest.raises(InterfaceApiError,match='changed since execution'):run_action(request,project_root=project)


def test_chart_summary_keeps_null_groups_and_null_numeric_values(project):
    from geoagent_harness.interface_api.workflow_runs import ChartAnalysis
    _,_,request=recorded(project,b'region,value\nNorth,\n,5\n')
    request.analysis=ChartAnalysis(group_by='region',value='value',aggregation='sum')
    result=run_action(request,project_root=project)['chart_analysis']
    assert {'category':'North','value':None} in result['preview']
    assert {'category':None,'value':5} in result['preview']


@pytest.mark.parametrize('content,group,value,match',[
 (b'region,value\nNorth,bad\n','region','value','non-numeric'),
 (b'region,value\nNorth,10\n','missing','value','existing'),
 (('region,value\n'+''.join(f'{i},1\n' for i in range(101))).encode(),'region','value','100 categories'),
 (b'region,value\nNorth,1e30\n','region','value','numeric'),
])
def test_chart_summary_refuses_unsupported_inputs(project,content,group,value,match):
    from geoagent_harness.interface_api.workflow_runs import ChartAnalysis
    _,_,request=recorded(project,content)
    request.analysis=ChartAnalysis(group_by=group,value=value,aggregation='sum')
    with pytest.raises(InterfaceApiError,match=match):run_action(request,project_root=project)
