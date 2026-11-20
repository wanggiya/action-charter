"""P2-0 remount recovery: temporary files only, no owner metadata or live service."""
import fcntl
import json
import os
from pathlib import Path
import shutil

import pytest
from typer.testing import CliRunner

from geoagent_harness.platform import project_identity as identity, project_recovery as recovery
from geoagent_harness.platform.workspace import CONFIG_NAME, OWNER_NAME, WorkspaceLayout, WorkspaceError
from geoagent_harness.platform.workspace_migration import migrate, inventory
from geoagent_harness.core.policy import write_policy
from tests.test_project_identity import claim, digest


def legacy_device_change(project):
    record = identity.read_record(project)
    record = {key: value for key, value in record.items() if not key.endswith('_filesystem')}
    record['version'] = 1
    for key in ('source_object', 'state_object'):
        record[key][0] += 100
    (project / identity.IDENTITY_NAME).write_text(json.dumps(record))
    return record


@pytest.fixture
def bound(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    (project / 'plans').mkdir()
    (project / 'plans/original.json').write_text('{"evidence":"preserved"}')
    identity.initialize(project, offline=True)
    claim(project)
    legacy_device_change(project)
    return project, tmp_path / 'backup'


def recover(project, backup):
    preview = recovery.preview(project, backup)
    return recovery.recover(project, backup, expected_digest=preview['preview_sha256'], offline=True)


def test_preview_is_pure_and_does_not_weaken_normal_guard(bound):
    project, backup = bound
    before = inventory(project)
    marker = (project / identity.IDENTITY_NAME).read_bytes()
    preview = recovery.preview(project, backup)
    assert preview['matching_paths_and_inodes'] and not preview['execution_authority']
    assert len(preview['preview_sha256']) == 64
    assert not backup.exists()
    assert inventory(project) == before
    assert (project / identity.IDENTITY_NAME).read_bytes() == marker
    with pytest.raises(WorkspaceError, match='Copied project identity'):
        WorkspaceLayout.load(project)


@pytest.mark.parametrize('external', [False, True])
def test_recovery_preserves_uuid_claims_and_verified_backup(tmp_path, external):
    project = tmp_path / 'project'
    project.mkdir()
    if external:
        migrate(project, tmp_path / 'state', offline=True, apply=True)
    identity.initialize(project, offline=True)
    from geoagent_harness.platform.storage.action_ledger import LocalActionLedger
    from geoagent_harness.contracts.task_context import DuplicateAction
    run = claim(project)
    state = WorkspaceLayout.load(project).state_root
    ledger = state / 'workflow-state/action-ledger.sqlite3'
    before = digest(ledger)
    original = legacy_device_change(project)
    metadata = {path: path.read_bytes() for path in (project / CONFIG_NAME, state / OWNER_NAME) if path.exists()}
    backup = tmp_path / 'backup'
    result = recover(project, backup)
    assert result['project_id'] == original['project_id']
    assert not result['execution_authority'] and not result['execution_performed']
    assert identity.read_record(project)['version'] == 2
    assert digest(ledger) == before
    assert LocalActionLedger(project).events(run.run_id)
    with pytest.raises(DuplicateAction):
        claim(project)
    assert all(path.read_bytes() == value for path, value in metadata.items())
    assert json.loads((backup / identity.IDENTITY_NAME).read_text()) == original
    receipt = json.loads((backup / 'recovery.json').read_text())
    assert receipt['status'] == 'complete'
    assert receipt['sqlite_logical_sha256']
    assert backup.stat().st_mode & 0o077 == 0
    assert all(path.stat().st_mode & 0o077 == 0 for path in backup.rglob('*'))


def test_v2_binding_accepts_later_device_renumber_but_not_filesystem_change(bound, monkeypatch):
    project, backup = bound
    recover(project, backup)
    stable = identity.resolve_identity(project)
    original = identity._object
    monkeypatch.setattr(identity, '_object', lambda path: [original(path)[0] + 9, original(path)[1]])
    assert identity.resolve_identity(project) == stable
    original_fs = identity._filesystem
    monkeypatch.setattr(identity, '_filesystem', lambda path: original_fs(path) + 1)
    with pytest.raises(identity.ProjectIdentityError, match='Copied project identity'):
        identity.resolve_identity(project)


@pytest.mark.parametrize('version', [1, 2])
def test_actual_copies_are_rejected_even_if_original_path_absent(bound, version):
    project, backup = bound
    if version == 2:
        recover(project, backup)
    copied = project.with_name('copy')
    shutil.copytree(project, copied)
    project.rename(project.with_name('old'))
    copied.rename(project)
    with pytest.raises(identity.ProjectIdentityError, match='copied|Copied'):
        if version == 1:
            recovery.preview(project, backup)
        else:
            identity.resolve_identity(project)


@pytest.mark.parametrize('mutation', ['payload', 'config', 'marker', 'wal'])
def test_stale_preview_cannot_publish(bound, mutation):
    project, backup = bound
    preview = recovery.preview(project, backup)
    if mutation == 'payload':
        (project / 'plans/original.json').write_text('changed')
    elif mutation == 'config':
        (project / CONFIG_NAME).write_text(json.dumps({'version': 1, 'state_root': '.'}))
    elif mutation == 'marker':
        (project / identity.IDENTITY_NAME).write_text(json.dumps(identity.read_record(project), indent=2))
    else:
        (project / 'workflow-state/action-ledger.sqlite3-wal').write_bytes(b'changed fixture')
    before = (project / identity.IDENTITY_NAME).read_bytes()
    with pytest.raises(identity.ProjectIdentityError, match='preview changed'):
        recovery.recover(project, backup, expected_digest=preview['preview_sha256'], offline=True)
    assert not backup.exists() and (project / identity.IDENTITY_NAME).read_bytes() == before


@pytest.mark.parametrize('scope', ['stable', 'legacy', 'artifact'])
def test_active_leases_block_recovery(bound, scope):
    project, backup = bound
    preview = recovery.preview(project, backup)
    record = identity.read_record(project)
    if scope == 'artifact':
        path = project / 'plans/fixture.lock'
        path.touch()
        preview = recovery.preview(project, backup)
        fd = os.open(path, os.O_RDONLY)
    else:
        scope_id = (identity.ProjectIdentity(record['project_id'], record['legacy_scope']).scope
                    if scope == 'stable' else record['legacy_scope'])
        fd = write_policy._owner_fd(project, create=True, scope=scope_id)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(identity.ProjectIdentityError, match='in use'):
            recovery.recover(project, backup, expected_digest=preview['preview_sha256'], offline=True)
    finally:
        os.close(fd)
    assert not backup.exists() and identity.read_record(project)['version'] == 1


@pytest.mark.parametrize('failure', ['copy', 'verification', 'marker', 'receipt'])
def test_interrupted_recovery_keeps_original_or_coherent_v2(bound, monkeypatch, failure):
    project, backup = bound
    before = (project / identity.IDENTITY_NAME).read_bytes()
    original_copy, original_write = recovery._copy_state, recovery._json_write
    def copy(*args):
        if failure == 'copy':
            raise OSError('fixture interrupted backup')
        result = original_copy(*args)
        if failure == 'verification':
            (project / 'plans/original.json').write_text('concurrent change')
        return result
    def write(path, value):
        if ((failure == 'marker' and path == project / identity.IDENTITY_NAME)
                or (failure == 'receipt' and value.get('status') == 'complete')):
            raise OSError('fixture interrupted publication')
        return original_write(path, value)
    monkeypatch.setattr(recovery, '_copy_state', copy)
    monkeypatch.setattr(recovery, '_json_write', write)
    with pytest.raises((OSError, identity.ProjectIdentityError), match='fixture|changed'):
        recover(project, backup)
    receipt = json.loads((backup / 'recovery.json').read_text())
    if failure == 'receipt':
        assert identity.status(project)['mode'] == 'stable'
        assert receipt['status'] == 'verified_before_publication'
    else:
        assert (project / identity.IDENTITY_NAME).read_bytes() == before
        assert receipt['status'] in ('copying', 'verified_before_publication')
    with pytest.raises(identity.ProjectIdentityError, match='existing legacy|must be new'):
        recover(project, backup)  # No automatic retry, replacement or state replay.


def test_foreign_owner_and_changed_paths_are_not_recovery(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    state = tmp_path / 'state'
    migrate(project, state, offline=True, apply=True)
    identity.initialize(project, offline=True)
    legacy_device_change(project)
    owner = state / OWNER_NAME
    owner.write_text('{"version":2,"project_id":"foreign"}')
    with pytest.raises(identity.ProjectIdentityError, match='ownership differs'):
        recovery.preview(project, tmp_path / 'backup')
    project.rename(tmp_path / 'moved')
    with pytest.raises(identity.ProjectIdentityError, match='exact recorded'):
        recovery.preview(tmp_path / 'moved', tmp_path / 'backup')


def test_foreign_audit_scope_blocks_before_backup(bound):
    import sqlite3
    project, backup = bound
    with sqlite3.connect(project / 'workflow-state/action-ledger.sqlite3') as db:
        db.execute('UPDATE action_project_scope SET project_sha256=?', ('f' * 64,))
    with pytest.raises(identity.ProjectIdentityError, match='another project'):
        recover(project, backup)
    assert not backup.exists()


@pytest.mark.parametrize('kind', ['inside_source', 'inside_state', 'existing', 'symlink', 'shared_parent'])
def test_backup_path_cannot_overwrite_or_mix_trust_boundaries(bound, kind, tmp_path):
    project, backup = bound
    if kind in ('inside_source', 'inside_state'):
        backup = project / 'backup'
    elif kind == 'existing':
        backup.mkdir()
    elif kind == 'symlink':
        backup.symlink_to(tmp_path / 'elsewhere')
    else:
        parent = tmp_path / 'shared'
        parent.mkdir(mode=0o777)
        parent.chmod(0o777)
        backup = parent / 'backup'
    with pytest.raises((identity.ProjectIdentityError, WorkspaceError)):
        recovery.preview(project, backup)


def test_no_usable_filesystem_id_means_no_recovery(bound, monkeypatch):
    project, backup = bound
    class Unsupported:
        f_fsid = 0
    monkeypatch.setattr(identity.os, 'statvfs', lambda _: Unsupported())
    with pytest.raises(identity.ProjectIdentityError, match='no usable stable ID'):
        recovery.preview(project, backup)
    assert not backup.exists()


def test_existing_write_approval_is_stale_after_recovery(tmp_path, monkeypatch):
    from tests.test_workspace_authority import export_plan
    from tests.test_reusable_recipes_and_runs import execution
    from geoagent_harness.core.policy.recipe_approval import load_recipe_approval
    project = tmp_path / 'project'
    project.mkdir()
    repo = Path(__file__).resolve().parents[1]
    for name in ('context', 'agents'):
        shutil.copytree(repo / name, project / name)
    (project / 'data/input').mkdir(parents=True)
    (project / 'data/output').mkdir()
    shutil.copyfile(repo / 'data/input/sample_orders.csv', project / 'data/input/sample_orders.csv')
    monkeypatch.setenv('ENABLE_WRITE_TOOLS', 'true')
    identity.initialize(project, offline=True)
    with write_policy.session(project, enabled=True):
        request = execution(project, export_plan('must-not-run.csv'))
        approval = load_recipe_approval(project / 'approvals' / request.recipe_approval_filename,
                                       approval_root=project / 'approvals')
        write_policy.check(project, approval)
    legacy_device_change(project)
    recover(project, tmp_path / 'backup')
    assert write_policy.snapshot(project) is None
    with write_policy.session(project, enabled=False) as current:
        assert current['enabled'] is False
    with write_policy.session(project, enabled=True):
        with pytest.raises(write_policy.WritePolicyError, match='stale'):
            write_policy.check(project, approval)
    assert not (project / 'data/output/must-not-run.csv').exists()


def test_cli_requires_explicit_review_and_offline(bound):
    from geoagent_harness.apps.cli.main import app
    project, backup = bound
    runner = CliRunner()
    base = ['project-identity', '--project-root', str(project), '--backup-root', str(backup)]
    result = runner.invoke(app, [*base, '--preview-recovery'])
    assert result.exit_code == 0, result.output
    preview = json.loads(result.stdout)
    for extra in ([], ['--expected-digest', preview['preview_sha256']]):
        result = runner.invoke(app, [*base, '--recover-device', *extra])
        assert result.exit_code == 2
    result = runner.invoke(app, [*base, '--recover-device', '--offline',
                                 '--expected-digest', preview['preview_sha256']])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)['recovery_status'] == 'complete'
    assert not (project / 'task-history').exists()


@pytest.mark.parametrize('kind', ['symlink', 'hardlink', 'writable'])
def test_unsafe_metadata_blocks_recovery(bound, kind, tmp_path):
    project, backup = bound
    marker = project / identity.IDENTITY_NAME
    if kind == 'symlink':
        saved = tmp_path / 'saved-marker'
        marker.rename(saved)
        marker.symlink_to(saved)
    elif kind == 'hardlink':
        os.link(marker, tmp_path / 'linked-marker')
    else:
        marker.chmod(0o666)
    with pytest.raises((identity.ProjectIdentityError, WorkspaceError)):
        recovery.preview(project, backup)
    assert not backup.exists()


def test_copied_state_with_matching_uuid_is_rejected(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    state = tmp_path / 'state'
    migrate(project, state, offline=True, apply=True)
    identity.initialize(project, offline=True)
    legacy_device_change(project)
    shutil.copytree(state, tmp_path / 'copy')
    state.rename(tmp_path / 'original')
    (tmp_path / 'copy').rename(state)
    with pytest.raises(identity.ProjectIdentityError, match='copied source/state'):
        recovery.preview(project, tmp_path / 'backup')


def test_backup_corruption_is_detected_before_marker_publication(bound, monkeypatch):
    project, backup = bound
    before = (project / identity.IDENTITY_NAME).read_bytes()
    original = recovery.inventory
    def corrupt_then_check(root):
        if root == backup / 'state':
            (root / 'plans/original.json').write_text('fixture corrupt copy')
        return original(root)
    monkeypatch.setattr(recovery, 'inventory', corrupt_then_check)
    with pytest.raises(identity.ProjectIdentityError, match='Backup bytes differ'):
        recover(project, backup)
    assert (project / identity.IDENTITY_NAME).read_bytes() == before


def test_corrupted_metadata_backup_cannot_publish_identity(bound, monkeypatch):
    project, backup = bound
    before = (project / identity.IDENTITY_NAME).read_bytes()
    original = recovery._copy_state
    def corrupt_metadata(*args):
        result = original(*args)
        (backup / identity.IDENTITY_NAME).write_text('{}')
        return result
    monkeypatch.setattr(recovery, '_copy_state', corrupt_metadata)
    with pytest.raises(identity.ProjectIdentityError, match='Backup metadata differs'):
        recover(project, backup)
    assert (project / identity.IDENTITY_NAME).read_bytes() == before


def test_backup_parent_sync_failure_leaves_identity_unchanged(bound, monkeypatch):
    project, backup = bound
    before = (project / identity.IDENTITY_NAME).read_bytes()
    original = os.fsync
    def fail_parent(fd):
        if Path(f'/proc/self/fd/{fd}').resolve() == backup.parent:
            raise OSError('fixture backup directory durability failure')
        return original(fd)
    monkeypatch.setattr(recovery.os, 'fsync', fail_parent)
    with pytest.raises(OSError, match='durability failure'):
        recover(project, backup)
    assert (project / identity.IDENTITY_NAME).read_bytes() == before
    assert json.loads((backup / 'recovery.json').read_text())['status'] == 'verified_before_publication'


def test_first_initialization_falls_back_to_strict_v1_without_filesystem_id(tmp_path, monkeypatch):
    project = tmp_path / 'project'
    project.mkdir()
    class Unsupported:
        f_fsid = 0
    monkeypatch.setattr(identity.os, 'statvfs', lambda _: Unsupported())
    identity.initialize(project, offline=True)
    assert identity.read_record(project)['version'] == 1
    old_object = identity._object
    monkeypatch.setattr(identity, '_object', lambda path: [old_object(path)[0] + 1, old_object(path)[1]])
    with pytest.raises(identity.ProjectIdentityError, match='Copied project identity'):
        identity.resolve_identity(project)


@pytest.mark.parametrize('invalid', [0, -1, True, '123'])
def test_v2_requires_valid_filesystem_binding_fields(bound, invalid):
    project, backup = bound
    recover(project, backup)
    record = identity.read_record(project)
    record['state_filesystem'] = invalid
    (project / identity.IDENTITY_NAME).write_text(json.dumps(record))
    with pytest.raises(identity.ProjectIdentityError, match='Invalid project identity'):
        identity.resolve_identity(project)


def test_backup_includes_exact_crlf_metadata_and_migration_receipt(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    state = tmp_path / 'state'
    migrate(project, state, offline=True, apply=True)
    identity.initialize(project, offline=True)
    record = legacy_device_change(project)
    marker = project / identity.IDENTITY_NAME
    marker.write_bytes((json.dumps(record, indent=2).replace('\n', '\r\n') + '\r\n').encode())
    original = marker.read_bytes()
    backup = tmp_path / 'backup'
    recover(project, backup)
    assert (backup / identity.IDENTITY_NAME).read_bytes() == original
    assert (backup / '.actioncharter-migration.json').read_bytes() == (state / '.actioncharter-migration.json').read_bytes()


def test_recovered_history_reopens_same_workflow_and_outcome_without_dispatch(tmp_path):
    from tests.test_workspace_layout import _inspect
    from geoagent_harness.task_actions.conversation import conversation_turn, TurnRequest
    from geoagent_harness.task_actions.workflow_runs import run_action, RunRequest
    from geoagent_harness.task_actions.planner_submission import submission_action, SubmissionRequest
    project = tmp_path / 'project'
    project.mkdir()
    repo = Path(__file__).resolve().parents[1]
    for name in ('context', 'agents'):
        shutil.copytree(repo / name, project / name)
    (project / 'data/input').mkdir(parents=True)
    (project / 'data/output').mkdir()
    shutil.copyfile(repo / 'data/input/sample_orders.csv', project / 'data/input/sample_orders.csv')
    migrate(project, tmp_path / 'state', offline=True, apply=True)
    identity.initialize(project, offline=True)
    original = _inspect(project)
    run = original['run']
    assert run['status'] == 'completed'
    state = WorkspaceLayout.load(project).state_root
    before = {p: p.read_bytes() for store in ('plans', 'planner-conversations', 'inspection-runs', 'workflow-state')
              for p in (state / store).rglob('*.json')}
    legacy_device_change(project)
    recover(project, tmp_path / 'backup')
    restored = conversation_turn(TurnRequest(action='read', conversation_id='c' * 32), project_root=project)
    assert restored['planner_result']['plan_sha256'] == run['plan_sha256']
    latest = run_action(RunRequest(action='latest', conversation_id='c' * 32,
                                  confirmed_plan_sha256=run['plan_sha256']), project_root=project)
    assert latest['record']['run_id'] == run['run_id'] and not latest['execution_performed']
    receipt = submission_action(SubmissionRequest(action='read', submission_id='d' * 32,
                                                 conversation_id='c' * 32), project_root=project)
    assert receipt['run']['run_id'] == run['run_id']
    assert all(p.read_bytes() == value for p, value in before.items())
    assert len(list((state / 'workflow-state/interface-runs').glob('*.json'))) == 1
    assert not (state / 'approvals').exists() and not list((project / 'data/output').iterdir())
