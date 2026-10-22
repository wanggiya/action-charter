"""Exercise the evaluation itself through real temporary services and outputs."""
import importlib.util
from pathlib import Path

SPEC=importlib.util.spec_from_file_location('paired_fixture_evaluation',Path(__file__).parents[1]/'scripts/checkpoint28_paired_evaluation.py')
evaluation=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(evaluation)


def test_paired_harness_identical_inputs_real_gates_and_no_false_benefit(tmp_path,monkeypatch):
    # evaluate config is process-local; pytest must restore it for later tests.
    import os
    for key in ('ENABLE_WRITE_TOOLS','ALLOW_OVERWRITE','MODEL_NAME','MODEL_BASE_URL','MODEL_TIMEOUT_SECONDS','MODEL_MAX_TOKENS','MODEL_REASONING_EFFORT','PLANNER_TURN_TIMEOUT_SECONDS'):
        monkeypatch.setenv(key,os.environ.get(key,''))
    report=evaluation.evaluate(output=tmp_path/'report.json')
    assert report['evaluation']=='deterministic_harness_self_test'
    assert len(report['attempts'])==12
    assert all(a['correct_output'] for a in report['attempts'])
    assert report['summary']['representative_threshold_met'] is False
    assert report['summary']['human_interventions']==0
    for case in evaluation.CASES:
        pair=[a for a in report['attempts'] if a['case']==case]
        assert pair[0]['input_sha256']==pair[1]['input_sha256']
        assert len(pair[0]['calls'])==len(pair[1]['calls'])==1
        off=next(a for a in pair if a['recommendations']=='OFF')
        on=next(a for a in pair if a['recommendations']=='ON')
        assert off['calls'][0]['recommendations_supplied'] is None
        assert on['calls'][0]['recommendations_supplied']['scope']=='this_chat'
        assert on['recommendation_receipt']['model_adoption']=='not_measured'
        if case in {'csv_inspection','vector_inspection'}:
            assert on['gates']['read_only_no_authorize'] and not on['scripted_authorization']
            assert on['recommendation_receipt']['items']==[]
        else:
            assert on['gates']=={'writes_off_blocked':True,'missing_authority_blocked':True}
            assert on['recommendation_receipt']['items']


def test_output_oracle_uses_transform_result_when_final_step_is_inspection(tmp_path):
    root=tmp_path
    evaluation.fixture_project(root)
    target=root/'data/output/filtered.csv'
    target.write_text('order_id,region,amount\n101,North,7\n102,South,12\n')
    record={'steps':[
        {'skill_id':'inspect_csv','outcome':{'row_count':4},'validation_outcome':None},
        {'skill_id':'filter_csv_rows','outcome':{'output':{'path':'data/output/filtered.csv'}},'validation_outcome':{'passed':True}},
        {'skill_id':'inspect_csv','outcome':{'row_count':4},'validation_outcome':None}]}
    evaluation.verify('filter',record,root)


import pytest


@pytest.mark.parametrize('automatic',[False,True])
def test_spatial_guide_binds_explicit_new_input_without_reusing_history(tmp_path,monkeypatch,automatic):
    import os,json
    from geoagent_harness.interface_api.conversation import TurnRequest, conversation_turn
    from geoagent_harness.model.schemas import ModelResult
    root=tmp_path;evaluation.fixture_project(root)
    for key in ('MODEL_NAME','ENABLE_WRITE_TOOLS'):monkeypatch.setenv(key,'fixture' if key=='MODEL_NAME' else 'false')
    initial=conversation_turn(TurnRequest(action='turn',conversation_id=evaluation.CHAT,message='Inspect seed_boundaries.geojson and extract attributes then group and sum by region.',allowed_skill_ids=['inspect_vector','vector_attributes_to_csv','aggregate_csv']),project_root=root,model_client=evaluation.FixtureModel(evaluation.fixed_plan('combined',training=True)))
    from tests.test_planner_conversation import Client
    client=Client({'message':'Wrong historical source','plan':evaluation.fixed_plan('combined',training=True)}, {'message':'Correct new source','plan':evaluation.fixed_plan('combined')})
    result=conversation_turn(TurnRequest(action='turn',conversation_id=evaluation.CHAT,expected_revision=initial['revision'],message=evaluation.CASES['combined'],allowed_skill_ids=[] if automatic else ['inspect_vector','vector_attributes_to_csv','aggregate_csv']),project_root=root,model_client=client)
    assert len(client.requests)==2
    system=json.loads(client.requests[0].messages[0].content)
    assert set(system['operation_argument_schemas'])=={'inspect_vector','vector_attributes_to_csv','aggregate_csv'}
    if automatic:assert 'inspect_csv' in system['available_skills']
    prefixes=client.requests[0].response_schema['$defs']['WorkflowPlan']['properties']['steps']['prefixItems']
    assert prefixes[0]['properties']['arguments']['properties']['path']['const']=='data/input/boundaries.geojson'
    assert prefixes[2]['properties']['arguments']['properties']['source_step']['const']=='step_2'
    assert [step['arguments'].get('path') for step in result['planner_result']['plan']['steps'][:2]]==['data/input/boundaries.geojson']*2
    assert not result['execution_performed']
