"""Complete shared lifecycle over a disposable transactional relation fixture, no DB service."""
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
from pathlib import Path

import pytest

from geoagent_harness.platform.settings import MCPSettings
from geoagent_harness.data.databases.postgis.inspection.schemas import PostGISColumn
from geoagent_harness.data.databases.postgis.inspection.service import inspect_postgis_table
from geoagent_harness.data.databases.postgis.promotion.plan.service import plan_postgis_promotion
from geoagent_harness.data.databases.postgis.promotion.approval.service import create_postgis_promotion_approval
from geoagent_harness.data.databases.postgis.promotion.approval.storage import persist_postgis_promotion_approval, postgis_promotion_approval_sha256
from geoagent_harness.data.databases.postgis.promotion.execution.service import execute_postgis_promotion, PostGISPromotionExecutionError
from geoagent_harness.data.databases.postgis.promotion.execution.storage import persist_postgis_promotion_execution
from geoagent_harness.data.databases.postgis.promotion.verification.service import verify_postgis_promotion
from geoagent_harness.data.databases.postgis.promotion.verification.storage import persist_postgis_promotion_verification
from geoagent_harness.data.databases.postgis.rollback.plan.service import plan_postgis_rollback
from geoagent_harness.data.databases.postgis.rollback.plan.storage import persist_postgis_rollback_plan, postgis_rollback_plan_sha256
from geoagent_harness.data.databases.postgis.rollback.approval.service import create_postgis_rollback_approval
from geoagent_harness.data.databases.postgis.rollback.approval.storage import persist_postgis_rollback_approval, postgis_rollback_approval_sha256
from geoagent_harness.data.databases.postgis.rollback.execution.service import execute_postgis_rollback, PostGISRollbackExecutionError
from geoagent_harness.data.databases.postgis.rollback.execution.storage import persist_postgis_rollback_execution
from geoagent_harness.data.databases.postgis.rollback.verification.service import verify_postgis_rollback
from geoagent_harness.data.databases.postgis.rollback.verification.storage import persist_postgis_rollback_verification
from geoagent_harness.platform.workspace import runtime_store_path
from geoagent_harness.platform.workspace_migration import migrate
from tests.test_postgis_promotion_plan import request
from tests.test_postgis_promotion_approval import NOW
from tests.test_workspace_layout import configure


SCHEMA = 'agent_sandbox'


class Database:
    def __init__(self):
        self.tables = {(SCHEMA, 'reference_layer'): [10, 20], (SCHEMA, 'candidate_layer'): [100, 200]}
        self.readers = []

    def reader(self):
        reader = Reader(self.tables); self.readers.append(reader)
        return reader


class Reader:
    def __init__(self, tables): self.tables = tables; self.closed = False; self.observed = []
    def table_exists(self, schema, table): self.observed.append((schema, table)); return (schema, table) in self.tables
    def columns(self, schema, table): return [PostGISColumn(ordinal_position=1, name='id', data_type='integer', nullable=False)]
    def keys(self, schema, table): return [('p', table+'_pkey', ['id'])]
    def geometry_metadata(self, schema, table): return []
    def row_count(self, schema, table): return len(self.tables[(schema, table)])
    def geometry_statistics(self, *args): raise AssertionError('Fixture has no geometry')
    def close(self): self.closed = True


class Transaction(Reader):
    def __init__(self, database, settings, *, fail=None):
        super().__init__(deepcopy(database.tables))
        self.database = database; self.settings = settings; self.fail = fail
        self.renames = []; self.committed = False; self.rolled_back = False; self.locked = []
    def lock(self, relations): self.locked = relations
    def inspect(self, request): return inspect_postgis_table(request=request, settings=self.settings, reader=self)
    def rename(self, source, target):
        self.renames.append((source, target))
        if self.fail == 'second_rename' and len(self.renames) == 2: raise RuntimeError('password=fixture-private')
        assert target not in self.tables
        self.tables[target] = self.tables.pop(source)
        if self.fail == 'validation' and len(self.renames) == 2:
            self.tables[target].append(999)
    def commit(self):
        if self.fail == 'commit_before': raise RuntimeError('password=fixture-private')
        self.database.tables = deepcopy(self.tables); self.committed = True
        if self.fail == 'commit_after': raise RuntimeError('password=fixture-private')
    def rollback(self):
        if self.fail == 'rollback': raise RuntimeError('password=fixture-private')
        self.rolled_back = True
    def close(self):
        self.closed = True
        if self.fail == 'close': raise RuntimeError('password=fixture-private')


def prepare(root, *, relocated=False):
    root.mkdir()
    if relocated: configure(root, root.parent / 'private-state')
    settings = MCPSettings(project_root=root, input_root=root/'data/input',
                           output_root=root/'data/output', enable_write_tools=True)
    database = Database()
    plan = plan_postgis_promotion(request=request(), settings=settings, reader=database.reader())
    plan_root = runtime_store_path(root, 'postgis-promotion-plans'); plan_root.mkdir(parents=True)
    plan_file = plan_root / 'PLAN.json'; plan_file.write_text(json.dumps(plan.model_dump(mode='json')))
    approval = create_postgis_promotion_approval(plan_result=plan, decision='approved', approver='fixture',
        reason='Temporary relations only', now=NOW, expires_at=NOW+timedelta(hours=1))
    approval_root = runtime_store_path(root, 'postgis-promotion-approvals')
    stored = persist_postgis_promotion_approval(approval, approval_root=approval_root)
    kwargs = dict(plan_file=plan_file, plan_root=plan_root, approval_file=Path(stored.approval_file),
        approval_root=approval_root, settings=settings, confirm_plan_sha256=plan.plan_sha256,
        confirm_approval_sha256=postgis_promotion_approval_sha256(approval), now=NOW+timedelta(minutes=1))
    return database, plan, approval, kwargs


def receipts(root):
    return [json.loads(path.read_text()) for path in runtime_store_path(root, 'workflow-state', 'postgis-attempts').glob('*.json')]


def assert_legacy_bytes(path, value):
    expected = json.dumps(value.model_dump(mode='json'), sort_keys=True, indent=2, ensure_ascii=False)+'\n'
    assert path.read_bytes() == expected.encode()
    assert hashlib.sha256(expected.encode()).hexdigest() in path.parent.name


def prepare_rollback(root, *, relocated=False):
    db, plan, approval, args = prepare(root, relocated=relocated)
    original = deepcopy(db.tables)
    transaction = Transaction(db, args['settings'])
    executed = execute_postgis_promotion(**args, transaction=transaction)
    er = runtime_store_path(root, 'postgis-promotion-executions')
    stored = persist_postgis_promotion_execution(executed, execution_root=er)
    reader = db.reader()
    verified = verify_postgis_promotion(execution_file=Path(stored.execution_file), execution_root=er,
        plan_file=args['plan_file'], plan_root=args['plan_root'], settings=args['settings'], reader=reader, now=NOW)
    assert verified.status == 'verified' and reader is not transaction and reader.observed
    vr = runtime_store_path(root, 'postgis-promotion-verifications')
    vf = persist_postgis_promotion_verification(verified, verification_root=vr)
    rollback_plan = plan_postgis_rollback(plan_file=args['plan_file'], plan_root=args['plan_root'],
        execution_file=Path(stored.execution_file), execution_root=er,
        verification_file=vf, verification_root=vr, now=NOW)
    pr = runtime_store_path(root, 'postgis-rollback-plans')
    pf = Path(persist_postgis_rollback_plan(rollback_plan, rollback_plan_root=pr).rollback_plan_file)
    ar = runtime_store_path(root, 'postgis-rollback-approvals')
    authority = create_postgis_rollback_approval(rollback_plan_file=pf, rollback_plan_root=pr,
        decision='approved', approver='fixture', reason='Separately restore temporary relations', now=NOW, expires_at=NOW+timedelta(hours=1))
    af = Path(persist_postgis_rollback_approval(authority, approval_root=ar).approval_file)
    rollback_args = dict(rollback_plan_file=pf, rollback_plan_root=pr, approval_file=af, approval_root=ar,
        settings=args['settings'], confirm_rollback_plan_sha256=postgis_rollback_plan_sha256(rollback_plan),
        confirm_approval_sha256=postgis_rollback_approval_sha256(authority), now=NOW+timedelta(minutes=2))
    for path, value in ((Path(stored.execution_file), executed), (vf, verified), (pf, rollback_plan), (af, authority)):
        assert_legacy_bytes(path, value)
    return db, args, rollback_args


def round_trip(root, *, relocated=False):
    db, args, rollback_args = prepare_rollback(root, relocated=relocated)
    original = Database().tables
    tx = Transaction(db, args['settings'])
    restored = execute_postgis_rollback(**rollback_args, transaction=tx)
    rr = runtime_store_path(root, 'postgis-rollback-executions')
    rf = Path(persist_postgis_rollback_execution(restored, execution_root=rr).execution_file)
    checked = verify_postgis_rollback(execution_file=rf, execution_root=rr, rollback_plan_file=rollback_args['rollback_plan_file'],
        rollback_plan_root=rollback_args['rollback_plan_root'], approval_file=rollback_args['approval_file'], approval_root=rollback_args['approval_root'], settings=args['settings'],
        reader=db.reader(), now=NOW+timedelta(minutes=3))
    assert checked.status == 'verified' and db.tables == original
    out = persist_postgis_rollback_verification(checked, verification_root=runtime_store_path(root, 'postgis-rollback-verifications'))
    for path, value in ((rf, restored), (out, checked)):
        assert_legacy_bytes(path, value)
    assert sorted(r['status'] for r in receipts(root)) == ['committed', 'committed']
    journals = runtime_store_path(root, 'workflow-state', 'postgis-attempts').glob('*.events.jsonl')
    for path in journals:
        events = [json.loads(line) for line in path.read_text().splitlines()]
        assert [event['sequence'] for event in events] == list(range(1, 7))
        assert [event['status'] for event in events] == ['claimed', 'mutating', 'mutating', 'validating', 'commit_requested', 'committed']
    return db, args, rollback_args


@pytest.mark.parametrize('relocated', [False, True])
def test_complete_independent_lifecycle_and_legacy_evidence_bytes(tmp_path, relocated):
    round_trip(tmp_path / 'project', relocated=relocated)


@pytest.mark.parametrize('kind', ['promotion', 'rollback'])
def test_used_authority_stays_consumed_after_restoration_and_offline_copy(tmp_path, kind):
    root = tmp_path / 'project'
    db, args, rollback_args = round_trip(root)
    migrate(root, tmp_path / 'new-state', apply=True, offline=True, archive_legacy=True)
    # Public file arguments are explicit: point them at their copied packages.
    kwargs = args if kind == 'promotion' else rollback_args
    for key in list(kwargs):
        value = kwargs[key]
        if isinstance(value, Path): kwargs[key] = tmp_path / 'new-state' / value.relative_to(root)
    fn = execute_postgis_promotion if kind == 'promotion' else execute_postgis_rollback
    error = PostGISPromotionExecutionError if kind == 'promotion' else PostGISRollbackExecutionError
    transaction = Transaction(db, args['settings'])
    with pytest.raises(error, match='already has an attempt'): fn(**kwargs, transaction=transaction)
    assert transaction.locked == [] and transaction.renames == []


@pytest.mark.parametrize('kind', ['promotion', 'rollback'])
@pytest.mark.parametrize('failure,status', [('second_rename','rolled_back'), ('validation','rolled_back'),
    ('commit_before','commit_unknown'), ('commit_after','commit_unknown')])
def test_failure_receipts_never_infer_commit_outcome_or_repeat_authority(tmp_path, failure, status, kind):
    root = tmp_path / 'project'
    if kind == 'promotion': db, _, _, kwargs = prepare(root)
    else: db, _, kwargs = prepare_rollback(root)
    fn = execute_postgis_promotion if kind == 'promotion' else execute_postgis_rollback
    error = PostGISPromotionExecutionError if kind == 'promotion' else PostGISRollbackExecutionError
    before = deepcopy(db.tables)
    transaction = Transaction(db, kwargs['settings'], fail=failure)
    with pytest.raises(error) as raised:
        fn(**kwargs, transaction=transaction)
    assert 'fixture-private' not in str(raised.value)
    assert transaction.closed and next(r for r in receipts(root) if r['kind'] == kind)['status'] == status
    if failure != 'commit_after': assert db.tables == before
    else: assert db.tables != before  # Server committed, acknowledgement was lost.
    with pytest.raises(error, match='already has an attempt'):
        fn(**kwargs, transaction=Transaction(db, kwargs['settings']))


def test_cleanup_failure_after_confirmed_commit_is_recorded_without_false_rollback(tmp_path):
    root = tmp_path / 'project'; db, _, _, kwargs = prepare(root)
    result = execute_postgis_promotion(**kwargs, transaction=Transaction(db, kwargs['settings'], fail='close'))
    assert result.transaction_committed and receipts(root)[0]['status'] == 'committed_close_unconfirmed'


def test_rollback_failure_is_unconfirmed_and_never_claimed_as_reverted(tmp_path):
    root = tmp_path / 'project'; db, _, _, kwargs = prepare(root)
    tx = Transaction(db, kwargs['settings'], fail='rollback')
    def failed_rename(*_): raise RuntimeError('fixture-private')
    tx.rename = failed_rename
    with pytest.raises(PostGISPromotionExecutionError, match='rollback_unconfirmed'):
        execute_postgis_promotion(**kwargs, transaction=tx)
    assert tx.closed and receipts(root)[0]['status'] == 'rollback_unconfirmed'


def test_independent_verifier_detects_post_commit_change(tmp_path):
    root = tmp_path / 'project'; db, _, _, kwargs = prepare(root)
    execution = execute_postgis_promotion(**kwargs, transaction=Transaction(db, kwargs['settings']))
    er = root / 'executions'; ef = Path(persist_postgis_promotion_execution(execution, execution_root=er).execution_file)
    db.tables[(SCHEMA, 'reference_layer')].append(999)
    observed = verify_postgis_promotion(execution_file=ef, execution_root=er, plan_file=kwargs['plan_file'],
        plan_root=kwargs['plan_root'], settings=kwargs['settings'], reader=db.reader())
    assert observed.status == 'failed' and observed.findings == ['promoted_relation_mismatch']


@pytest.mark.parametrize('kind', ['promotion', 'rollback'])
@pytest.mark.parametrize('damage', ['digest', 'expiry', 'future', 'denied', 'binding'])
def test_invalid_authority_never_claims_an_attempt_or_opens_transaction(tmp_path, kind, damage):
    root = tmp_path / 'project'
    if kind == 'promotion':
        db, _, _, kwargs = prepare(root)
        from geoagent_harness.data.databases.postgis.promotion.approval.storage import load_postgis_promotion_approval as load, persist_postgis_promotion_approval as persist, postgis_promotion_approval_sha256 as digest
        fn, error, bound_field = execute_postgis_promotion, PostGISPromotionExecutionError, 'plan_sha256'
    else:
        db, _, kwargs = prepare_rollback(root)
        from geoagent_harness.data.databases.postgis.rollback.approval.storage import load_postgis_rollback_approval as load, persist_postgis_rollback_approval as persist, postgis_rollback_approval_sha256 as digest
        fn, error, bound_field = execute_postgis_rollback, PostGISRollbackExecutionError, 'rollback_plan_sha256'
    before = receipts(root)
    if damage == 'digest': kwargs['confirm_approval_sha256'] = '0'*64
    elif damage == 'expiry': kwargs['now'] = NOW+timedelta(hours=2)
    else:
        authority = load(kwargs['approval_file'], approval_root=kwargs['approval_root'])
        changes = ({'created_at': NOW+timedelta(minutes=10)} if damage == 'future' else
                   {'decision': 'denied', 'approved_step_ids': []} if damage == 'denied' else
                   {bound_field: 'f'*64})
        authority = authority.model_copy(update=changes)
        kwargs['approval_file'] = Path(persist(authority, approval_root=kwargs['approval_root']).approval_file)
        kwargs['confirm_approval_sha256'] = digest(authority)
    tx = Transaction(db, kwargs['settings'])
    with pytest.raises(error): fn(**kwargs, transaction=tx)
    assert tx.locked == [] and tx.renames == [] and receipts(root) == before


def test_connection_failure_is_redacted_and_consumes_only_that_decision(tmp_path, monkeypatch):
    import geoagent_harness.data.databases.postgis.promotion.execution.service as service
    root = tmp_path / 'project'; _, _, _, kwargs = prepare(root)
    def unavailable(*_): raise RuntimeError('password=fixture-private')
    monkeypatch.setattr(service, 'PsycopgPromotionTransaction', unavailable)
    with pytest.raises(PostGISPromotionExecutionError, match='connection failed') as raised:
        execute_postgis_promotion(**kwargs)
    assert 'fixture-private' not in str(raised.value)
    assert receipts(root)[0]['status'] == 'connection_failed'


def test_unsafe_attempt_store_blocks_before_database_access(tmp_path):
    root = tmp_path / 'project'; db, _, _, kwargs = prepare(root)
    (root / 'workflow-state').mkdir()
    outside = tmp_path / 'outside'; outside.mkdir()
    (root / 'workflow-state/postgis-attempts').symlink_to(outside, target_is_directory=True)
    tx = Transaction(db, kwargs['settings'])
    with pytest.raises(PostGISPromotionExecutionError, match='recorded safely'):
        execute_postgis_promotion(**kwargs, transaction=tx)
    assert tx.locked == [] and list(outside.iterdir()) == []


def test_concurrent_calls_with_same_authority_dispatch_once(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    root = tmp_path / 'project'; db, _, _, kwargs = prepare(root)
    transactions = [Transaction(db, kwargs['settings']) for _ in range(2)]
    def submit(tx):
        try: return execute_postgis_promotion(**kwargs, transaction=tx)
        except PostGISPromotionExecutionError as error: return error
    with ThreadPoolExecutor(max_workers=2) as pool: outcomes = list(pool.map(submit, transactions))
    assert sum(isinstance(value, PostGISPromotionExecutionError) for value in outcomes) == 1
    assert sum(len(tx.renames) for tx in transactions) == 2
    assert len(receipts(root)) == 1 and receipts(root)[0]['status'] == 'committed'


def test_fixed_driver_uses_serializable_transaction_and_quoted_identifiers(tmp_path, monkeypatch):
    from geoagent_harness.data.databases.postgis import lifecycle
    from psycopg import IsolationLevel
    class Connection:
        def __init__(self): self.statements = []; self.closed = False
        def execute(self, query, params=None):
            self.statements.append((query.as_string() if hasattr(query, 'as_string') else query, params))
        def commit(self): self.committed = True
        def rollback(self): self.reverted = True
        def close(self): self.closed = True
    connection = Connection()
    monkeypatch.setattr(lifecycle.psycopg, 'connect', lambda **_: connection)
    monkeypatch.setattr(lifecycle, '_read_password', lambda _: 'fixture-only')
    settings = MCPSettings(project_root=tmp_path, input_root=tmp_path/'input', output_root=tmp_path/'output')
    driver = lifecycle.PsycopgRelationTransaction(settings)
    driver.lock([('agent_sandbox', 'reference_layer'), ('agent_sandbox', 'candidate_layer')])
    driver.rename(('agent_sandbox', 'reference_layer'), ('archive_schema', 'archived_layer'))
    driver.commit(); driver.close()
    assert connection.isolation_level == IsolationLevel.SERIALIZABLE
    assert connection.statements[0][1] == ('30000', '10000')
    assert connection.statements[1][0] == 'LOCK TABLE "agent_sandbox"."reference_layer", "agent_sandbox"."candidate_layer" IN ACCESS EXCLUSIVE MODE'
    assert connection.statements[2][0] == 'ALTER TABLE "agent_sandbox"."reference_layer" SET SCHEMA "archive_schema"'
    assert connection.statements[3][0] == 'ALTER TABLE "archive_schema"."reference_layer" RENAME TO "archived_layer"'
    assert connection.committed and connection.closed


def test_driver_constructor_failure_closes_opened_connection_and_redacts(tmp_path, monkeypatch):
    from geoagent_harness.data.databases.postgis import lifecycle
    class Broken:
        closed = False
        @property
        def isolation_level(self): return None
        @isolation_level.setter
        def isolation_level(self, _): raise RuntimeError('password=fixture-private')
        def close(self): self.closed = True
    connection = Broken()
    monkeypatch.setattr(lifecycle.psycopg, 'connect', lambda **_: connection)
    monkeypatch.setattr(lifecycle, '_read_password', lambda _: 'fixture-only')
    settings = MCPSettings(project_root=tmp_path, input_root=tmp_path/'input', output_root=tmp_path/'output')
    with pytest.raises(RuntimeError, match='connection failed') as raised:
        lifecycle.PsycopgRelationTransaction(settings)
    assert connection.closed and 'fixture-private' not in str(raised.value)


def test_package_and_returned_metadata_use_one_detached_snapshot(tmp_path, monkeypatch):
    from geoagent_harness.data.databases.postgis.artifact_storage import ArtifactStore
    from geoagent_harness.data.databases.postgis.promotion.approval.storage import load_postgis_promotion_approval
    root = tmp_path / 'project'; _, _, approval, _ = prepare(root)
    expected_id, expected_plan = approval.approval_id, approval.plan_id
    canonical = ArtifactStore.canonical
    def mutate_caller(self, value):
        content = canonical(self, value)
        approval.approval_id = 'postgis-promotion-approval-20260904t180000z-aaaaaaaa'
        approval.plan_id = 'different-plan'
        return content
    monkeypatch.setattr(ArtifactStore, 'canonical', mutate_caller)
    stored = persist_postgis_promotion_approval(approval, approval_root=root/'snapshot-approvals')
    assert stored.approval_id == expected_id and stored.plan_id == expected_plan
    restored = load_postgis_promotion_approval(Path(stored.approval_file), approval_root=root/'snapshot-approvals')
    assert restored.approval_id == expected_id and restored.plan_id == expected_plan
