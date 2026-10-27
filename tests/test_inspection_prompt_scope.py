"""Read-only analytical requests retain real analysis but avoid writer schemas."""
from geoagent_harness.planner.prompt_scope import schema_scope
import json
import pytest
from tests.test_task_agents import project

REQUEST = '''Inspect data/input/test/diabetic_sample_5000.csv.
Return row count, column names, observed types, missing-value counts,
distinct encounter_id and patient_nbr counts, and descriptive statistics
for time_in_hospital. Treat encounter_id and patient_nbr as identifiers,
not numerical measurements. Preserve all rows. No writes.'''
AVAILABLE=['inspect_csv','select_csv_columns','aggregate_csv','export_csv',
           'inspect_vector','import_csv_to_postgres']

def test_analytical_inspection_focuses_only_schema_even_with_explicit_selection():
    for selected in (False,True):
        assert schema_scope(REQUEST,AVAILABLE,selected=selected)==['inspect_csv']
    assert len(AVAILABLE)==6  # This is descriptive scope, not an authority allowlist.

def test_analytical_inspection_does_not_hide_existing_workflow_or_new_actions():
    assert 'select_csv_columns' in schema_scope(REQUEST,AVAILABLE,['select_csv_columns'])
    assert 'export_csv' in schema_scope(REQUEST+' Export the results.',AVAILABLE)
    assert 'inspect_vector' in schema_scope(REQUEST+' Also inspect vector lines.geojson.',AVAILABLE)
    assert 'import_csv_to_postgres' in schema_scope(REQUEST+' Load it into PostgreSQL.',AVAILABLE)

def test_actual_model_request_keeps_analysis_and_timeout_is_not_retried(project):
    from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
    from geoagent_harness.model import ModelClientError
    requests=[]
    class TimeoutClient:
        def complete(self,request):
            requests.append(request)
            raise ModelClientError.timeout()
    with pytest.raises(ModelClientError):
        conversation_turn(TurnRequest(action='turn',conversation_id='f'*32,
            message=REQUEST.replace('data/input/test/diabetic_sample_5000.csv','data/input/sample_orders.csv')),
            project_root=project,model_client=TimeoutClient())
    assert len(requests)==1
    system=json.loads(requests[0].messages[0].content)
    assert set(system['operation_argument_schemas'])=={'inspect_csv'}
    assert 'analysis' in system['operation_argument_schemas']['inspect_csv']['properties']
    assert 'select_csv_columns' in system['deferred_operation_schema_ids']
    assert not (project/'approvals').exists()
