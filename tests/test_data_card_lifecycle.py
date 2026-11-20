"""P2-D2: synthetic sources, real bounded readers, no model/service/data writes."""
import json
import os
from pathlib import Path
import shutil

import pytest
from typer.testing import CliRunner
from geoagent_harness.contracts.errors import InterfaceApiError

from geoagent_harness.data.discovery.context import prepare, selection_for, reader_contract
from geoagent_harness.data.discovery.source import fingerprint
from geoagent_harness.platform.storage import data_cards as cache
from geoagent_harness.platform.storage.metadata import transaction
from geoagent_harness.workspaces.sandbox import inspection

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    (tmp_path / 'data/input').mkdir(parents=True)
    (tmp_path / 'data/input/facts.csv').write_text('id,group,value\n001,A,2\n002,B,4\n003,A,6\n')
    return tmp_path


def test_reuse_checks_full_content_without_repeating_inspection(project, monkeypatch):
    first = prepare(project, 'facts.csv', allow_read=True)
    assert first['status'] == 'prepared' and first['card']['source_rows'] == 3
    assert first['card']['profile_rows'] == 3 and not first['execution_authority']
    actual, actions = inspection.bounded_read, []
    def checked(*args, **kwargs):
        actions.append(kwargs['action'])
        assert kwargs['action'] == 'source_fingerprint'
        return actual(*args, **kwargs)
    monkeypatch.setattr(inspection, 'bounded_read', checked)
    second = prepare(project, 'facts.csv', allow_read=True)
    assert second['status'] == 'verified_reused' and not second['reader_performed']
    assert second['source_checked'] and second['checked_at'] and actions == ['source_fingerprint']
    assert second['card'] == first['card']


def test_same_size_and_restored_mtime_cannot_hide_changed_values(project):
    first = prepare(project, 'facts.csv', allow_read=True)
    path = project / 'data/input/facts.csv'
    old = path.stat()
    path.write_bytes(path.read_bytes().replace(b'A,2', b'A,8'))
    os.utime(path, ns=(old.st_atime_ns, old.st_mtime_ns))
    assert path.stat().st_size == old.st_size and path.stat().st_mtime_ns == old.st_mtime_ns
    second = prepare(project, 'facts.csv', allow_read=True)
    assert second['status'] == 'prepared'
    assert second['card']['source_sha256'] != first['card']['source_sha256']
    assert next(f for f in second['card']['fields'] if f['name'] == 'value')['mean'] == 6


def test_policy_off_never_reads_sources_or_creates_cache(project, monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('No source read permitted')
    monkeypatch.setattr(inspection, 'bounded_read', denied)
    result = prepare(project, 'facts.csv')
    assert result['status'] == 'read_not_permitted' and result['card'] is None
    assert not result['source_checked'] and not (project / 'planner-workspace').exists()


def test_off_uses_historical_label_even_after_source_changes(project, monkeypatch):
    first = prepare(project, 'facts.csv', allow_read=True)
    (project / 'data/input/facts.csv').write_text('different\n9\n')
    monkeypatch.setattr(inspection, 'bounded_read', lambda *a, **k: pytest.fail('Unexpected read'))
    old = prepare(project, 'facts.csv')
    assert old['status'] == 'historical' and not old['source_checked']
    assert old['checked_at'] is None and old['card'] == first['card']


def test_preliminary_scope_stays_sample_despite_full_hash(project):
    result = prepare(project, 'facts.csv', allow_read=True, preliminary=True)
    card = result['card']
    assert result['source_checked'] and card['source_sha256']
    assert card['scope'] == 'sample' and card['source_rows'] is None
    assert all(f['mean'] is None and f['missing_count'] is None for f in card['fields'])
    assert prepare(project, 'facts.csv', allow_read=True, preliminary=True)['status'] == 'verified_reused'
    assert prepare(project, 'facts.csv', allow_read=True)['status'] == 'prepared'


@pytest.mark.parametrize('selection', [dict(source_options={'sheet':'Data'}),
                                     dict(filters=[{'column':'group','value':'A'}]),
                                     dict(missing_values={'value':['?']})])
def test_send_policy_does_not_expand_to_selected_or_analytical_reads(project, monkeypatch, selection):
    monkeypatch.setattr(inspection, 'bounded_read', lambda *a, **k: pytest.fail('Unexpected read'))
    result = prepare(project, 'facts.csv', allow_read=True, preliminary=True, **selection)
    assert result['status'] == 'review_required' and not result['source_checked']


def test_workbook_selection_cannot_reuse_other_sheet(project):
    from openpyxl import Workbook
    book = Workbook(); book.active.title = 'One'
    book.active.append(['value']); book.active.append([2])
    sheet = book.create_sheet('Two'); sheet.append(['value']); sheet.append([7]); sheet.append([9])
    book.save(project / 'data/input/book.xlsx')
    one = prepare(project, 'book.xlsx', allow_read=True, source_options={'sheet':'One'})
    assert one['card']['profile_rows'] == 1 and one['card']['selection']['sheet'] == 'One'
    assert prepare(project, 'book.xlsx', allow_read=True, source_options={'sheet':'One'})['status'] == 'verified_reused'
    two = prepare(project, 'book.xlsx', allow_read=True, source_options={'sheet':'Two'})
    assert two['status'] == 'prepared' and two['card']['profile_rows'] == 2
    assert two['card']['selection']['sheet'] == 'Two'
    with pytest.raises((ValueError, InterfaceApiError), match='Choose|source|discovery|Dataset'):
        prepare(project, 'book.xlsx', allow_read=True)


def test_json_collection_and_csv_filter_are_part_of_population(project):
    (project / 'data/input/wrapped.json').write_text('{"one":[{"v":2}],"two":[{"v":4},{"v":8}]}')
    for key, rows in [('one',1),('two',2)]:
        result = prepare(project, 'wrapped.json', allow_read=True, source_options={'records_key':key})
        assert result['status'] == 'prepared' and result['card']['profile_rows'] == rows
        assert result['card']['selection']['records_key'] == key
    a = prepare(project, 'facts.csv', allow_read=True, filters=[{'column':'group','value':'A'}])
    b = prepare(project, 'facts.csv', allow_read=True, filters=[{'column':'group','value':'B'}])
    assert a['card']['scope'] == b['card']['scope'] == 'filtered_rows'
    assert a['card']['profile_rows'] == 2 and b['card']['profile_rows'] == 1
    assert b['status'] == 'prepared' and b['requested_selection'] != a['requested_selection']


def test_missing_value_policy_and_reader_revision_invalidate_reuse(project, monkeypatch):
    (project / 'data/input/facts.csv').write_text('value\n2\n?\n')
    first = prepare(project, 'facts.csv', allow_read=True)
    selected = prepare(project, 'facts.csv', allow_read=True, missing_values={'value':['?']})
    assert selected['status'] == 'prepared' and selected['requested_selection'] != first['requested_selection']
    from geoagent_harness.data.discovery import context
    monkeypatch.setattr(context, 'READER_REVISION', 'fixture-new-reader-revision')
    assert prepare(project, 'facts.csv', allow_read=True)['status'] == 'prepared'


def test_chats_and_explicit_tool_scope_do_not_share_cache(project):
    one = prepare(project, 'facts.csv', owner='a'*32, allow_read=True)
    assert one['status'] == 'prepared'
    assert prepare(project, 'facts.csv', owner='b'*32)['card'] is None
    assert prepare(project, 'facts.csv')['card'] is None
    assert prepare(project, 'facts.csv', owner='b'*32, allow_read=True)['reader_performed']
    assert prepare(project, 'facts.csv', owner='a'*32, allow_read=True)['status'] == 'verified_reused'


def test_corrupt_cache_is_not_trusted_as_evidence(project):
    prepare(project, 'facts.csv', allow_read=True)
    selected = selection_for('data/input/facts.csv')
    contract = reader_contract('data/input/facts.csv')
    key = cache.cache_key('explicit_discovery', 'data/input/facts.csv', selected, contract)
    with transaction(project, write=True) as unit:
        unit.records('data_cards_v1').put(key, '{"owner":"other"}', owner='explicit_discovery')
    assert prepare(project, 'facts.csv')['card'] is None
    assert prepare(project, 'facts.csv', allow_read=True)['status'] == 'prepared'


@pytest.mark.parametrize('kind',['file_link','directory_link','outside','fifo'])
def test_fingerprint_refuses_unsafe_sources(project, kind, tmp_path):
    path = 'data/input/facts.csv'
    if kind == 'file_link':
        (project / 'data/input/link.csv').symlink_to(project / path)
        path = 'data/input/link.csv'
    elif kind == 'directory_link':
        (project / 'data/input/alias').symlink_to(project / 'data/input', target_is_directory=True)
        path = 'data/input/alias/facts.csv'
    elif kind == 'outside':
        path = '../facts.csv'
    else:
        os.mkfifo(project / 'data/input/fifo.csv')
        path = 'data/input/fifo.csv'
    with pytest.raises((ValueError,OSError)):
        fingerprint(project, path)


def test_fingerprint_detects_path_replacement_during_read(project, monkeypatch):
    from geoagent_harness.data.discovery import source
    actual = source.os.read
    path = project / 'data/input/facts.csv'
    replaced = False
    def replace(fd, size):
        nonlocal replaced
        chunk = actual(fd, size)
        if not replaced:
            replaced = True
            path.rename(path.with_suffix('.old'))
            path.write_text('id,group,value\n099,C,9\n')
        return chunk
    monkeypatch.setattr(source.os, 'read', replace)
    with pytest.raises(ValueError, match='changed'):
        fingerprint(project, 'facts.csv')


def test_spatial_package_reuse_binds_companion_file_contents(project):
    import geopandas as gpd
    from shapely.geometry import Point
    gpd.GeoDataFrame({'value':[1]},geometry=[Point(0,0)],crs='EPSG:4326').to_file(project/'data/input/points.shp')
    first = prepare(project, 'points.shp', allow_read=True, preliminary=True)
    assert first['card']['identity_basis'] == 'package_manifest_sha256'
    assert first['card']['scope'] == 'driver_metadata'
    assert prepare(project, 'points.shp', allow_read=True, preliminary=True)['status'] == 'verified_reused'
    projection = project/'data/input/points.prj'
    projection.write_text(projection.read_text()+' ')
    second = prepare(project, 'points.shp', allow_read=True, preliminary=True)
    assert second['status'] == 'prepared' and second['card']['source_sha256'] != first['card']['source_sha256']


def test_cli_and_mcp_use_same_explicit_context_namespace(project):
    from geoagent_harness.apps.cli.main import app
    from geoagent_harness.task_actions.data_tools import discover_dataset
    from geoagent_harness.platform.settings import MCPSettings
    result = CliRunner().invoke(app, ['discover-dataset','facts.csv','--project-root',str(project),'--card-context'])
    assert result.exit_code == 0, result.output
    cli = json.loads(result.stdout)
    mcp = discover_dataset('facts.csv', settings=MCPSettings(project_root=project,input_root=project/'data/input',output_root=project/'data/output'),card_context=True)
    assert cli['status'] == 'prepared' and mcp['status'] == 'verified_reused'
    assert cli['card'] == mcp['card'] and not (project / 'data/output').exists()


@pytest.fixture
def planning_project(project):
    for name in ('agents','context'):
        shutil.copytree(ROOT/name, project/name)
    return project


def submit(root, client, *, revision=0, enabled=True, identity='a'*32, message='Inspect facts.csv and suggest useful analysis.'):
    from geoagent_harness.task_actions.conversation import TurnRequest
    from geoagent_harness.task_actions.planner_submission import SubmissionRequest, submission_action
    import uuid
    return submission_action(SubmissionRequest(action='submit',submission_id=uuid.uuid4().hex,
        conversation_id=identity,inspect_on_send=enabled,turn=TurnRequest(action='turn',conversation_id=identity,
        expected_revision=revision,message=message,allowed_skill_ids=['inspect_csv'])),
        project_root=root,model_client=client,background=False)


def test_planner_submit_receipts_and_refresh_never_dispatch_or_recheck(planning_project, monkeypatch):
    from tests.test_planner_conversation import Client
    from geoagent_harness.task_actions.conversation import TurnRequest, conversation_turn
    from geoagent_harness.task_actions.planner_submission import SubmissionRequest, submission_action
    client = Client(*[{'message':'Which analytical goal matters?','plan':None} for _ in range(2)])
    first = submit(planning_project, client)
    use = first['conversation']['context_usage']['dataset_context'][0]
    assert use['status'] == 'prepared' and use['card']['scope'] == 'sample'
    assert first['discovery_performed'] and not first['execution_performed'] and not first['approval_performed']
    second = submit(planning_project, client, revision=first['conversation']['revision'])
    assert second['conversation']['context_usage']['dataset_context'][0]['status'] == 'verified_reused'
    system = json.loads(client.requests[-1].messages[0].content)
    assert system['dataset_context_checks'][0]['status'] == 'verified_reused'
    assert system['dataset_cards'][0]['source'] == 'data/input/facts.csv'
    assert '"001"' not in json.dumps(system['dataset_cards'])
    monkeypatch.setattr(inspection, 'bounded_read', lambda *a, **k: pytest.fail('Refresh read source'))
    restored = conversation_turn(TurnRequest(action='read',conversation_id='a'*32),project_root=planning_project)
    assert restored['context_usage']['dataset_context'] == second['conversation']['context_usage']['dataset_context']
    receipt = submission_action(SubmissionRequest(action='read',submission_id=second['submission']['submission_id'],conversation_id='a'*32),project_root=planning_project)
    assert receipt['conversation']['context_usage']['dataset_context'] == restored['context_usage']['dataset_context']
    assert receipt['run'] is None and not (planning_project/'approvals').exists()


def test_off_and_plain_conversation_do_not_read_sources(planning_project, monkeypatch):
    from tests.test_planner_conversation import Client
    from geoagent_harness.task_actions.conversation import TurnRequest, conversation_turn
    monkeypatch.setattr(inspection, 'bounded_read', lambda *a, **k: pytest.fail('Unexpected source read'))
    first = submit(planning_project, Client({'message':'Which goal matters?','plan':None}),enabled=False)
    assert first['conversation']['context_usage']['dataset_context'][0]['status'] == 'read_not_permitted'
    direct = conversation_turn(TurnRequest(action='turn',conversation_id='b'*32,message='Inspect facts.csv and suggest analysis.',allowed_skill_ids=['inspect_csv']),project_root=planning_project,model_client=Client({'message':'Which goal matters?','plan':None}))
    assert direct['context_usage']['dataset_context'][0]['status'] == 'read_not_permitted'


def test_no_fact_receipts_stay_in_interface_without_padding_model_prompt(planning_project):
    from tests.test_planner_conversation import Client
    client = Client({'message':'Which goal matters?','plan':None})
    reply = submit(planning_project, client, enabled=False)
    system = json.loads(client.requests[0].messages[0].content)
    assert 'dataset_context_status' not in system
    assert 'dataset_cards' not in system and 'dataset_context_checks' not in system
    assert reply['conversation']['context_usage']['dataset_context'][0]['finding']


@pytest.mark.parametrize('message',['Inspect absent.csv and suggest analysis.','Analyze this dataset.'])
def test_missing_or_ambiguous_inputs_ask_before_model_or_read(planning_project, monkeypatch, message):
    from tests.test_planner_conversation import Client
    client = Client({'message':'Should not run','plan':None})
    monkeypatch.setattr(inspection, 'bounded_read', lambda *a, **k: pytest.fail('Unexpected source read'))
    result = submit(planning_project, client, message=message)
    assert not client.requests and result['conversation']['context_usage']['model_request']['stage'] == 'inspection_clarification'
    assert result['run'] is None


def test_unsafe_input_is_a_policy_refusal_before_model_or_read(planning_project, monkeypatch):
    from tests.test_planner_conversation import Client
    from geoagent_harness.core.policy.plan import PlannerPolicyError
    client = Client({'message':'Must not be called','plan':None})
    monkeypatch.setattr(inspection, 'bounded_read', lambda *a, **k: pytest.fail('Unsafe source read'))
    with pytest.raises(PlannerPolicyError, match='Read refused'):
        submit(planning_project, client, message='Inspect ../outside.csv and suggest analysis.')
    assert not client.requests


def test_unsupported_suffix_does_not_select_a_supported_filename_prefix(planning_project, monkeypatch):
    from tests.test_planner_conversation import Client
    from geoagent_harness.data.discovery.input import input_references
    refs = input_references('Inspect facts.csv.gz and suggest analysis.', planning_project)
    assert refs['existing_supplied_paths'] == [] and refs['missing_supplied_paths'] == ['data/input/facts.csv.gz']
    client = Client({'message':'Must not be called','plan':None})
    monkeypatch.setattr(inspection, 'bounded_read', lambda *a, **k: pytest.fail('Wrong source was read'))
    value = submit(planning_project, client, message='Inspect facts.csv.gz and suggest analysis.')
    assert not client.requests and value['run'] is None


def test_natural_language_filter_change_does_not_certify_old_selection(planning_project, monkeypatch):
    from tests.test_planner_conversation import Client
    monkeypatch.setattr(inspection, 'bounded_read', lambda *a, **k: pytest.fail('Unexpected source read'))
    result = submit(planning_project, Client({'message':'Prepare the exact filter before profiling.','plan':None}),message='Inspect facts.csv where group is B and suggest analysis.')
    use = result['conversation']['context_usage']['dataset_context'][0]
    assert use['status'] == 'review_required' and use['card'] is None and not use['source_checked']


def test_output_and_excluded_files_are_not_guessed_as_input(project):
    from geoagent_harness.data.discovery.input import input_references
    value = input_references('Inspect facts.csv and export results to fresh.csv. Do not read absent.csv.', project)
    assert value['existing_supplied_paths'] == ['data/input/facts.csv']
    assert value['missing_supplied_paths'] == []


def test_full_hash_budget_is_enforced_before_reading_content(project):
    with pytest.raises(ValueError, match='bounded regular'):
        fingerprint(project, 'facts.csv', max_bytes=1)


def test_cache_uses_existing_external_workspace_and_survives_new_process(project, tmp_path):
    from geoagent_harness.platform.workspace_migration import migrate
    from geoagent_harness.data.discovery.service import discover_dataset
    import subprocess, sys
    state = tmp_path.parent / (tmp_path.name + '-external-state')
    migrate(project, state, apply=True, offline=True)
    first = discover_dataset(project, 'facts.csv', card_context=True)
    code = 'import json,sys;from pathlib import Path;from geoagent_harness.data.discovery.service import discover_dataset;print(json.dumps(discover_dataset(Path(sys.argv[1]),"facts.csv",card_context=True)))'
    result = subprocess.run([sys.executable,'-c',code,str(project)],capture_output=True,text=True,timeout=20,
                            env={**os.environ,'PYTHONPATH':str(ROOT/'src')})
    assert result.returncode == 0, result.stderr
    second = json.loads(result.stdout)
    assert second['status'] == 'verified_reused' and second['card'] == first['card']
    assert (state/'planner-workspace/tasks.sqlite3').exists()
    assert not (project/'planner-workspace').exists()


@pytest.mark.parametrize('count', [1,2])
def test_current_workflow_source_is_used_only_when_unique(planning_project, monkeypatch, count):
    from geoagent_harness.contracts.planning import PlannerResult
    from geoagent_harness.task_actions.conversation import TurnRequest, conversation_turn
    from geoagent_harness.task_actions.inspection_policy import planning_discovery
    from tests.test_planner_conversation import Client
    (planning_project/'data/input/other.csv').write_text('other\n1\n')
    base = PlannerResult(model='fixture',original_request='Prepare only',context_references=[],plan={
        'summary':'Inspect sources','steps':[{'step_id':f'step_{i+1}','skill':'inspect_csv','purpose':'Read metadata',
        'arguments':{'path':'data/input/'+path},'requires_approval':False,'validation_required':False,'depends_on':[]}
        for i,path in enumerate(['facts.csv','other.csv'][:count])]})
    client = Client({'message':'Which analytical goal matters?','plan':None})
    if count == 2:
        monkeypatch.setattr(inspection, 'bounded_read', lambda *a, **k: pytest.fail('Ambiguous source was read'))
    token = planning_discovery.set({'planning_read_permitted':True,'routing':'explicit_submit'})
    try:
        result = conversation_turn(TurnRequest(action='turn',conversation_id='a'*32,current_plan=base,
            message='Analyze this dataset and suggest a useful next step.',allowed_skill_ids=['inspect_csv']),project_root=planning_project,model_client=client)
    finally:
        planning_discovery.reset(token)
    if count == 1:
        assert result['context_usage']['dataset_context'][0]['card']['source'] == 'data/input/facts.csv'
        assert client.requests
    else:
        assert not client.requests and result['context_usage']['model_request']['stage'] == 'inspection_clarification'


def test_cache_eviction_does_not_remove_chat_history(project, monkeypatch):
    monkeypatch.setattr(cache, 'MAX_CARDS', 3)
    prepared = prepare(project, 'facts.csv', allow_read=True)
    with transaction(project, write=True) as unit:
        unit.records('conversations').ensure()
        unit.records('conversations').put('c'*32, '{"conversation_id":"'+'c'*32+'","messages":[]}')
    for number in range(4):
        cache.store(project, owner=f'{number:032x}', path=prepared['source'],
            selection=prepared['requested_selection'], contract=prepared['reader_contract'], card=prepared['card'])
    with transaction(project) as unit:
        assert unit.records('data_cards_v1').count() == 3
        assert unit.records('conversations').count() == 1
        assert unit.records('conversations').get('c'*32) is not None


@pytest.mark.parametrize('message',['Inspect the PostgreSQL table public.measurements.',
                                   'Summarize these recorded results.'])
def test_database_and_saved_result_questions_do_not_select_local_workflow_input(project, message):
    from types import SimpleNamespace
    from geoagent_harness.task_actions.inspection_policy import planning_sources
    base = SimpleNamespace(plan=SimpleNamespace(steps=[SimpleNamespace(arguments={'path':'data/input/facts.csv'})]))
    assert planning_sources(project, message, base) == ([], None)


def test_missing_current_source_asks_for_existing_file(project):
    from types import SimpleNamespace
    from geoagent_harness.task_actions.inspection_policy import planning_sources
    base = SimpleNamespace(plan=SimpleNamespace(steps=[SimpleNamespace(arguments={'path':'data/input/absent.csv'})]))
    paths, question = planning_sources(project, 'Analyze this dataset.', base)
    assert paths == [] and 'existing input' in question


def test_current_registry_approval_requirement_blocks_planning_reads(planning_project, monkeypatch):
    import yaml
    from tests.test_planner_conversation import Client
    path = planning_project/'context/SKILLS_INDEX.yaml'
    registry = yaml.safe_load(path.read_text())
    next(item for item in registry['skills'] if item['id']=='inspect_csv').update(
        access='artifact_write', approval_required=True, validation_required=True,
        verifier='geoagent_harness.data.tabular.service:validate_output')
    path.write_text(yaml.safe_dump(registry,sort_keys=False))
    monkeypatch.setattr(inspection, 'bounded_read', lambda *a, **k: pytest.fail('Registry review gate was bypassed'))
    reply = submit(planning_project, Client({'message':'Prepare a reviewed inspection first.','plan':None}))
    use = reply['conversation']['context_usage']['dataset_context'][0]
    assert use['status']=='review_required' and not use['source_checked']
