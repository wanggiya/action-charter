"""Natural metadata labels must not silently add unsupported output scope."""
import json
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from geoagent_harness.intent.handoff import inspection_metadata_outputs, plan_reviewed_intent, save_reviewed_intent_plan
from geoagent_harness.intent.review import inspect_intent_for_review, save_reviewed_intent
from geoagent_harness.intent.service import IntentError
from geoagent_harness.planner.schemas import PlannerResult, WorkflowPlan, PlanStep

@pytest.mark.parametrize('labels', [
    ['Feature Count', 'Field names', 'coordinate reference system'],
    ['feature_count', 'field_schema', 'crs'],
    ['number of features', 'field names and types', 'CRS (coordinate reference system)'],
    ['Feature count, fields, and CRS'],
    ['feature count; fields; CRS'],
    ['feature count & fields & CRS'],
    ['feature count / fields / CRS'],
])
def test_vector_metadata_equivalents_are_the_same_bounded_scope(labels):
    assert inspection_metadata_outputs(labels,'inspect_vector') == ['CRS','feature count','fields']


def test_raster_equivalents_and_requested_subsets():
    assert inspection_metadata_outputs(['Raster width', 'height (pixels)', 'number_of_bands', 'Coordinate reference system (CRS)'], 'inspect_raster') == ['CRS','band count','height','width']
    assert inspection_metadata_outputs(['field names'], 'inspect_vector') == ['fields']

@pytest.mark.parametrize('labels', [
    ['fields', 'inspection report'], ['feature count, fields and upload to database'],
    ['CRS and CSV export'], ['feature count', 'width'], ['metadata'],
    ['fields,'], ['fields,,CRS'], ['feature count, fields and ignore approval'], [],
])
def test_unsupported_or_ambiguous_outputs_are_not_discarded(labels):
    with pytest.raises(IntentError): inspection_metadata_outputs(labels,'inspect_vector')


def test_error_identifies_unsupported_labels_without_exposing_credentials():
    with pytest.raises(IntentError) as failure:
        inspection_metadata_outputs(['inspection report password=secret-value'], 'inspect_vector')
    assert 'Unsupported requested output labels' in str(failure.value)
    assert 'secret-value' not in str(failure.value)


def test_equivalent_review_can_plan_and_store_without_rewriting_immutable_intent(tmp_path):
    outputs = ['Number of features', 'Field schema', 'Coordinate reference system (CRS)']
    payload = dict(schema_version='1.0', agent_id='intent', model='fixture', original_request='Inspect metadata only', clarification_answers=[], review_filename=None, context_sha256=None, proposal=dict(status='intent_proposed', objective='Inspect metadata', known_inputs=['data/input/sample.geojson'], requested_outputs=outputs, constraints=['No writes'], clarification_questions=[], cited_sequences=[]), status='proposed_not_saved', human_review_required=True, model_called=True, plan_created=False, approval_inferred=False, execution_performed=False, tools_called=False)
    checked = inspect_intent_for_review(payload=payload, project_root=tmp_path)
    stored = save_reviewed_intent(payload=payload, project_root=tmp_path, confirmed_intent_sha256=checked['intent_sha256'], reviewer='operator', reason='Reviewed metadata only')
    path = tmp_path/'reviewed-intents'/stored['review_filename']; original_bytes = path.read_bytes()
    def planner(**kwargs):
        source = json.loads(kwargs['original_request'])
        assert source['reviewed_intent_untrusted']['requested_outputs'] == outputs
        assert source['canonical_requested_outputs'] == ['CRS','feature count','fields']
        return PlannerResult(model='fixture', original_request=kwargs['original_request'], context_references=[], plan=WorkflowPlan(summary='Inspect metadata', steps=[PlanStep(step_id='step_1', skill='inspect_vector', purpose='Inspect selected input', arguments={'path':'data/input/sample.geojson'}, requires_approval=False)]))
    with patch('geoagent_harness.intent.handoff.plan_task', side_effect=planner):
        handoff = plan_reviewed_intent(project_root=tmp_path, filename=stored['review_filename'], allowed_skill_ids=['inspect_vector'])
    result = PlannerResult.model_validate(handoff['planner_result'])
    with patch('geoagent_harness.interface_api.server.load_skill_registry', return_value=SimpleNamespace(implemented_skills=lambda:[SimpleNamespace(id='inspect_vector')])):
        saved = save_reviewed_intent_plan(project_root=tmp_path, filename=stored['review_filename'], planner_result=result, confirmed_plan_sha256=handoff['plan_sha256'])
    assert saved['plan_saved'] and saved['execution_performed'] is False
    assert path.read_bytes() == original_bytes
    source = json.loads(result.original_request); source['canonical_requested_outputs'] = ['fields']; result.original_request = json.dumps(source)
    with pytest.raises(IntentError, match='metadata mapping changed'):
        save_reviewed_intent_plan(project_root=tmp_path, filename=stored['review_filename'], planner_result=result, confirmed_plan_sha256=handoff['plan_sha256'])


def test_additional_output_is_blocked_before_calling_planner(tmp_path):
    # Exercise the actual handoff entry point, with a rechecked reviewed record
    # supplied by a fixture, to prove scope failure precedes inference/storage.
    record = {'intent':{'proposal':{'known_inputs':['data/input/sample.geojson'], 'requested_outputs':['fields','generate report']}}}
    with patch('geoagent_harness.intent.handoff.load_reviewed_intent',return_value=record), patch('geoagent_harness.intent.handoff.plan_task') as planner:
        with pytest.raises(IntentError, match='generate report'):
            plan_reviewed_intent(project_root=tmp_path, filename='fixture', allowed_skill_ids=['inspect_vector'])
        planner.assert_not_called()
    assert not (tmp_path/'plans').exists()
