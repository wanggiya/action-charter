"""Selected capabilities shape the prompt; correction never bypasses policy."""
import json
from pathlib import Path
import pytest
from geoagent_harness.agent_manifest import load_agent_manifest
from geoagent_harness.context_pack import build_context_pack
from geoagent_harness.model.schemas import ModelResult
from geoagent_harness.planner.agent import PlannerAgentError, run_planner_agent
from geoagent_harness.planner.prompt import build_planner_request

ROOT = Path(__file__).resolve().parents[1]

def setup():
    return (build_context_pack('Convert sample_points.geojson only.', ROOT, allowed_skill_ids=['convert_vector']),
            load_agent_manifest('planner', ROOT / 'agents'))

def proposal(skill='convert_vector'):
    return json.dumps({'summary':'Convert only', 'steps':[{'step_id':'step_1','skill':skill,
        'purpose':'Convert requested file','arguments':{'path':'data/input/sample_points.geojson',
        'target_path':'data/output/scope_test.gpkg'},'requires_approval':True,'validation_required':True}]})

class Responses:
    def __init__(self, contents): self.contents=contents; self.requests=[]
    def complete(self, request):
        self.requests.append(request)
        return ModelResult(model='fixture',content=self.contents[len(self.requests)-1],finish_reason='stop')

def test_conversion_prompt_excludes_postgis_workflow_and_has_arguments():
    context, manifest = setup()
    request = build_planner_request(context, manifest)
    system = json.loads(request.messages[0].content)
    assert system['available_skills'] == ['convert_vector']
    assert system['required_skill_arguments'] == {'convert_vector':['path','target_path']}
    assert system['required_json_schema']['$defs']['PlanStep']['properties']['skill']['enum'] == ['convert_vector']
    assert 'load_vector_to_postgis' not in request.messages[0].content
    assert 'generate_report' not in request.messages[0].content

def test_one_rejected_skill_can_be_corrected_and_revalidated():
    context, manifest = setup()
    client=Responses([proposal('load_vector_to_postgis'),proposal()])
    result=run_planner_agent(context_pack=context,manifest=manifest,model_client=client)
    assert result.plan.steps[0].skill == 'convert_vector'
    assert len(client.requests) == 2
    assert any('correction' in warning for warning in result.warnings)
    assert not result.plan.execution_performed

def test_repeated_disallowed_skill_is_blocked_after_two_calls():
    context, manifest = setup()
    client=Responses([proposal('load_vector_to_postgis')]*2)
    with pytest.raises(PlannerAgentError,match='after one correction'):
        run_planner_agent(context_pack=context,manifest=manifest,model_client=client)
    assert len(client.requests) == 2
