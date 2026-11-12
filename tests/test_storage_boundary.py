"""R3 metadata/contract compatibility on disposable default and relocated workspaces."""
from contextlib import contextmanager
import hashlib
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys

import pytest

from geoagent_harness.contracts.errors import TaskActionError
from geoagent_harness.contracts.planning import PlannerResult
from geoagent_harness.platform.storage.contracts import RepositoryError
from geoagent_harness.platform.storage.provider import repositories, using_repository_provider
from geoagent_harness.platform.storage import metadata
from geoagent_harness.task_actions import planning_tasks

ROOT = Path(__file__).resolve().parents[1]
CHAT = 'a' * 32
OTHER = 'b' * 32


@pytest.fixture(params=[False, True], ids=['default-root', 'relocated-root'])
def project(tmp_path, request):
    root = tmp_path / 'project'; root.mkdir()
    if request.param:
        (root / 'actioncharter.workspace.json').write_text(json.dumps({
            'version': 1, 'state_root': str(tmp_path / 'state')}))
    return root


def test_transactions_and_identity_retain_the_legacy_callable_identity():
    from geoagent_harness.contracts.errors import InterfaceApiError, TaskActionError as LegacyError
    assert LegacyError is InterfaceApiError is TaskActionError
    assert planning_tasks.transaction is metadata.transaction
    assert planning_tasks.database is metadata.raw_database
    assert planning_tasks._identity is metadata.validate_identity
    assert import_module('geoagent_harness.contracts.planning') is import_module('geoagent_harness.contracts.planning')


def test_absent_reads_do_not_create_runtime_state(project):
    before = sorted(str(p.relative_to(project)) for p in project.rglob('*'))
    with metadata.transaction(project) as unit:
        assert unit is None
        assert metadata.read_record(unit, 'conversations', CHAT) is None
    assert sorted(str(p.relative_to(project)) for p in project.rglob('*')) == before


def test_raw_repository_and_legacy_views_share_unchanged_encoded_records(project):
    value = {'conversation_id': CHAT, 'revision': 1, 'text': 'café'}
    expected = '{"conversation_id":"' + CHAT + '","revision":1,"text":"café"}'
    with metadata.transaction(project, write=True) as unit:
        metadata.write_record(unit, 'conversations', CHAT, value)
    with planning_tasks.database(project) as db:
        assert db.execute('SELECT value FROM conversations WHERE id=?', (CHAT,)).fetchone()[0] == expected
        assert planning_tasks._get(db, 'conversations', CHAT) == value
    with planning_tasks.transaction(project, write=True) as unit:
        planning_tasks._put(unit, 'conversations', CHAT, {**value, 'revision': 2})
    with metadata.transaction(project) as unit:
        assert metadata.read_record(unit, 'conversations', CHAT)['revision'] == 2


def test_domain_failure_rolls_back_earlier_metadata_writes(project):
    with pytest.raises(TaskActionError, match='fixture rollback'):
        with metadata.transaction(project, write=True) as unit:
            metadata.write_record(unit, 'conversations', CHAT, {'conversation_id': CHAT, 'revision': 0})
            raise TaskActionError('fixture rollback')
    with metadata.transaction(project) as unit:
        assert metadata.read_record(unit, 'conversations', CHAT) is None


def test_record_count_limit_still_allows_updates(project, monkeypatch):
    monkeypatch.setattr(metadata, 'MAX_RECORDS', 1)
    with metadata.transaction(project, write=True) as unit:
        metadata.write_record(unit, 'conversations', CHAT, {'conversation_id': CHAT, 'revision': 0})
        metadata.write_record(unit, 'conversations', CHAT, {'conversation_id': CHAT, 'revision': 1})
        with pytest.raises(TaskActionError, match='storage limit reached'):
            metadata.write_record(unit, 'conversations', OTHER, {'conversation_id': OTHER})
    with metadata.transaction(project) as unit:
        assert metadata.read_record(unit, 'conversations', CHAT)['revision'] == 1
        assert metadata.read_record(unit, 'conversations', OTHER) is None


@pytest.mark.parametrize('identity', [None, 1, '', 'a' * 31, 'a' * 33, 'A' * 32])
def test_invalid_identity_fails_before_serialization(identity):
    with pytest.raises(TaskActionError, match='Invalid planning task identity'):
        metadata.write_record(None, 'conversations', identity, {'unserializable': object()})


def test_byte_limit_fails_before_existing_record_callback(project, monkeypatch):
    monkeypatch.setattr(metadata, 'MAX_RECORD_BYTES', 64)
    def forbidden(*args):
        pytest.fail('Oversized record must be rejected before reading existing domain state')
    with metadata.transaction(project, write=True) as unit:
        with pytest.raises(TaskActionError, match='byte bound'):
            metadata.write_record(unit, 'conversations', CHAT,
                                  {'conversation_id': CHAT, 'text': 'é' * 40}, existing_reader=forbidden)


def test_read_rejects_changed_record_identity(project):
    with repositories(project).transaction(write=True) as unit:
        unit.records('conversations').put(CHAT, json.dumps({'conversation_id': OTHER}))
    with metadata.transaction(project) as unit:
        with pytest.raises(TaskActionError, match='record identity changed'):
            metadata.read_record(unit, 'conversations', CHAT)


def test_existing_memory_still_passes_the_domain_validator_before_update(project):
    invalid = {'task_id': CHAT, 'revision': 0}
    with repositories(project).transaction(write=True) as unit:
        unit.records('memories').put(CHAT, json.dumps(invalid))
    with pytest.raises(ValueError):
        with metadata.transaction(project, write=True) as unit:
            planning_tasks._put(unit, 'memories', CHAT, {**invalid, 'revision': 1})
    with metadata.transaction(project) as unit:
        assert metadata.read_record(unit, 'memories', CHAT) == invalid


def test_provider_errors_keep_the_error_type_message_and_cause(project):
    error = RepositoryError('fixture unavailable')
    class Unavailable:
        def __init__(self, root):
            self.root = root
        @contextmanager
        def transaction(self, *, write=False):
            raise error
            yield  # Makes the fixture a context manager without opening any resource.
    with using_repository_provider(Unavailable):
        with pytest.raises(TaskActionError, match='fixture unavailable') as observed:
            with metadata.transaction(project):
                pytest.fail('Unavailable provider cannot yield a transaction')
    assert observed.value.__cause__ is error


def test_plan_contract_move_preserves_canonical_bytes_and_nonexecution_fields(project):
    from geoagent_harness.core.policy.approvals.service import canonical_plan_json, plan_sha256
    result = PlannerResult(model='fixture', original_request='Inspect', context_references=[], plan={
        'summary': 'Inspect', 'steps': [{'step_id': 'step_1', 'skill': 'inspect_csv',
                                      'purpose': 'Inspect', 'arguments': {'path': 'data/input/source.csv'}}]})
    expected = ('{"assumptions":[],"execution_performed":false,"risks":[],"schema_version":"1.0",'
                '"status":"planned","steps":[{"arguments":{"path":"data/input/source.csv"},'
                '"expected_artifacts":[],"purpose":"Inspect","requires_approval":false,'
                '"skill":"inspect_csv","step_id":"step_1","validation_required":false}],'
                '"summary":"Inspect","validation_performed":false}')
    assert canonical_plan_json(result.plan) == expected
    assert plan_sha256(result.plan) == hashlib.sha256(expected.encode()).hexdigest()
    plans = repositories(project).documents('plans')
    content = result.model_dump_json()
    plans.create('fixture.json', content)
    assert plans.load('fixture.json').model_dump_json() == content
    assert (plans.directory / 'fixture.json').read_text() == content
    with pytest.raises(ValueError):
        PlannerResult.model_validate({**result.model_dump(), 'plan': {**result.plan.model_dump(), 'execution_performed': True}})


def test_storage_and_plan_contracts_load_without_task_actions_or_planner_roles(tmp_path):
    root = tmp_path / 'project'; root.mkdir()
    code = f'''import sys
from pathlib import Path
from geoagent_harness.platform.storage.metadata import transaction, read_record
from geoagent_harness.contracts.planning import PlannerResult
with transaction(Path({str(root)!r})) as unit:
    assert read_record(unit, 'conversations', {'a'*32!r}) is None
assert not any(name.startswith(('geoagent_harness.task_actions', 'geoagent_harness.agents.roles.planner',
                               'geoagent_harness.interface_api', 'geoagent_harness.platform.model_gateway')) for name in sys.modules)
'''
    result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
