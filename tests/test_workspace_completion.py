"""Offline P0-2 exit and rollback on disposable projects, never live user state."""
import json
from pathlib import Path
import sqlite3

import pytest
from typer.testing import CliRunner

from geoagent_harness.apps.cli.main import app
from geoagent_harness.platform.workspace import CONFIG_NAME, RUNTIME_STORES, WorkspaceError, WorkspaceLayout
from geoagent_harness.platform.workspace_migration import migrate, verify, rollback, inventory
from tests.test_task_agents import project
from tests.test_workspace_layout import _inspect, configure


def test_verified_offline_migration_reopens_chat_run_and_leaves_source_only(project, tmp_path_factory):
    from geoagent_harness.task_actions.conversation import conversation_turn, TurnRequest
    from geoagent_harness.task_actions.workflow_runs import run_action, RunRequest
    original = _inspect(project)
    run = original['run']
    # Include a historical Builder package and explicit logical evidence link.
    (project / 'builder-reviews').mkdir()
    review = project / 'builder-reviews/review.json'
    review.write_text(json.dumps({'plan': 'plans/' + run['plan_filename']}))
    before = inventory(project)
    destination = tmp_path_factory.mktemp('offline-parent') / 'workspace'
    preview = migrate(project, destination)
    assert preview['inventory'] == before and not destination.exists()
    assert not (project / CONFIG_NAME).exists()
    result = migrate(project, destination, apply=True, offline=True, archive_legacy=True)
    assert result['status'] == 'verified' and result['source_only'] and result['exact_copy']
    assert not any((project / store).exists() for store in RUNTIME_STORES)
    assert (destination / 'builder-reviews/review.json').read_bytes() == (destination / '.legacy-source/builder-reviews/review.json').read_bytes()
    restored = conversation_turn(TurnRequest(action='read', conversation_id='c'*32), project_root=project)
    assert restored['planner_result']['plan_sha256'] == run['plan_sha256']
    assert run_action(RunRequest(action='read', run_id=run['run_id']), project_root=project)['status'] == 'completed'
    assert not (destination / 'data').exists()
    assert not any((project / store).exists() for store in RUNTIME_STORES)


def test_no_change_rollback_restores_original_records_and_keeps_destination(tmp_path):
    project = tmp_path / 'project'; project.mkdir()
    (project / 'plans').mkdir(); (project / 'plans/a.json').write_text('{"immutable":true}')
    original = inventory(project)
    destination = tmp_path / 'state'
    migrate(project, destination, apply=True, offline=True, archive_legacy=True)
    result = rollback(project, offline=True)
    assert result['status'] == 'rolled_back' and result['destination_preserved']
    assert inventory(project) == original and not (project / CONFIG_NAME).exists()
    assert (destination / 'plans/a.json').read_text() == '{"immutable":true}'


def test_later_writes_make_rollback_refuse_to_lose_new_state(tmp_path):
    project = tmp_path / 'project'; project.mkdir()
    (project / 'plans').mkdir(); (project / 'plans/old.json').write_text('{}')
    state = tmp_path / 'state'
    migrate(project, state, apply=True, offline=True, archive_legacy=True)
    (state / 'plans/new.json').write_text('{"new":true}')
    assert verify(project)['status'] == 'changed_since_migration'
    with pytest.raises(WorkspaceError, match='lose newer state'): rollback(project, offline=True)
    assert (state / 'plans/new.json').exists() and not (project / 'plans').exists()


def test_old_explicit_root_writes_also_block_rollback(tmp_path):
    project = tmp_path / 'project'; project.mkdir()
    (project / 'plans').mkdir(); (project / 'plans/old.json').write_text('{}')
    migrate(project, tmp_path / 'state', apply=True, offline=True)
    (project / 'plans/new.json').write_text('{}')
    with pytest.raises(WorkspaceError, match='Legacy state changed'):
        rollback(project, offline=True)
    assert (project / 'plans/new.json').exists()


def test_unsafe_archive_manifest_cannot_move_arbitrary_paths(tmp_path):
    from geoagent_harness.platform.workspace_migration import MANIFEST
    project = tmp_path / 'project'; project.mkdir()
    state = tmp_path / 'state'
    migrate(project, state, apply=True, offline=True)
    record = json.loads((state / MANIFEST).read_text())
    record['archived_entries'] = ['../../outside']
    (state / MANIFEST).write_text(json.dumps(record))
    with pytest.raises(WorkspaceError, match='archive entries'): rollback(project, offline=True)
    assert (project / CONFIG_NAME).exists()


def test_new_session_after_migration_revokes_previous_authority(project, tmp_path_factory, monkeypatch):
    from geoagent_harness.core.policy.write_policy import session, check, WritePolicyError
    from geoagent_harness.core.policy.recipe_approval import load_recipe_approval
    from tests.test_reusable_recipes_and_runs import execution
    from tests.test_workspace_authority import export_plan
    monkeypatch.setenv('ENABLE_WRITE_TOOLS', 'true')
    with session(project, enabled=True) as before:
        request = execution(project, export_plan('never-executed.csv'))
        approval = load_recipe_approval(project / 'approvals' / request.recipe_approval_filename,
                                        approval_root=project / 'approvals')
        check(project, approval)
    state = tmp_path_factory.mktemp('revocation-parent') / 'state'
    migrate(project, state, apply=True, offline=True, archive_legacy=True)
    with session(project, enabled=True) as after:
        assert after['session_id'] != before['session_id']
        with pytest.raises(WritePolicyError, match='stale'): check(project, approval)
    assert not (project / 'data/output/never-executed.csv').exists()
    assert verify(project)['status'] == 'changed_since_migration'


def test_sqlite_backup_includes_committed_wal_and_preserves_records(tmp_path):
    project = tmp_path / 'project'; project.mkdir()
    db = project / 'planner-workspace/tasks.sqlite3'; db.parent.mkdir()
    with sqlite3.connect(db) as connection:
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('CREATE TABLE sample(id INTEGER, value TEXT)')
        connection.execute("INSERT INTO sample VALUES(1, 'preserved')")
        connection.commit()
        state = tmp_path / 'state'
        result = migrate(project, state, apply=True, offline=True)
        assert result['exact_copy'] and not result['source_only']
        with sqlite3.connect(state / 'planner-workspace/tasks.sqlite3') as copied:
            assert copied.execute('SELECT * FROM sample').fetchall() == [(1, 'preserved')]
        assert not (state / 'planner-workspace/tasks.sqlite3-wal').exists()


def test_new_wal_commits_block_rollback_even_before_checkpoint(tmp_path):
    project = tmp_path / 'project'; project.mkdir()
    db = project / 'planner-workspace/tasks.sqlite3'; db.parent.mkdir()
    with sqlite3.connect(db) as connection:
        connection.execute('CREATE TABLE sample(value TEXT)')
        connection.commit()
    state = tmp_path / 'state'
    migrate(project, state, apply=True, offline=True)
    copied = state / 'planner-workspace/tasks.sqlite3'
    connection = sqlite3.connect(copied)
    try:
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        original = copied.read_bytes()
        connection.execute("INSERT INTO sample VALUES('new committed state')")
        connection.commit()
        assert copied.read_bytes() == original  # New content exists only in WAL.
        assert not verify(project)['exact_copy']
        with pytest.raises(WorkspaceError, match='lose newer state'): rollback(project, offline=True)
    finally: connection.close()


@pytest.mark.parametrize('kind', ['link', 'fifo', 'existing_destination', 'online', 'inside_project'])
def test_unsafe_or_unconfirmed_migrations_do_not_change_source(tmp_path, kind):
    import os
    project = tmp_path / 'project'; project.mkdir()
    plans = project / 'plans'; plans.mkdir()
    source = plans / 'record.json'; source.write_text('{}')
    state = tmp_path / 'state'
    if kind == 'link': (plans / 'linked').symlink_to(source)
    elif kind == 'fifo': os.mkfifo(plans / 'fifo')
    elif kind == 'existing_destination': state.mkdir()
    elif kind == 'inside_project': state = project / 'new-state'
    with pytest.raises(WorkspaceError):
        migrate(project, state, apply=True, offline=kind != 'online', archive_legacy=True)
    assert source.read_text() == '{}' and not (project / CONFIG_NAME).exists()


def test_active_launcher_blocks_migration_without_config_change(tmp_path):
    from geoagent_harness.core.policy.write_policy import session
    project = tmp_path / 'project'; project.mkdir()
    with session(project):
        with pytest.raises(WorkspaceError, match='in use'):
            migrate(project, tmp_path / 'state', apply=True, offline=True)
    assert not (project / CONFIG_NAME).exists() and not (tmp_path / 'state').exists()


def test_migrated_workspace_cannot_bind_to_a_different_project(tmp_path):
    project = tmp_path / 'project'; project.mkdir()
    state = tmp_path / 'state'
    migrate(project, state, apply=True, offline=True)
    other = tmp_path / 'other'; other.mkdir(); configure(other, state)
    with pytest.raises(WorkspaceError, match='another source project'):
        WorkspaceLayout.load(other)


def test_builder_cli_defaults_relocate_but_explicit_roots_remain_explicit(project, monkeypatch):
    from tests.test_builder_materialization_cli import write_generation
    monkeypatch.chdir(project)
    configure(project, 'state')
    generation = project / 'state/builder-generations'; generation.mkdir(parents=True)
    file = write_generation(generation)
    runner = CliRunner()
    result = runner.invoke(app, ['materialize-builder-proposal', '--generation-file', str(file)])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    candidate = Path(payload['candidate_path'])
    assert candidate.is_relative_to(project / 'state/builder-candidates')
    inspected = runner.invoke(app, ['inspect-builder-candidate', str(candidate)])
    assert inspected.exit_code == 0, inspected.output
    assert json.loads(inspected.stdout)['passed']
    custom = project / 'custom-candidates'
    other = runner.invoke(app, ['materialize-builder-proposal', '--generation-file', str(file),
        '--candidate-root', str(custom)])
    assert other.exit_code == 0, other.output
    assert Path(json.loads(other.stdout)['candidate_path']).is_relative_to(custom)
    assert not (project / 'builder-candidates').exists()


def test_cli_migration_preview_and_confirmed_cutover(tmp_path):
    project = tmp_path / 'project'; project.mkdir()
    state = tmp_path / 'state'
    runner = CliRunner()
    result = runner.invoke(app, ['workspace-migrate', str(state), '--project-root', str(project)])
    assert result.exit_code == 0, result.output
    assert not state.exists() and not (project / CONFIG_NAME).exists()
    result = runner.invoke(app, ['workspace-migrate', str(state), '--project-root', str(project), '--apply', '--offline'])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)['exact_copy']
    result = runner.invoke(app, ['workspace-verify', '--project-root', str(project)])
    assert result.exit_code == 0 and json.loads(result.stdout)['source_only']


def test_reviewed_context_and_intent_survive_migration_and_still_recheck_history(tmp_path):
    from tests.test_intent_review import IntentReviewTests
    from geoagent_harness.agents.roles.intent.review import save_reviewed_intent, load_reviewed_intent
    from geoagent_harness.agents.roles.intent.inventory import reviewed_context_inventory
    from geoagent_harness.core.ledger.task_history.service import append_task_event
    fixture = IntentReviewTests(); fixture.setUp()
    try:
        project = fixture.root
        saved = save_reviewed_intent(**fixture.args)
        before = load_reviewed_intent(project_root=project, filename=saved['review_filename'])
        state = tmp_path / 'review-state'
        migrate(project, state, apply=True, offline=True, archive_legacy=True)
        assert load_reviewed_intent(project_root=project, filename=saved['review_filename']) == before
        assert all(r['status'] == 'available' for r in reviewed_context_inventory(project_root=project)['reviews'])
        append_task_event(root=state / 'task-history', task_id='task-intent-review',
                          event_type='decision', summary='A later decision')
        assert all(r['status'] == 'blocked' for r in reviewed_context_inventory(project_root=project)['reviews'])
        assert not before['plan_approved'] and not before['execution_performed']
    finally: fixture.doCleanups()
