"""P0-2b ownership fixtures; no real workspace, model, container or database service."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from geoagent_harness.platform import project_identity as identity
from geoagent_harness.platform.workspace import CONFIG_NAME, OWNER_NAME, WorkspaceLayout, WorkspaceError
from geoagent_harness.platform.workspace_migration import migrate, rollback, verify
from geoagent_harness.platform.storage.action_ledger import LocalActionLedger
from geoagent_harness.contracts.task_context import Actor, RunContext, PolicyDecision, DuplicateAction
from geoagent_harness.core.policy import write_policy


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()
    return root


def claim(project, *, key='one', namespace='local'):
    ledger = LocalActionLedger(project, namespace=namespace)
    run = RunContext(str(project), idempotency_key=key)
    ledger.claim(identity=run.run_id, run=run, actor=Actor(), action='fixture',
                 fingerprint='fixed', parent=None, key=key, at='fixture', decision=PolicyDecision('allow', 'fixture'))
    return run


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_legacy_reads_create_no_identity_or_state(project):
    before = list(project.iterdir())
    assert identity.status(project)['mode'] == 'legacy_path'
    assert identity.ownership_scope(project) == identity.path_scope(project)
    assert list(project.iterdir()) == before


@pytest.mark.parametrize('namespace', ['local', 'mcp'])
def test_adoption_preserves_all_claim_and_event_bytes(project, namespace):
    run = claim(project, namespace=namespace)
    path = project / ('workflow-state' if namespace == 'local' else 'traces/.action-audit') / 'action-ledger.sqlite3'
    original = digest(path)
    recorded = LocalActionLedger(project, namespace=namespace).events(run.run_id)
    result = identity.initialize(project, offline=True)
    assert result['mode'] == 'stable' and result['execution_authority'] is False
    assert digest(path) == original
    assert LocalActionLedger(project, namespace=namespace).events(run.run_id) == recorded
    with pytest.raises(DuplicateAction):
        claim(project, namespace=namespace)
    assert identity.read_record(project)['legacy_scope'] == identity.path_scope(project)


def test_verified_source_rename_keeps_id_claims_and_policy_boundary(project):
    identity.initialize(project, offline=True)
    stable = identity.resolve_identity(project)
    run = claim(project)
    db = project / 'workflow-state/action-ledger.sqlite3'
    original = digest(db)
    with write_policy.session(project, enabled=True):
        old_ticket = write_policy.ticket(project)
    moved = project.with_name('moved')
    project.rename(moved)
    with pytest.raises(WorkspaceError, match='moved'):
        WorkspaceLayout.load(moved)
    identity.rebind(moved, offline=True)
    assert identity.resolve_identity(moved) == stable
    assert digest(moved / 'workflow-state/action-ledger.sqlite3') == original
    assert LocalActionLedger(moved).events(run.run_id)
    with pytest.raises(DuplicateAction):
        claim(moved)
    assert write_policy.snapshot(moved) is None
    with write_policy.session(moved, enabled=False) as current:
        assert current['session_id'] != old_ticket[1]
        assert current['enabled'] is False


def test_external_state_adoption_move_and_migration_receipt(project, tmp_path):
    (project / 'plans').mkdir()
    (project / 'plans/immutable.json').write_text('{"old":"evidence"}')
    state = tmp_path / 'state'
    migrate(project, state, offline=True, apply=True, archive_legacy=True)
    identity.initialize(project, offline=True)
    project_id = identity.resolve_identity(project).project_id
    assert json.loads((state / OWNER_NAME).read_text()) == {'version': 2, 'project_id': project_id}
    moved = project.with_name('moved')
    project.rename(moved)
    identity.rebind(moved, offline=True)
    assert verify(moved)['exact_copy'] is True
    assert identity.resolve_identity(moved).project_id == project_id
    with pytest.raises(WorkspaceError, match='moved'):
        rollback(moved, offline=True)


def test_stable_identity_survives_state_cutover_and_safe_rollback(project, tmp_path):
    identity.initialize(project, offline=True)
    before = identity.read_record(project)
    run = claim(project)
    state = tmp_path / 'state'
    assert migrate(project, state, offline=True, apply=True)['exact_copy']
    assert identity.resolve_identity(project).project_id == before['project_id']
    assert LocalActionLedger(project).events(run.run_id)
    assert rollback(project, offline=True)['status'] == 'rolled_back'
    assert identity.read_record(project) == before
    with pytest.raises(DuplicateAction):
        claim(project)


def test_copied_project_or_marker_cannot_claim_original_state(project, tmp_path):
    state = tmp_path / 'state'
    migrate(project, state, offline=True, apply=True)
    identity.initialize(project, offline=True)
    copied = tmp_path / 'copied'
    shutil.copytree(project, copied)
    with pytest.raises(WorkspaceError, match='Copied'):
        WorkspaceLayout.load(copied)
    with pytest.raises(identity.ProjectIdentityError, match='Old source'):
        identity.rebind(copied, offline=True)
    project.rename(tmp_path / 'original-moved')
    with pytest.raises(identity.ProjectIdentityError, match='filesystem object'):
        identity.rebind(copied, offline=True)


def test_copied_state_cannot_be_substituted(project, tmp_path):
    state = tmp_path / 'state'
    migrate(project, state, offline=True, apply=True)
    identity.initialize(project, offline=True)
    clone = tmp_path / 'cloned-state'
    shutil.copytree(state, clone)
    (project / CONFIG_NAME).write_text(json.dumps({'version': 1, 'state_root': str(clone)}))
    with pytest.raises(WorkspaceError, match='binding changed'):
        WorkspaceLayout.load(project)


def test_independent_fresh_projects_have_distinct_ids(project, tmp_path):
    other = tmp_path / 'independent'
    other.mkdir()
    identity.initialize(project, offline=True)
    identity.initialize(other, offline=True)
    assert identity.ownership_scope(project) != identity.ownership_scope(other)


def test_active_owner_blocks_adoption_without_changing_state(project):
    with write_policy.session(project, enabled=True):
        with pytest.raises(WorkspaceError, match='in use'):
            identity.initialize(project, offline=True)
        assert not (project / identity.IDENTITY_NAME).exists()


def test_active_owner_follows_id_even_when_directory_has_moved(project):
    identity.initialize(project, offline=True)
    moved = project.with_name('moved')
    with write_policy.session(project, enabled=True):
        project.rename(moved)
        with pytest.raises(identity.ProjectIdentityError, match='in use'):
            identity.rebind(moved, offline=True)
    identity.rebind(moved, offline=True)


def test_unmanaged_artifact_lease_blocks_rebind(project):
    identity.initialize(project, offline=True)
    (project / 'plans').mkdir()
    lock = project / 'plans/fixture.lock'
    lock.touch()
    moved = project.with_name('moved')
    with lock.open() as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        project.rename(moved)
        with pytest.raises(identity.ProjectIdentityError, match='in use'):
            identity.rebind(moved, offline=True)
    identity.rebind(moved, offline=True)


@pytest.mark.parametrize('operation', ['initialize', 'rebind'])
def test_offline_confirmation_is_required(project, operation):
    with pytest.raises(identity.ProjectIdentityError, match='offline'):
        getattr(identity, operation)(project)


@pytest.mark.parametrize('bad', ['symlink', 'hardlink', 'oversize', 'invalid', 'writable'])
def test_invalid_identity_never_falls_back_to_path_ownership(project, bad):
    marker = project / identity.IDENTITY_NAME
    if bad == 'symlink':
        target = project / 'other'
        target.write_text('{}')
        marker.symlink_to(target)
    elif bad == 'hardlink':
        marker.write_text('{}')
        os.link(marker, project / 'other')
    else:
        marker.write_text('x' * 4097 if bad == 'oversize' else '{}')
        if bad == 'writable':
            marker.chmod(0o666)
    with pytest.raises(WorkspaceError):
        WorkspaceLayout.load(project)


def test_foreign_audit_scope_is_not_adopted(project, tmp_path):
    foreign = tmp_path / 'foreign'
    foreign.mkdir()
    claim(foreign)
    shutil.copytree(foreign / 'workflow-state', project / 'workflow-state')
    with pytest.raises(identity.ProjectIdentityError, match='another project'):
        identity.initialize(project, offline=True)
    assert not (project / identity.IDENTITY_NAME).exists()


def test_installed_cli_uses_explicit_project_from_another_directory(project, tmp_path):
    identity.initialize(project, offline=True)
    result = subprocess.run([sys.executable, '-m', 'geoagent_harness.cli', 'project-identity',
                             '--project-root', str(project)], cwd=tmp_path, capture_output=True, text=True,
                            timeout=20, env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['project_id'] == identity.resolve_identity(project).project_id


def test_identity_cli_is_not_itself_a_workflow_or_audit_mutation(project):
    from geoagent_harness.apps.cli.main import app
    runner = CliRunner()
    result = runner.invoke(app, ['project-identity', '--project-root', str(project)])
    assert result.exit_code == 0, result.output
    assert list(project.iterdir()) == []
    result = runner.invoke(app, ['project-identity', '--project-root', str(project), '--initialize', '--offline'])
    assert result.exit_code == 0, result.output
    assert not (project / 'workflow-state').exists()


def test_partial_adoption_publication_blocks_access_and_preserves_payloads(project, tmp_path, monkeypatch):
    from geoagent_harness.platform import workspace_migration
    state = tmp_path / 'state'
    migrate(project, state, offline=True, apply=True)
    owner_before = (state / OWNER_NAME).read_bytes()
    original = workspace_migration._json_write
    def fail_owner(path, value):
        if path == state / OWNER_NAME:
            raise OSError('fixture publication failure')
        return original(path, value)
    monkeypatch.setattr(workspace_migration, '_json_write', fail_owner)
    with pytest.raises(OSError, match='fixture'):
        identity.initialize(project, offline=True)
    assert (state / OWNER_NAME).read_bytes() == owner_before
    with pytest.raises(WorkspaceError, match='another source'):
        WorkspaceLayout.load(project)


def test_invalid_rebind_config_is_rejected_before_marker_changes(project):
    identity.initialize(project, offline=True)
    old = (project / identity.IDENTITY_NAME).read_bytes()
    moved = project.with_name('moved')
    project.rename(moved)
    (moved / CONFIG_NAME).write_text('{"unknown":true}')
    with pytest.raises(identity.ProjectIdentityError, match='Invalid workspace'):
        identity.rebind(moved, offline=True)
    assert (moved / identity.IDENTITY_NAME).read_bytes() == old


def test_old_exact_approval_cannot_gain_fresh_authority_after_identity_move(project, monkeypatch):
    from tests.test_workspace_authority import export_plan
    from tests.test_reusable_recipes_and_runs import execution
    from geoagent_harness.core.policy.recipe_approval import load_recipe_approval
    root = Path(__file__).resolve().parents[1]
    for name in ('context', 'agents'):
        shutil.copytree(root / name, project / name)
    (project / 'data/input').mkdir(parents=True)
    (project / 'data/output').mkdir()
    shutil.copyfile(root / 'data/input/sample_orders.csv', project / 'data/input/sample_orders.csv')
    monkeypatch.setenv('ENABLE_WRITE_TOOLS', 'true')
    identity.initialize(project, offline=True)
    with write_policy.session(project, enabled=True):
        request = execution(project, export_plan('must-not-run.csv'))
        approval = load_recipe_approval(project / 'approvals' / request.recipe_approval_filename,
                                        approval_root=project / 'approvals')
        write_policy.check(project, approval)
    moved = project.with_name('moved')
    project.rename(moved)
    identity.rebind(moved, offline=True)
    with write_policy.session(moved, enabled=True):
        with pytest.raises(write_policy.WritePolicyError, match='stale'):
            write_policy.check(moved, approval)
    assert not (moved / 'data/output/must-not-run.csv').exists()
