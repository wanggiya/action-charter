"""R6a shared contexts and neutral contracts; no model, files or live services."""
from concurrent.futures import ThreadPoolExecutor
from contextvars import Context, copy_context
import hashlib
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from geoagent_harness.contracts.graph import ancestors, plan_dependencies, plan_topological_order
from geoagent_harness.contracts.planning import WorkflowPlan
from geoagent_harness.platform import execution_control as control


@pytest.mark.parametrize('legacy,owner', [
    ('recipes.control', 'platform.execution_control'),
    ('planner.topology', 'contracts.graph'),
    ('critic.schemas', 'contracts.critic'),
])
def test_compatibility_modules_are_exact_owner_aliases(legacy, owner):
    metadata = Path(__file__).resolve().parents[1] / 'tests/architecture'
    historical = json.loads((metadata / 'r6_module_owners.json').read_text())
    retired = json.loads((metadata / 'r11_compatibility.json').read_text())['retired']
    legacy = 'geoagent_harness.' + legacy
    owner = 'geoagent_harness.' + owner
    native = import_module(historical.get(owner, {}).get('owner', owner))
    if legacy in retired:
        with pytest.raises(ModuleNotFoundError):import_module(legacy)
    else:
        assert import_module(legacy) is native


def test_legacy_executor_types_share_neutral_class_identity():
    from geoagent_harness.agents.roles.executor import schemas
    from geoagent_harness.contracts import execution
    for name in ('WorkflowToolArguments', 'ExecutionEnvelope', 'WorkflowExecutionResult', 'ExecutorRunResult'):
        assert getattr(schemas, name) is getattr(execution, name)
    # The domain result retains its recipe/evidence validators and dependencies.
    assert schemas.ExecutorRecipeRunResult.model_fields['recipe'].annotation is schemas.RecipeRunResult
    assert schemas.ExecutorRecipeRunResult.model_fields['execution_record'].annotation is schemas.RecipeExecutionRecord


class Observer:
    def __init__(self):
        self.events = []
    def checkpoint(self):
        self.events.append('checkpoint')
    def progress(self, *args):
        self.events.append(args)


def test_legacy_and_native_callers_share_progress_and_cancellation():
    from geoagent_harness.platform import execution_control as legacy
    observer = Observer()
    token = legacy.observer.set(observer)
    result, validation = {'rows': 2}, {'passed': True}
    try:
        control.checkpoint()
        legacy.progress('step_1', 'inspect_csv', 'completed', result, validation)
        assert observer.events == ['checkpoint', ('step_1', 'inspect_csv', 'completed', result, validation)]
        class Cancel:
            def checkpoint(self):
                raise legacy.ExecutionCancelled('fixture cancellation')
        inner = control.observer.set(Cancel())
        try:
            with pytest.raises(control.ExecutionCancelled, match='fixture cancellation'):
                legacy.checkpoint()
        finally:
            control.observer.reset(inner)
        assert legacy.observer.get() is observer
    finally:
        legacy.observer.reset(token)
    assert control.observer.get() is None


def test_copied_worker_context_propagates_once_and_does_not_leak():
    observer = Observer()
    token = control.observer.set(observer)
    try:
        inherited = copy_context()
    finally:
        control.observer.reset(token)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(inherited.run, control.checkpoint).result(timeout=5)
        pool.submit(Context().run, control.checkpoint).result(timeout=5)
    control.checkpoint()
    assert observer.events == ['checkpoint']
    assert control.observer.get() is None


def test_failure_restores_the_outer_observer():
    outer, inner = Observer(), Observer()
    first = control.observer.set(outer)
    try:
        second = control.observer.set(inner)
        try:
            control.checkpoint()
            raise ValueError('fixture failure')
        except ValueError:
            pass
        finally:
            control.observer.reset(second)
        control.checkpoint()
        assert outer.events == inner.events == ['checkpoint']
    finally:
        control.observer.reset(first)
    assert control.observer.get() is None


def test_no_observer_does_not_dispatch_or_produce_a_result():
    assert control.observer.get() is None
    assert control.checkpoint() is None
    assert control.progress('step_1', 'inspect_csv', 'queued') is None


def plan(parents):
    return WorkflowPlan(summary='Fixture graph', steps=[{
        'step_id': f'step_{index}', 'skill': 'inspect_csv', 'purpose': 'Inspect',
        'arguments': {'path': 'data/input/orders.csv'}, 'depends_on': dependencies,
    } for index, dependencies in enumerate(parents, 1)])


def test_legacy_graph_fallback_preserves_canonical_serialization_and_digest():
    from geoagent_harness.core.policy.approvals.service import canonical_plan_json, plan_sha256
    value = plan([None, None, None])
    before, digest = canonical_plan_json(value), plan_sha256(value)
    assert plan_dependencies(value) == {'step_1': [], 'step_2': ['step_1'], 'step_3': ['step_2']}
    assert plan_topological_order(value) == ['step_1', 'step_2', 'step_3']
    assert ancestors('step_3', plan_dependencies(value)) == {'step_1', 'step_2'}
    assert canonical_plan_json(value) == before and plan_sha256(value) == digest
    assert 'depends_on' not in before


def test_explicit_graph_retains_stable_ready_order_and_copies_parent_lists():
    value = plan([['step_3'], [], []])
    assert plan_topological_order(value) == ['step_2', 'step_3', 'step_1']
    edges = plan_dependencies(value)
    assert ancestors('step_1', edges) == {'step_3'}
    edges['step_1'].append('step_2')
    assert value.steps[0].depends_on == ['step_3']


@pytest.mark.parametrize('parents,message', [
    ([['step_2', 'step_2'], []], 'unique'),
    ([['step_1']], 'itself'),
    ([['step_9']], 'unknown step'),
    ([['step_2'], ['step_1']], 'cycle'),
])
def test_graph_guards_reject_invalid_untrusted_dependencies(parents, message):
    value = SimpleNamespace(steps=[SimpleNamespace(step_id=f'step_{i}', depends_on=deps)
                                  for i, deps in enumerate(parents, 1)])
    with pytest.raises(ValueError, match=message):
        plan_topological_order(value)


def test_neutral_execution_envelope_keeps_canonical_payload():
    from geoagent_harness.contracts.execution import ExecutionEnvelope
    from tests.test_executor_schemas import valid_envelope
    payload = valid_envelope()
    value = ExecutionEnvelope.model_validate(payload)
    encoded = lambda data: json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
    assert value.model_dump(mode='json') == payload
    assert hashlib.sha256(encoded(value.model_dump(mode='json'))).hexdigest() == hashlib.sha256(encoded(payload)).hexdigest()


@pytest.mark.parametrize('field', ['execution_performed', 'database_modified', 'authoritative_status_changed'])
def test_neutral_critic_record_cannot_claim_authority(field):
    from geoagent_harness.contracts.critic import CriticResultRecord
    result = {
        'model': 'fixture', 'task_id': 'fixture-task', 'deterministic_status': 'validated_success',
        'evidence_references': [], 'evidence_gaps': [], 'workflow_warnings': [], 'human_corrections': [],
        'assessment': {'deterministic_status': 'validated_success', 'conclusion': 'supported',
                       'success_claimed': True, 'summary': 'Fixture observations only.'},
    }
    record = dict(task_id='fixture-task', deterministic_status='validated_success',
                  critic_result_sha256='a' * 64, critic_result=result, recorded_at='2026-11-06T00:00:00Z')
    assert getattr(CriticResultRecord.model_validate(record), field) is False
    with pytest.raises(ValueError):
        CriticResultRecord.model_validate({**record, field: True})


def test_neutral_primitives_import_without_roles_or_data_runtimes():
    code = '''import sys
from geoagent_harness.contracts import execution, critic, graph
from geoagent_harness.platform import execution_control
assert not any(n.startswith(('geoagent_harness.executor', 'geoagent_harness.critic',
    'geoagent_harness.planner', 'geoagent_harness.recipes', 'geoagent_harness.task_actions',
    'geoagent_harness.model', 'geoagent_harness.mcp_server', 'geopandas', 'pyogrio', 'rasterio'))
    for n in sys.modules)
'''
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
