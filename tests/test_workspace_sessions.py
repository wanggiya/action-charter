"""Relocated local session ownership and task history; no live models/databases."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from tests.test_task_agents import project
from tests.test_workspace_layout import configure
from tests.test_workspace_authority import export_plan
from tests.test_reusable_recipes_and_runs import execution
from geoagent_harness import write_policy as policy
from geoagent_harness.interface_api import server as api
from geoagent_harness.interface_api.workflow import execute_workflow
from geoagent_harness.task_history.service import history_directory,load_task_events,TaskHistoryError
from geoagent_harness.workspace import CONFIG_NAME


def backup(source,destination):
    destination.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    with sqlite3.connect(source) as original,sqlite3.connect(destination) as copied:
        original.backup(copied)


def child(project,code):
    return subprocess.run([sys.executable,'-c',code,str(project)],capture_output=True,text=True,
        timeout=15,env={**os.environ,'PYTHONPATH':str(Path(__file__).parents[1]/'src')})


def test_relocated_session_executes_and_other_process_observes_same_policy(project,tmp_path_factory,monkeypatch):
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','true')
    state=tmp_path_factory.mktemp('session-state');configure(project,state)
    with policy.session(project,enabled=True) as owner:
        result=child(project,'from geoagent_harness.write_policy import snapshot; import json,sys; print(json.dumps(snapshot(sys.argv[1])))')
        assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)['session_id']==owner['session_id']
        request=execution(project,export_plan('session-output.csv'))
        assert execute_workflow(request,project_root=project)['status']=='validated_success'
        assert (state/'workflow-state/write-policy.sqlite3').is_file()
        assert (state/'workflow-state/write-policy.lock').is_file()
        assert not (project/'workflow-state').exists()
    assert policy.snapshot(project) is None


def test_live_configuration_change_blocks_reads_writes_and_second_process(project):
    with policy.session(project,enabled=True) as before:
        configure(project,'other-state')
        for read in (policy.snapshot,policy.ticket):
            with pytest.raises(policy.WritePolicyError,match='changed during an active'):
                read(project)
        code='from geoagent_harness.write_policy import session; import sys\nwith session(sys.argv[1],enabled=True): pass'
        denied=child(project,code)
        assert denied.returncode!=0 and 'Another API' in denied.stderr
        assert not (project/'other-state').exists()
        (project/CONFIG_NAME).unlink()
        assert policy.snapshot(project)['session_id']==before['session_id']


def test_missing_relocated_policy_never_silently_creates_empty_authority(project):
    with policy.session(project):pass
    old=project/'workflow-state/write-policy.sqlite3';before=old.read_bytes()
    configure(project,'state')
    with pytest.raises(policy.WritePolicyError,match='migration required'):policy.snapshot(project)
    with pytest.raises(policy.WritePolicyError,match='migration required'):
        with policy.session(project):pass
    assert old.read_bytes()==before and not (project/'state').exists()


def test_offline_policy_copy_preserves_history_but_new_session_revokes_old_approval(project,tmp_path_factory,monkeypatch):
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','true')
    from geoagent_harness.recipes.approval import load_recipe_approval
    with policy.session(project,enabled=True) as before:
        request=execution(project,export_plan('not-executed.csv'))
        approval=load_recipe_approval(project/'approvals'/request.recipe_approval_filename,approval_root=project/'approvals')
        policy.check(project,approval)
    source=project/'workflow-state/write-policy.sqlite3';old=source.read_bytes()
    state=tmp_path_factory.mktemp('copied-session')
    backup(source,state/'workflow-state/write-policy.sqlite3')
    for store in ('plans','approvals','workflow-recipes'):shutil.copytree(project/store,state/store)
    configure(project,state)
    with policy.session(project,enabled=True) as after:
        assert after['session_id']!=before['session_id']
        with pytest.raises(policy.WritePolicyError,match='stale'):policy.check(project,approval)
    assert source.read_bytes()==old and not (project/'data/output/not-executed.csv').exists()


def test_active_legacy_lease_blocks_relocated_start(project,tmp_path_factory):
    with policy.session(project):pass
    state=tmp_path_factory.mktemp('legacy-session-copy')
    backup(project/'workflow-state/write-policy.sqlite3',state/'workflow-state/write-policy.sqlite3')
    fd=os.open(project/'workflow-state/write-policy.lock',os.O_RDONLY)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        configure(project,state)
        with pytest.raises(policy.WritePolicyError,match='legacy project'):
            with policy.session(project):pass
    finally:os.close(fd)


def test_task_history_api_cli_and_offline_copy_keep_exact_event_chain(project,tmp_path_factory):
    from geoagent_harness.cli import app
    recorded=api.record_interface_task_event(api.InterfaceTaskEventRequest(action='record_task_event',
        event_type='request',summary='Inspect only'),project_root=project)
    identity=recorded['task_id']
    old_context=api.inspect_interface_task_context(project_root=project,task_id=identity)
    from geoagent_harness.context_retrieval import retrieve_task_context,save_reviewed_context,load_reviewed_context,ContextReviewError
    retrieved=retrieve_task_context(root=project/'task-history',query='Inspect',task_ids=[identity])
    review=save_reviewed_context(history_root=project/'task-history',review_root=project/'reviewed-contexts',
        query='Inspect',task_ids=[identity],confirmed_context_sha256=retrieved['context_sha256'],reviewer='fixture',reason='Read-only context')
    before={p.name:p.read_bytes() for p in (project/'task-history'/identity).glob('*.json')}
    state=tmp_path_factory.mktemp('history-copy');shutil.copytree(project/'task-history',state/'task-history')
    configure(project,state)
    assert api.inspect_interface_task_context(project_root=project,task_id=identity)==old_context
    restored=load_reviewed_context(review_root=project/'reviewed-contexts',filename=review['review_filename'],history_root=history_directory(project))
    assert restored['context_sha256']==retrieved['context_sha256']
    cli=CliRunner()
    read=cli.invoke(app,['build-task-context',identity,'--project-root',str(project)])
    assert read.exit_code==0,read.output
    assert json.loads(read.output)==old_context
    saved=cli.invoke(app,['record-task-event',identity,'--event-type','clarification','--summary','No writes','--project-root',str(project)])
    assert saved.exit_code==0,saved.output
    assert len(load_task_events(root=history_directory(project),task_id=identity))==2
    with pytest.raises(ContextReviewError):
        load_reviewed_context(review_root=project/'reviewed-contexts',filename=review['review_filename'],history_root=history_directory(project))
    assert all((project/'task-history'/identity/name).read_bytes()==raw and (state/'task-history'/identity/name).read_bytes()==raw for name,raw in before.items())
    assert len(list((project/'task-history'/identity).glob('*.json')))==1


def test_missing_history_and_policy_reads_are_side_effect_free(tmp_path):
    configure(tmp_path,'state')
    assert policy.snapshot(tmp_path) is None
    assert load_task_events(root=history_directory(tmp_path),task_id='task-missing')==[]
    assert not (tmp_path/'state').exists()


def test_missing_relocated_history_rejects_without_writing(project):
    old=project/'task-history/task-old';old.mkdir(parents=True);(old/'record.json').write_text('{}')
    configure(project,'state')
    with pytest.raises(TaskHistoryError,match='migration required'):history_directory(project)
    assert not (project/'state').exists()


def test_unsafe_owner_directory_rejects_without_creating_policy(tmp_path,monkeypatch):
    real=tmp_path/'real';real.mkdir(mode=0o700)
    link=tmp_path/'link';link.symlink_to(real,target_is_directory=True)
    monkeypatch.setattr(policy,'_owner_directory',lambda:link)
    with pytest.raises(policy.WritePolicyError,match='ownership directory is unsafe'):
        with policy.session(tmp_path):pass
    assert not (tmp_path/'workflow-state').exists()


def test_crashed_owner_releases_lease_and_restart_is_new_read_only_session(project):
    code='from geoagent_harness.write_policy import session; import os,sys\nwith session(sys.argv[1],enabled=True) as state:\n print(state["session_id"],flush=True)\n os._exit(0)'
    crashed=child(project,code)
    assert crashed.returncode==0,crashed.stderr
    assert policy.snapshot(project) is None
    with policy.session(project) as restarted:
        assert restarted['session_id']!=crashed.stdout.strip()
        assert restarted['enabled'] is False
    assert not list((project/'data/output').iterdir())
