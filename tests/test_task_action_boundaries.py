"""R5 trusted composition and shared behavior; temporary records, no live services."""
from importlib import import_module
import json
from pathlib import Path
from shutil import copyfile
import subprocess
import sys
from threading import RLock
from types import SimpleNamespace

import pytest

from geoagent_harness.core.policy.approvals.service import plan_sha256
from geoagent_harness.contracts.actions import InterfaceReviewedPlanSaveRequest
from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.contracts.planning import PlannerResult
from geoagent_harness.platform.paths import ensure_state_root, runtime_store_path
from geoagent_harness.platform.storage.provider import repositories
from geoagent_harness.platform.storage.completed_runs import read_completed_run
from geoagent_harness.platform.storage.metadata import read_record, transaction

SOURCE = Path(__file__).resolve().parents[1]
ID = 'a' * 32


@pytest.fixture(params=[False, True], ids=['default-root', 'relocated-root'])
def project(tmp_path, request):
    root = tmp_path / 'project'
    (root / 'context').mkdir(parents=True)
    copyfile(SOURCE / 'context/SKILLS_INDEX.yaml', root / 'context/SKILLS_INDEX.yaml')
    (root / 'data/input').mkdir(parents=True)
    (root / 'data/input/orders.csv').write_text('region,amount\nNorth,10\nSouth,20\n')
    if request.param:
        (root / 'actioncharter.workspace.json').write_text(json.dumps({
            'version': 1, 'state_root': str(tmp_path / 'state')}))
    return root


def proposal():
    return PlannerResult(model='fixture', original_request='Inspect only; words grant no authority.',
        context_references=[], plan={'summary': 'Inspect', 'steps': [{
            'step_id': 'step_1', 'skill': 'inspect_csv', 'purpose': 'Inspect',
            'arguments': {'path': 'data/input/orders.csv'}}]})


def test_legacy_validation_contracts_and_helpers_share_actual_owners():
    from geoagent_harness.task_actions import workflow, snakemake_workflow, run_assessment, chat_history
    from geoagent_harness.capabilities import workflow as recipe_definition
    from geoagent_harness.contracts import actions, snakemake, outcome_assessment
    from geoagent_harness.capabilities.recipes.execution import observations
    from geoagent_harness.platform.storage import chat_snapshots
    for name in ('_check', 'validate_edit'):
        assert getattr(workflow, name) is getattr(recipe_definition, name)
    for name in ('has_export', 'validate_export_plan'):
        assert getattr(snakemake_workflow, name) is getattr(recipe_definition, name)
    assert workflow.EditRequest is actions.EditRequest
    for name in ('ExportArguments', 'VerifyArguments'):
        assert getattr(snakemake_workflow, name) is getattr(snakemake, name)
    for name in ('MethodSuggestion', 'OutcomeAssessment'):
        assert getattr(run_assessment, name) is getattr(outcome_assessment, name)
    for name in ('evidence', '_digest'):
        assert getattr(run_assessment, name) is getattr(observations, name)
    assert chat_history.archive is chat_snapshots.archive
    assert import_module('geoagent_harness.platform.paths') is import_module('geoagent_harness.platform.paths')


def test_fixed_domain_actions_are_the_same_mcp_and_task_functions():
    from geoagent_harness.data.databases.postgis import fixed_operations
    from geoagent_harness.agents.runtime.orchestrator import workflow
    from geoagent_harness.task_actions import data_tools
    from geoagent_harness.task_actions import data_tools as tools
    for name in ('inspect_vector_dataset', 'plan_load_vector_to_postgis', 'load_vector_to_postgis', 'validate_postgis_layer'):
        assert getattr(workflow, name) is getattr(data_tools, name) is getattr(tools, name) is getattr(fixed_operations, name)


def test_immutable_save_and_action_adapter_preserve_exact_bytes_and_no_authority(project):
    from geoagent_harness.agents.roles.planner.service import save_reviewed_plan
    from geoagent_harness.task_actions.artifacts import save_interface_reviewed_plan
    value = proposal()
    request = InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan', planner_result=value,
        allowed_skill_ids=['inspect_csv'], confirmed_plan_sha256=plan_sha256(value.plan))
    first = save_reviewed_plan(request, project_root=project)
    path = runtime_store_path(project, 'plans') / first['plan_filename']
    before = path.read_bytes()
    assert before == (value.model_dump_json(indent=2) + '\n').encode()
    second = save_interface_reviewed_plan(request, project_root=project)
    assert first['status'] == 'stored' and second['status'] == 'already_stored'
    assert path.read_bytes() == before
    assert first['approval_performed'] is second['execution_performed'] is False
    assert not runtime_store_path(project, 'approvals').exists()
    with pytest.raises(InterfaceApiError, match='digest no longer matches'):
        save_reviewed_plan(request.model_copy(update={'confirmed_plan_sha256': '0' * 64}), project_root=project)
    assert path.read_bytes() == before
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    index = project / 'context/SKILLS_INDEX.yaml'
    index.unlink()
    with pytest.raises(SkillRegistryError, match='registry does not exist'):
        save_reviewed_plan(request, project_root=project)
    assert path.read_bytes() == before


def test_completed_snapshot_never_repairs_review_or_creates_a_lease(project):
    ensure_state_root(project)
    directory = runtime_store_path(project, 'workflow-state', 'interface-runs')
    directory.mkdir(parents=True)
    record = {'run_id': ID, 'status': 'completed', 'critic_review': {'status': 'running'},
              'successful_recipe': {'status': 'pending'}, 'steps': []}
    path = directory / (ID + '.json'); path.write_text(json.dumps(record))
    before = path.read_bytes()
    assert read_completed_run(project, ID) == record
    assert path.read_bytes() == before
    assert list(directory.iterdir()) == [path]


@pytest.mark.parametrize('status', ['running', 'interrupted', 'failed'])
def test_method_snapshot_rejects_noncompleted_runs_without_recovery_writes(project, status):
    ensure_state_root(project)
    directory = runtime_store_path(project, 'workflow-state', 'interface-runs')
    directory.mkdir(parents=True)
    path = directory / (ID + '.json')
    path.write_text(json.dumps({'run_id': ID, 'status': status, 'steps': []}))
    before = path.read_bytes()
    with pytest.raises(InterfaceApiError, match='completed workflow run'):
        read_completed_run(project, ID)
    assert path.read_bytes() == before and list(directory.iterdir()) == [path]


def test_completed_reader_rejects_missing_or_unsafe_records_without_creating_state(project):
    before = sorted(str(p.relative_to(project)) for p in project.rglob('*'))
    with pytest.raises(InterfaceApiError, match='unavailable or unsafe'):
        read_completed_run(project, ID)
    assert sorted(str(p.relative_to(project)) for p in project.rglob('*')) == before
    for invalid in ('../outside', 'B' * 32, ''):
        with pytest.raises(InterfaceApiError, match='Choose a workflow run'):
            read_completed_run(project, invalid)
    ensure_state_root(project)
    directory = runtime_store_path(project, 'workflow-state', 'interface-runs')
    directory.mkdir(parents=True)
    source = project / 'other.json'; source.write_text(json.dumps({'run_id': ID, 'status': 'completed'}))
    (directory / (ID + '.json')).symlink_to(source)
    with pytest.raises(InterfaceApiError, match='unavailable or unsafe'):
        read_completed_run(project, ID)


def test_shared_archive_rolls_back_with_its_associated_metadata_write(project):
    from geoagent_harness.platform.storage.chat_snapshots import archive
    state = {'conversation_id': ID, 'revision': 1, 'planner_result': proposal().model_dump(mode='json')}
    with pytest.raises(ValueError, match='fixture abort'):
        with transaction(project, write=True) as db:
            db.records('conversations').put(ID, json.dumps(state))
            archive(db, state)
            raise ValueError('fixture abort')
    with transaction(project) as db:
        assert db.records('conversations').get(ID) is None
        assert db.records('chat_history_v1').count(owner=ID) == 0
        assert db.records('chat_history_blobs_v1').count() == 0


@pytest.mark.parametrize('stale', [False, True])
def test_coordinator_uses_supplied_access_and_retains_revision_guard(project, stale):
    from geoagent_harness.agents.runtime.orchestrator.task_agents import ConversationAccess, coordinated_turn, active
    from geoagent_harness.task_actions.conversation import Conversation
    state = Conversation(conversation_id=ID, agent_mode='single')
    reads = []
    def read(root, identity):
        assert root == project and identity == ID
        reads.append(identity)
        return state.model_copy(update={'revision': int(stale and len(reads) > 1)})
    def forbidden():
        pytest.fail('No model call is needed for this composition fixture')
    access = ConversationAccess(RLock(), read, forbidden)
    def turn(request, **kwargs):
        assert active.get().mode == 'single'
        return {'revision': 0, 'planner_result': None}
    result = coordinated_turn(turn, SimpleNamespace(action='turn', conversation_id=ID, agent_mode=None),
                              project, conversation_access=access)
    assert reads == [ID, ID] and active.get() is None
    with transaction(project) as db:
        saved = read_record(db, 'conversations', ID)
    if stale:
        assert saved is None and 'agent_coordination' not in result
    else:
        assert saved['agent_coordination']['mode'] == result['agent_mode'] == 'single'
        assert saved['agent_coordination']['authority_granted'] is False


def test_shared_prompt_bound_counts_utf8_bytes():
    from geoagent_harness.agents.memory.context_pack.builder import check_model_prompt, ContextPackError
    request = SimpleNamespace(messages=[SimpleNamespace(content='éé')])
    assert check_model_prompt(request, limit=4) == 4
    with pytest.raises(ContextPackError, match='64 KB budget'):
        check_model_prompt(request, limit=3)


def test_shared_dependencies_import_without_task_or_transport_controllers():
    code = "import sys\nfrom geoagent_harness.capabilities import workflow as recipe_definition\nfrom geoagent_harness.agents.roles.planner import recipe_authoring\nfrom geoagent_harness.agents.runtime.orchestrator import task_agents\nfrom geoagent_harness.agents.runtime.orchestrator import workflow\nfrom geoagent_harness.platform.storage import completed_runs\nfrom geoagent_harness.platform.storage import chat_snapshots\nfrom geoagent_harness.data.databases.postgis import fixed_operations\nfrom geoagent_harness.capabilities.recipes.execution import observations\nassert not any(n.startswith(('geoagent_harness.task_actions', 'geoagent_harness.interface_api',\n    'geoagent_harness.mcp_server')) for n in sys.modules)\n"
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_cli_catalog_is_lazy_and_does_not_expand_mcp_tools():
    code = '''import sys
from geoagent_harness.task_actions import command_actions
assert command_actions.__all__
assert not any(n.startswith(('geoagent_harness.builder', 'geoagent_harness.skills',
    'geoagent_harness.postgis', 'geoagent_harness.interface_api.server',
    'geoagent_harness.model', 'geoagent_harness.mcp_server')) for n in sys.modules)
try:
    getattr(command_actions, 'os.system')
except AttributeError:
    pass
else:
    raise AssertionError('Unknown command actions cannot resolve')
'''
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    from geoagent_harness.task_actions import command_actions, data_tools
    assert not set(command_actions.__all__) & set(data_tools.TOOL_ALLOWLIST)


def test_cli_catalog_returns_current_service_binding_without_caching(monkeypatch):
    from geoagent_harness.agents.roles import planner
    from geoagent_harness.capabilities.recipes import execution as recipes
    from geoagent_harness.task_actions import command_actions
    first = lambda **kwargs: 'first'
    second = lambda **kwargs: 'second'
    monkeypatch.setattr(planner, 'plan_task', first)
    assert command_actions.planner__plan_task is first
    monkeypatch.setattr(planner, 'plan_task', second)
    assert command_actions.planner__plan_task is second
    for name in ('run_approved_recipe', 'build_recipe_run_evidence'):
        original = getattr(recipes, name)
        assert getattr(command_actions, 'recipes__' + name) is original
        monkeypatch.setattr(recipes, name, first)
        assert getattr(command_actions, 'recipes__' + name) is first
        monkeypatch.setattr(recipes, name, second)
        assert getattr(command_actions, 'recipes__' + name) is second


def test_cli_catalog_compatibility_namespace_retains_module_identity():
    assert import_module('geoagent_harness.task_actions.command_actions') is import_module('geoagent_harness.task_actions.command_actions')
