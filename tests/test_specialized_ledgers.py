"""Local storage contract acceptance: fixtures only, no model or database service."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import copy_context
from pathlib import Path
import os
import subprocess
import sys

import pytest

from geoagent_harness.platform.storage.ledger_contracts import LedgerStorageError, UnsafeLedgerRecord
from geoagent_harness.platform.storage.ledger_files import LocalImmutableRecords, LocalAttemptLedger
from geoagent_harness.platform.storage.ledger_provider import (
    LocalLedgerRepositories, ledger_repositories, using_ledger_provider,
)
from geoagent_harness.platform.storage.ledger_sqlite import SQLiteSuccessfulMethods, write_policy
from tests.test_reusable_recipes_and_runs import project


@pytest.mark.parametrize('name', ['', '.', '..', '../escape', '/absolute', 'nested/file', 'nested\\file'])
def test_names_cannot_escape_the_selected_ledger(tmp_path, name):
    with pytest.raises(ValueError, match='one path component'):
        LocalAttemptLedger(tmp_path).claim(name, b'data')
    assert list(tmp_path.iterdir()) == []


def test_immutable_record_preserves_bytes_and_cannot_replace(tmp_path):
    records = LocalImmutableRecords(tmp_path)
    with records.create_text('record.json') as stream:
        stream.write('{"text":"café"}\n')
    expected = '{"text":"café"}\n'.encode()
    assert records.read_bytes('record.json', max_bytes=len(expected)) == expected
    with pytest.raises(FileExistsError):
        with records.create_text('record.json'):
            pytest.fail('An existing record must never be opened for writing')
    assert (tmp_path/'record.json').read_bytes() == expected
    assert not hasattr(records, 'replace_snapshot')


@pytest.mark.parametrize('kind', ['symlink', 'hardlink', 'fifo', 'directory', 'oversize'])
def test_bounded_read_rejects_unsafe_files_without_blocking(tmp_path, kind):
    target = tmp_path/'record'
    original = tmp_path/'original'
    original.write_bytes(b'123')
    if kind == 'symlink': target.symlink_to(original)
    elif kind == 'hardlink': os.link(original, target)
    elif kind == 'fifo': os.mkfifo(target)
    elif kind == 'directory': target.mkdir()
    else: target.write_bytes(b'12345')
    with pytest.raises(OSError):
        LocalImmutableRecords(tmp_path).read_bytes('record', max_bytes=4)
    assert original.read_bytes() == b'123'


def test_sync_failure_consumes_record_name_without_implicit_retry(tmp_path, monkeypatch):
    records = LocalImmutableRecords(tmp_path)
    def unavailable(): raise OSError('fixture durability failure')
    monkeypatch.setattr(records, 'sync', unavailable)
    with pytest.raises(OSError, match='durability'):
        with records.create_text('record') as stream: stream.write('uncertain')
    with pytest.raises(FileExistsError):
        with records.create_text('record'): pass
    assert (tmp_path/'record').read_text() == 'uncertain'


def test_two_processes_cannot_publish_the_same_immutable_package(tmp_path):
    destination = tmp_path/'packages'
    destination.mkdir()
    staged = [tmp_path/'first', tmp_path/'second']
    for index, path in enumerate(staged):
        path.mkdir()
        (path/'owner').write_text(str(index))
    script = '''
import sys
from pathlib import Path
from geoagent_harness.platform.storage.ledger_files import LocalImmutableRecords
sys.stdin.readline()
try:
    LocalImmutableRecords(Path(sys.argv[1])).publish_directory(Path(sys.argv[2]), 'same')
except FileExistsError:
    print('exists')
else:
    print('created')
'''
    processes = [subprocess.Popen([sys.executable, '-c', script, str(destination), str(path)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for path in staged]
    try:
        for process in processes:
            process.stdin.write('go\n')
            process.stdin.flush()
        outputs = [process.communicate(timeout=15) for process in processes]
        assert all(process.returncode == 0 for process in processes), outputs
        assert sorted(out.strip() for out, _ in outputs) == ['created', 'exists']
        assert (destination/'same/owner').read_text() in {'0', '1'}
        assert sum(path.exists() for path in staged) == 1
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()


def test_existing_empty_directory_cannot_be_replaced(tmp_path):
    (tmp_path/'existing').mkdir()
    (tmp_path/'staged').mkdir()
    (tmp_path/'staged/content').write_text('must remain staged')
    with pytest.raises(FileExistsError):
        LocalImmutableRecords(tmp_path).publish_directory(tmp_path/'staged', 'existing')
    assert list((tmp_path/'existing').iterdir()) == []
    assert (tmp_path/'staged/content').is_file()


def test_claim_is_exclusive_and_snapshot_never_rewrites_events(tmp_path):
    ledger = LocalAttemptLedger(tmp_path)
    ledger.claim('claim', b'claimed')
    with pytest.raises(FileExistsError): ledger.claim('claim', b'repeated')
    ledger.append('events', lambda: b'claimed\n', create=True, max_existing_bytes=64)
    ledger.append('events', lambda: b'unknown\n', create=False, max_existing_bytes=64)
    ledger.replace_snapshot('status', b'unknown')
    ledger.replace_snapshot('status', b'checked')
    assert (tmp_path/'claim').read_bytes() == b'claimed'
    assert (tmp_path/'events').read_bytes() == b'claimed\nunknown\n'
    assert (tmp_path/'status').read_bytes() == b'checked'
    assert not list(tmp_path.glob('.attempt-*'))


def test_attempt_rejects_unsafe_or_oversized_history_before_constructing_event(tmp_path):
    ledger = LocalAttemptLedger(tmp_path)
    ledger.claim('events', b'oversized')
    def forbidden(): pytest.fail('No event construction before storage validation')
    with pytest.raises(OSError, match='Unsafe'): ledger.append('events', forbidden, create=False, max_existing_bytes=1)
    with pytest.raises(FileExistsError): ledger.append('events', forbidden, create=True, max_existing_bytes=64)
    assert (tmp_path/'events').read_bytes() == b'oversized'


def test_short_append_is_uncertain_and_does_not_release_claim(tmp_path, monkeypatch):
    ledger = LocalAttemptLedger(tmp_path)
    ledger.claim('claim', b'exact authority')
    actual_write = os.write
    monkeypatch.setattr(os, 'write', lambda fd, data: actual_write(fd, data[:1]))
    with pytest.raises(OSError, match='Incomplete'):
        ledger.append('events', lambda: b'claimed\n', create=True, max_existing_bytes=64)
    with pytest.raises(FileExistsError): ledger.claim('claim', b'exact authority')
    assert (tmp_path/'events').read_bytes() == b'c'


def test_checked_append_serializes_validation_and_preserves_history_on_rejection(tmp_path):
    ledger = LocalAttemptLedger(tmp_path)
    def append(_):
        ledger.append_checked('events', lambda previous: f'{len(previous.splitlines())}\n'.encode(), max_bytes=256)
    with ThreadPoolExecutor(max_workers=4) as workers:
        list(workers.map(append, range(20)))
    expected = ''.join(f'{i}\n' for i in range(20)).encode()
    assert (tmp_path/'events').read_bytes() == expected
    def invalid(previous):
        assert previous == expected
        raise ValueError('invalid sequence')
    with pytest.raises(ValueError, match='sequence'):
        ledger.append_checked('events', invalid, max_bytes=256)
    with pytest.raises(OSError, match='budget'):
        ledger.append_checked('events', lambda previous: b'X'*256, max_bytes=256)
    assert (tmp_path/'events').read_bytes() == expected


def test_checked_append_does_not_modify_hardlink_or_invoke_domain_callback(tmp_path):
    original = tmp_path/'original'
    original.write_bytes(b'evidence\n')
    os.chmod(original, 0o600)
    os.link(original, tmp_path/'events')
    with pytest.raises(UnsafeLedgerRecord):
        LocalAttemptLedger(tmp_path).append_checked('events', lambda _: pytest.fail('Unsafe history'), max_bytes=64)
    assert original.stat().st_mode & 0o777 == 0o600
    assert original.read_bytes() == b'evidence\n'


def test_policy_unit_rolls_back_and_cannot_overwrite_existing_authority(tmp_path):
    database = tmp_path/'policy.sqlite3'
    with write_policy(database) as unit:
        assert not hasattr(unit, 'execute')
        unit.initialize('session', True, False)
        unit.begin_write()
        unit.set_enabled(False)
        unit.bind('uncommitted', 'session', 0)
        unit.rollback()
        assert unit.current()['revision'] == 0
        assert unit.current()['enabled'] == 1
        assert unit.approval_scope('uncommitted') is None
        unit.begin_write()
        unit.bind('digest', 'session', 0)
        unit.commit()
    with pytest.raises(LedgerStorageError):
        with write_policy(database) as unit:
            unit.begin_write()
            unit.bind('digest', 'different-session', 5)
    with write_policy(database) as unit:
        assert unit.approval_scope('digest') == ('session', 0)


def test_policy_writers_observe_committed_revision_under_lock(tmp_path):
    database = tmp_path/'policy.sqlite3'
    with write_policy(database) as unit: unit.initialize('session', True, False)
    def update(_):
        with write_policy(database) as unit:
            unit.begin_write()
            before = unit.current()['revision']
            unit.set_enabled(False)
            unit.record_change('session', before+1, False, 'fixture')
            unit.commit()
            return before
    with ThreadPoolExecutor(max_workers=4) as workers:
        assert sorted(workers.map(update, range(8))) == list(range(8))
    with write_policy(database) as unit: assert unit.current()['revision'] == 8


def test_success_index_keeps_scopes_and_immutable_sources_with_mutable_notes(project):
    unit = SQLiteSuccessfulMethods(project)
    try:
        assert not hasattr(unit, 'execute')
        with pytest.raises(ValueError, match='rollback'):
            with unit:
                unit.begin_write()
                unit.insert('aborted', 'method', None, 'discard')
                raise ValueError('rollback')
        assert unit.count() == 0
        with unit:
            unit.begin_write()
            unit.insert('one', 'method', None, 'payload')
            unit.insert('two', 'method', 'other-chat', 'private')
            unit.save_annotation('one', 'initial')
        with pytest.raises(LedgerStorageError):
            with unit:
                unit.begin_write()
                unit.insert('one', 'method', 'other-chat', 'replacement')
        with unit: unit.save_annotation('one', 'updated')
        assert [row[0] for row in unit.entries(None, 10)] == ['payload']
        assert [row[0] for row in unit.entries('other-chat', 10)] == ['private']
        assert tuple(unit.success('one')) == ('payload', None)
        assert [tuple(row) for row in unit.annotations(None)] == [('one', 'updated')]
    finally: unit.close()


def test_scoped_provider_is_inherited_only_by_explicit_worker_context():
    original = ledger_repositories()
    provider = LocalLedgerRepositories()
    with using_ledger_provider(provider):
        context = copy_context()
        with ThreadPoolExecutor(max_workers=1) as worker:
            assert worker.submit(ledger_repositories).result() is original
            assert worker.submit(context.run, ledger_repositories).result() is provider
    assert ledger_repositories() is original


def test_evidence_round_trip_really_uses_selected_provider(tmp_path):
    from geoagent_harness.core.ledger import recipe_evidence as evidence
    from tests.test_recipe_evidence_storage import example_run_result
    class RecordingProvider(LocalLedgerRepositories):
        def __init__(self): self.calls = []
        def immutable(self, directory):
            self.calls.append(Path(directory))
            return super().immutable(directory)
    provider = RecordingProvider()
    result = example_run_result()
    with using_ledger_provider(provider):
        path = evidence.write_recipe_run_result(result, result_root=tmp_path)
        assert evidence.load_recipe_run_result(path, result_root=tmp_path) == result
    assert provider.calls == [tmp_path, tmp_path]
    assert path.read_text() == evidence.canonical_recipe_run_result_json(result)+'\n'


def test_unbound_approval_after_storage_failure_cannot_enter_write_session(project):
    from geoagent_harness.core.policy import write_policy as policy
    from geoagent_harness.core.policy.approvals.schemas import ApprovalRecord
    from tests.test_approval_service import planner_result, NOW
    from geoagent_harness.core.policy.approvals.service import create_approval
    from geoagent_harness.platform.workspace import runtime_store_path
    class UnavailableBinding(LocalLedgerRepositories):
        @contextmanager
        def write_policy(self, database):
            with super().write_policy(database) as underlying:
                class ClosedUnit:
                    def __getattr__(self, name):
                        if name == 'bind':
                            def fail(*args): raise LedgerStorageError('fixture commit unavailable')
                            return fail
                        return getattr(underlying, name)
                yield ClosedUnit()
    root = runtime_store_path(project, 'approvals')
    with policy.session(project, enabled=True):
        with using_ledger_provider(UnavailableBinding()):
            with pytest.raises(policy.WritePolicyError, match='storage unavailable'):
                create_approval(planner_result=planner_result(), decision='approved',
                    step_ids=['step_2'], approver='fixture', reason='temporary fixture',
                    approval_root=root, project_root=project, now=NOW)
        paths = list(root.glob('*.json'))
        assert len(paths) == 1  # File publication succeeded; binding did not.
        record = ApprovalRecord.model_validate_json(paths[0].read_text())
        with pytest.raises(policy.WritePolicyError, match='missing or stale'):
            policy.check(project, record)
