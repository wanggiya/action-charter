"""Actual temporary writes, authority revocation and cross-process policy behavior."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from tests.test_tabular_workflow import project, pipeline, saved, run
from geoagent_harness.interface_api.workflow import WorkflowRequest, prepare_workflow, authorize_workflow, execute_workflow
from geoagent_harness.mcp_server.settings import load_settings
from geoagent_harness.tabular.service import run_operation, inspect_csv
from geoagent_harness import write_policy as policy


def change(root, enabled):
    state=policy.snapshot(root)
    return policy.update(root,policy.PolicyUpdate(enabled=enabled,session_id=state['session_id'],revision=state['revision']))


def authorized(root, proposal=None):
    request=saved(root,proposal or pipeline())
    review=prepare_workflow(request,project_root=root)
    receipt=authorize_workflow(WorkflowRequest(**{**request.model_dump(),'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,'approver':'fixture','reason':'Temporary fixture writes only'}),project_root=root)
    return WorkflowRequest(**{**request.model_dump(),'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True,'plan_approval_filename':receipt['plan_approval_filename'],'recipe_approval_filename':receipt['recipe_approval_filename']})


def test_off_inspection_on_exact_workflow_and_direct_bypass(project):
    with policy.session(project):
        assert inspect_csv('sample_orders.csv',load_settings())['row_count']==6
        with pytest.raises((policy.WritePolicyError,RuntimeError),match='OFF'):authorized(project)
        change(project,True)
        # Cached settings=True cannot grant direct execution authority, even while ON.
        with pytest.raises(policy.WritePolicyError,match='entry point'):
            run_operation('select_csv_columns',{'path':'sample_orders.csv','columns':['amount'],'target_path':'data/output/bypass.csv'},load_settings())
        assert not list((project/'data/output').iterdir())
        result=execute_workflow(authorized(project),project_root=project)
        assert result['status']=='validated_success'
        assert (project/'data/output/final.csv').is_file()


def test_policy_revision_restart_and_legacy_authority(project):
    with policy.session(project,enabled=True):
        request=authorized(project)
        before=policy.snapshot(project)
        assert change(project,True)['revision']==before['revision'] # Idempotent ON is not a revocation.
        change(project,False);change(project,True)
        with pytest.raises((policy.WritePolicyError,RuntimeError),match='review|authorization|Confirm'):
            execute_workflow(request,project_root=project)
        previous=policy.snapshot(project)
    with policy.session(project,enabled=True):
        assert policy.snapshot(project)['session_id']!=previous['session_id']
        review=prepare_workflow(request,project_root=project)
        refreshed=request.model_copy(update={'confirmed_review_sha256':review['review_sha256']})
        with pytest.raises(policy.WritePolicyError,match='stale'):
            execute_workflow(refreshed,project_root=project)
    assert not list((project/'data/output').iterdir())


def test_disable_during_validation_keeps_output_and_stops_later_write(project,monkeypatch):
    from geoagent_harness.recipes import runner
    original=runner.validate_tabular_output
    with policy.session(project,enabled=True):
        request=authorized(project)
        def verify(result,settings):
            checked=original(result,settings)
            change(project,False)
            return checked
        monkeypatch.setattr(runner,'validate_tabular_output',verify)
        with pytest.raises(RuntimeError) as failed:
            execute_workflow(request,project_root=project)
        from geoagent_harness.interface_api.workflow import execution_failure_payload
        finding=execution_failure_payload(failed.value)
        assert finding['failure_code']=='write_policy_blocked'
        assert finding['failed_step_id']=='step_3'
        assert 'Write operations are OFF' in finding['error']
        assert sorted(p.name for p in (project/'data/output').iterdir())==['selected.csv']
        # Output verification ran before OFF stopped the next operation.
        assert (project/'data/output/selected.csv').read_text().startswith('order_id,region,amount')


def test_cas_lock_cross_process_and_cached_settings(project):
    with policy.session(project,locked=True):
        with pytest.raises(policy.WritePolicyError,match='administratively'):change(project,True)
    with policy.session(project):
        state=policy.snapshot(project)
        command=[sys.executable,'-c',"from geoagent_harness.write_policy import snapshot; import json,sys; print(json.dumps(snapshot(sys.argv[1])))",str(project)]
        result=subprocess.run(command,capture_output=True,text=True,check=True,env={**os.environ,'PYTHONPATH':str(Path(__file__).parents[1]/'src')})
        assert json.loads(result.stdout)['session_id']==state['session_id']
        request=policy.PolicyUpdate(enabled=True,session_id=state['session_id'],revision=state['revision'])
        with ThreadPoolExecutor(2) as pool:
            futures=[pool.submit(policy.update,project,request) for _ in range(2)]
        assert sum(f.exception() is None for f in futures)==1
        assert isinstance(next(f.exception() for f in futures if f.exception()),policy.WritePolicyError)
        with pytest.raises(policy.WritePolicyError,match='Another API'):
            with policy.session(project):pass


def test_policy_symlinks_fail_closed(project,tmp_path):
    (project/'workflow-state').symlink_to(tmp_path/'elsewhere')
    with pytest.raises(policy.WritePolicyError,match='symlink'):
        with policy.session(project):pass


def test_cli_controls_same_session_and_legacy_decision_cannot_enter(project):
    from typer.testing import CliRunner
    from geoagent_harness.cli import app
    # Existing pre-session approvals stay readable but do not confer session authority.
    request=authorized(project)
    with policy.session(project):
        cli=CliRunner()
        result=cli.invoke(app,['write-policy','--project-root',str(project),'--enabled'])
        assert result.exit_code==0,result.output
        state=json.loads(result.output)
        assert state['enabled'] is True
        review=prepare_workflow(request,project_root=project)
        with pytest.raises(policy.WritePolicyError,match='missing or stale'):
            execute_workflow(request.model_copy(update={'confirmed_review_sha256':review['review_sha256']}),project_root=project)
        assert cli.invoke(app,['write-policy','--project-root',str(project),'--disabled']).exit_code==0
        assert not policy.snapshot(project)['enabled']
    assert not list((project/'data/output').iterdir())


@pytest.mark.parametrize('module,function',[
    ('skills.convert_vector.service','convert_vector'),
    ('skills.load_vector_to_postgis.service','load_vector_to_postgis'),
    ('skill_adapters.raster_conversion','convert_raster'),
    ('geoserver_publication.service','execute_geoserver_publication'),
    ('postgis_promotion_execution.service','execute_postgis_promotion'),
    ('postgis_rollback_execution.service','execute_postgis_rollback'),
])
def test_managed_direct_mutators_reject_without_session_authority(project,module,function):
    import importlib
    import inspect
    operation=getattr(importlib.import_module('geoagent_harness.'+module),function)
    arguments={name:None for name,parameter in inspect.signature(operation).parameters.items() if parameter.default is inspect.Parameter.empty}
    arguments['settings']=load_settings()
    with policy.session(project,enabled=True):
        with pytest.raises(policy.WritePolicyError,match='entry point'):
            operation(**arguments)
    assert not list((project/'data/output').iterdir())


def test_another_process_cannot_bypass_off_with_startup_flag(project):
    code="""from geoagent_harness.mcp_server.settings import load_settings
from geoagent_harness.tabular.service import run_operation
run_operation('select_csv_columns',{'path':'sample_orders.csv','columns':['amount'],'target_path':'data/output/bypass.csv'},load_settings())
"""
    with policy.session(project):
        result=subprocess.run([sys.executable,'-c',code],cwd=project,capture_output=True,text=True,
            env={**os.environ,'ENABLE_WRITE_TOOLS':'true','PYTHONPATH':str(Path(__file__).parents[1]/'src')})
        assert result.returncode!=0 and 'Write operations are OFF' in result.stderr
    assert not list((project/'data/output').iterdir())


def test_nested_export_path_cannot_bypass_project_policy(project):
    from geoagent_harness.snakemake_export.generator import generate_snakemake_recipe_export
    with policy.session(project,enabled=True):
        with pytest.raises(policy.WritePolicyError,match='entry point'):
            generate_snakemake_recipe_export(None,export_root=project/'nested'/'exports')
    assert not (project/'nested').exists()


def test_external_approval_storage_cannot_bind_registry_project_session(project,tmp_path):
    from geoagent_harness.approvals.service import create_approval
    with policy.session(project,enabled=True):
        record,_=create_approval(planner_result=pipeline(),step_ids=['step_2'],decision='approved',
            approver='fixture',reason='Only isolated storage',approval_root=tmp_path/'other-project'/'approvals',project_root=project)
        with pytest.raises(policy.WritePolicyError,match='missing or stale'):
            policy.check(project,record)
