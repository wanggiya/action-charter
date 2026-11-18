"""Evidence boundaries and real shared-reader integration; synthetic fixtures only."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from geoagent_harness.contracts.data_cards import DataCard
from geoagent_harness.data.discovery.cards import from_evidence, matches_source
from geoagent_harness.data.discovery.csv import inspect, probe


@pytest.fixture
def dataset(tmp_path):
    directory=tmp_path/'data/input';directory.mkdir(parents=True)
    (directory/'facts.csv').write_text('record_id,age,value,label\n001,[40-50),2,PRIVATE_ROW\n002,[50-60),4,\n002,[50-60),4,\n')
    return tmp_path


def test_complete_card_uses_all_rows_not_preview_and_excludes_examples(dataset):
    outcome=inspect(dataset,'facts.csv',preview_rows=1)
    card=from_evidence(outcome)
    assert card['source_rows']==card['profile_rows']==3 and len(outcome['preview'])==1
    assert card['source_sha256']==hashlib.sha256((dataset/'data/input/facts.csv').read_bytes()).hexdigest()
    fields={f['name']:f for f in card['fields']}
    assert fields['label']['missing_count']==2 and fields['record_id']['distinct_count']==2
    assert fields['age']['candidate_role']=='ordered_category' and fields['age']['mean'] is None
    assert fields['value']['mean']==pytest.approx(10/3)
    assert card['excess_duplicate_rows']==1 and card['missingness']=='empty_cells'
    assert 'PRIVATE_ROW' not in json.dumps(card) and 'preview' not in card
    assert card['freshness']=='recorded_read_not_current_file_check' and not card['execution_authority']


def test_probe_never_claims_full_statistics_or_digest(dataset):
    evidence=probe(dataset,'facts.csv')
    evidence['metadata']['missing_counts']={'label':0}
    card=from_evidence(evidence)
    assert card['scope']=='sample' and card['source_rows'] is None and card['source_sha256'] is None
    assert card['identity_basis']=='pending' and all(f['missing_count'] is None for f in card['fields'])


def test_changed_source_or_selection_cannot_match_recorded_identity(dataset):
    card=from_evidence(inspect(dataset,'facts.csv'))
    assert matches_source(card,path=card['source'],sha256=card['source_sha256'],selection=card['selection'])
    (dataset/'data/input/facts.csv').write_text('value\n99\n')
    digest=hashlib.sha256((dataset/'data/input/facts.csv').read_bytes()).hexdigest()
    assert not matches_source(card,path=card['source'],sha256=digest,selection=card['selection'])
    assert not matches_source(card,path=card['source'],sha256=None,selection=card['selection'])
    assert not matches_source(card,path=card['source'],sha256=card['source_sha256'],selection={'sheet':'Other'})


def test_mismatched_basic_profile_is_not_borrowed(dataset):
    result=inspect(dataset,'facts.csv');result['basic_profile']['source_sha256']='a'*64
    card=from_evidence(result)
    assert card['excess_duplicate_rows'] is None
    assert all(f['distinct_count'] is None and f['mean'] is None for f in card['fields'])


def test_supplied_card_is_never_a_fallback_and_read_projection_is_pure(dataset):
    from geoagent_harness.data.discovery.cards import attach
    from geoagent_harness.task_actions.workflow_runs import _with_data_cards
    assert attach({'data_card':{'execution_authority':True},'source':'secret'})=={'source':'secret'}
    result=inspect(dataset,'facts.csv')
    record={'steps':[{'outcome':result,'step_id':'step_1'}]}
    original=copy.deepcopy(record)
    projected=_with_data_cards(record)
    assert record==original and projected['steps'][0]['outcome']['data_card']['source_rows']==3
    assert _with_data_cards(None) is None


@pytest.mark.parametrize('field,value',[('discovery',1),('table_source',['bad']),
    ('basic_profile','old-format'),('column_types',7),('missing_counts',['unknown'])])
def test_malformed_legacy_details_do_not_break_saved_evidence(dataset,field,value):
    from geoagent_harness.task_actions.workflow_runs import _with_data_cards
    result=inspect(dataset,'facts.csv');result[field]=value
    original=copy.deepcopy(result)
    projected=_with_data_cards({'steps':[{'step_id':'step_1','outcome':result}]})
    assert projected['steps'][0]['outcome']==original
    assert result==original


def test_wide_cards_are_bounded_with_explicit_omissions(dataset):
    result=inspect(dataset,'facts.csv')
    result.update(columns=['column_'+str(i)+'x'*180 for i in range(100)],column_count=100)
    card=from_evidence(result)
    assert card and card['field_count']==100
    assert len(card['fields'])+card['fields_omitted']==100 and card['fields_omitted']>=68
    assert len(json.dumps(card).encode())<8000


def test_wide_sample_card_accounts_for_serialized_unknown_field_defaults(dataset):
    names=['field_'+str(i) for i in range(100)]
    (dataset/'data/input/wide.csv').write_text(','.join(names)+'\n'+','.join(['1']*100)+'\n')
    card=from_evidence(probe(dataset,'wide.csv'))
    assert card is not None and card['scope']=='sample'
    assert len(card['fields'])+card['fields_omitted']==100
    assert len(json.dumps(card).encode())<8000


@pytest.mark.parametrize('change',[{'source':'data/input/../secret.csv'},{'execution_authority':True},
    {'profile_rows':4},{'source_sha256':None}])
def test_contract_rejects_unsafe_identity_authority_and_population(dataset,change):
    card=from_evidence(inspect(dataset,'facts.csv'));card.update(change)
    with pytest.raises(ValidationError):DataCard.model_validate(card)


def test_shared_cli_mcp_and_worker_inspection_results_expose_same_card(dataset):
    from geoagent_harness.data.tabular.service import inspect_csv
    from geoagent_harness.data.tabular.analytical_service import profile_table
    from geoagent_harness.task_actions.data_tools import discover_dataset
    from geoagent_harness.platform.settings import MCPSettings
    from geoagent_harness.workspaces.sandbox.inspection import bounded_read
    cli=inspect_csv('facts.csv',SimpleNamespace(project_root=dataset))
    worker=bounded_read(dataset,action='csv_discover',path='data/input/facts.csv')
    analytical=profile_table(dataset,'facts.csv')
    mcp=discover_dataset('facts.csv',settings=MCPSettings(project_root=dataset,input_root=dataset/'data/input',output_root=dataset/'data/output'))
    assert cli['data_card']==worker['data_card']==analytical['data_card']==mcp['data_card']
    assert not (dataset/'data/output').exists()


def test_native_record_card_binds_resolved_selection_and_null_semantics(dataset):
    from geoagent_harness.data.tabular.inspection import inspect_table
    (dataset/'data/input/records.json').write_text('[{"id":1,"label":null},{"id":2,"label":""}]')
    result=inspect_table(dataset,'data/input/records.json')
    card=from_evidence(result)
    assert card['scope']=='complete_selected_table' and card['missingness']=='native_nulls'
    assert next(f for f in card['fields'] if f['name']=='label')['missing_count']==1
    selected=copy.deepcopy(result);selected['table_source']['selection']={'sheet':'Actual','header_row':2}
    assert from_evidence(selected)['selection']=={'sheet':'Actual','header_row':2}
    selected['table_source']['sha256']='b'*64
    assert from_evidence(selected) is None


def test_declared_tokens_are_bound_without_reclassifying_metadata_missingness(dataset):
    result=inspect(dataset,'facts.csv',analysis={'missing_values':{'label':['PRIVATE_ROW']}})
    card=from_evidence(result)
    assert card['selection']['missing_values']=={'label':['PRIVATE_ROW']}
    assert card['missingness']=='empty_cells'
    assert next(f for f in card['fields'] if f['name']=='label')['missing_count']==2


def test_spatial_metadata_card_does_not_claim_geometry_or_pixel_statistics():
    value={'operation':'inspect_raster','source':'data/input/image.tif','source_sha256':'a'*64,
        'source_manifest':{'image.tif':'b'*64},'width':400,'height':300,'band_count':2,
        'discovery':{'file_bytes':1000,'statistics_scope':'driver_metadata_only'}}
    card=from_evidence(value)
    assert card['scope']=='driver_metadata' and card['identity_basis']=='package_manifest_sha256'
    assert card['width']==400 and card['source_rows'] is None and not card['fields']


def test_comprehensive_card_does_not_consume_original_artifact_budget(dataset,monkeypatch):
    from geoagent_harness.data.tabular.dataset_service import profile_dataset
    from geoagent_harness.platform.paths import runtime_store_path
    monkeypatch.setenv('ACTIONCHARTER_ANALYTICAL_RUNTIME','local')
    result=profile_dataset(dataset,'facts.csv')
    artifact=result['artifact']
    stored=json.loads(runtime_store_path(dataset,'workflow-state','analytical-artifacts',artifact['sha256']+'.json').read_text())['result']
    assert 'data_card' not in stored and result['data_card']==from_evidence(stored)
    assert result['data_card']['source_rows']==3


def test_planner_receives_same_turn_cards_without_reading_extra_sources(tmp_path):
    from shutil import copytree
    from tests.test_planner_conversation import Client
    from geoagent_harness.task_actions.conversation import TurnRequest,conversation_turn
    from geoagent_harness.task_actions.inspection_policy import planning_discovery
    root=Path(__file__).parents[1]
    for name in ('agents','context'):
        copytree(root/name,tmp_path/name)
    folder=tmp_path/'data/input';folder.mkdir(parents=True)
    (folder/'facts.csv').write_text('value\n2\n')
    evidence=probe(tmp_path,'facts.csv')
    client=Client({'message':'Which analysis goal matters?','plan':None})
    token=planning_discovery.set(evidence)
    try:
        reply=conversation_turn(TurnRequest(action='turn',conversation_id='b'*32,
            message='Inspect facts.csv and suggest a useful analysis.',allowed_skill_ids=['inspect_csv']),project_root=tmp_path,model_client=client)
    finally:planning_discovery.reset(token)
    payload=json.loads(client.requests[0].messages[0].content)
    assert payload['dataset_cards'][0]['scope']=='sample'
    assert payload['dataset_cards'][0]['source']=='data/input/facts.csv'
    assert not reply['execution_performed'] and not reply['approval_performed']
