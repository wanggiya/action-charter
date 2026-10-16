"""Private temporary browser API. Only model completion is replaced; no live services."""
import argparse
import json
import os
from pathlib import Path
from shutil import copytree
from http.server import ThreadingHTTPServer
from geoagent_harness.interface_api import conversation, server, method_memory, method_helper
from geoagent_harness.model.schemas import ModelResult

parser=argparse.ArgumentParser()
parser.add_argument('--root',required=True)
parser.add_argument('--planning-task-fixture',action='store_true')
parser.add_argument('--recipe-runs-fixture',action='store_true')
args=parser.parse_args()
root=Path(args.root).resolve()
repo=Path(__file__).resolve().parents[1]
for directory in ['context','agents']:
    copytree(repo/directory,root/directory,dirs_exist_ok=True)
(root/'data/input').mkdir(parents=True,exist_ok=True)
for name in ['sample_orders.csv','sample_regions.csv','sample_points.geojson']:
    (root/'data/input'/name).write_bytes((repo/'data/input'/name).read_bytes())
(root/'data/output').mkdir(exist_ok=True)
plan=json.loads((repo/'examples/checkpoint24/regional_csv_plan.json').read_text())
class FixtureModel:
    def complete(self,request):
        role=json.loads(request.messages[0].content).get('agent',{}).get('id')
        with (root/'model-calls.jsonl').open('a') as handle:
            handle.write(json.dumps({'role':role or json.loads(request.messages[0].content).get('agent_id')})+'\n')
        if role=='critic' and json.loads(request.messages[0].content).get('required_json_schema',{}).get('title')=='OutcomeAssessment':
            source=json.loads(request.messages[1].content)
            return ModelResult(model='temporary Critic fixture',content=json.dumps({'deterministic_status':source['deterministic_status'],
                'conclusion':'supported' if source['deterministic_status']=='completed' else 'needs_attention',
                'summary':'Recorded operations completed and their reported validation is available.' if source['deterministic_status']=='completed' else 'The run stopped; inspect completed steps and partial outputs before recovery.',
                'findings':[],'limitations':['Fixture observations do not prove suitability for other inputs.'],'reusable_method':None}))
        if args.recipe_runs_fixture and role in {'planner','critic'}:
            if role=='planner':
                from geoagent_harness.recipe_catalog.composition import catalog
                value=catalog(root)['recipe_clean_csv'].model_dump(mode='json')
                value['id']='recipe_browser_clean'
                value['name']='Browser verified cleaner'
            else:
                value={'conclusion':'supported','findings':[],'limitations':['Synthetic fixtures cover a small scope only.']}
            return ModelResult(model='temporary recipe role fixture',content=json.dumps(value))
        if args.recipe_runs_fixture:
            payload=json.loads(request.messages[1].content)
            latest=payload.get('latest_message','').casefold()
            if 'reusable' in latest:
                return ModelResult(model='temporary Planner fixture',content=json.dumps({'message':'Prepare a reusable recipe.','workflow_action':'prepare_recipe'}))
            if 'group' in latest and payload.get('current_plan'):
                proposed=payload['current_plan']
                previous=proposed['steps'][-1]['step_id']
                proposed['steps'].append({'step_id':f"step_{len(proposed['steps'])+1}",'skill':'aggregate_csv','purpose':'Sum amount by region','arguments':{'source_step':previous,'by':['region'],'aggregations':[{'column':'amount','function':'sum','output_column':'total'}]},'depends_on':[previous],'requires_approval':True,'validation_required':True})
                return ModelResult(model='temporary Planner fixture',content=json.dumps({'message':'Added aggregation.','plan':proposed}))
            if 'clean' in latest:
                from geoagent_harness.recipe_catalog.composition import catalog,recipe_digest
                recipe=catalog(root)['recipe_clean_csv']
                return ModelResult(model='temporary Planner fixture',content=json.dumps({'message':'Prepared CSV cleaning.','recipe_uses':[{'recipe_id':recipe.id,'recipe_sha256':recipe_digest(recipe),'alias':'clean','parameters':{'source':'sample_orders.csv','columns':['region','amount'],'fill_values':{'region':'Unknown'}}}]}))
        if json.loads(request.messages[0].content).get('agent_id')=='method_memory':
            source=json.loads(request.messages[1].content)
            with (root/'helper-model-calls.jsonl').open('a') as handle:
                handle.write(json.dumps({'agent':'method_memory'})+'\n')
            if (root/'fail-helper-once').exists():
                (root/'fail-helper-once').unlink()
                from geoagent_harness.model import ModelClientError
                raise ModelClientError.timeout()
            skill=(source.get('workflow_structure') or [{'skill':'inspect_csv'}])[0]['skill']
            return ModelResult(model='temporary method fixture',content=json.dumps({
                'title':'Inspect selected data','purpose':'Inspect structure before transforming it.',
                'inputs':['An operator-selected dataset'],'prerequisites':['A supported format'],
                'operations':[{'skill':skill,'guidance':'Inspect counts and schema.'}],
                'checks':['Compare expected metadata.'],'limitations':['Proposed method only; no execution evidence.']}))
        if args.planning_task_fixture:
            latest=json.loads(request.messages[1].content)['latest_message']
            if 'Vector task inspection' in latest:
                proposed={'summary':'Vector task fixture','steps':[{'step_id':'step_1','skill':'inspect_vector','purpose':'Inspect vector','arguments':{'path':'data/input/sample_points.geojson'},'requires_approval':False,'validation_required':False}]}
            elif 'CSV task inspection' in latest:
                proposed={'summary':'CSV task fixture','steps':[
                    {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect CSV','arguments':{'path':'data/input/sample_orders.csv'},'requires_approval':False,'validation_required':False},
                    {'step_id':'step_2','skill':'select_csv_columns','purpose':'Select identifiers','arguments':{'path':'data/input/sample_orders.csv','columns':['order_id','region'],'target_path':'data/output/task_identity.csv'},'depends_on':['step_1'],'requires_approval':True,'validation_required':True}]}
            else:
                proposed=None
            return ModelResult(model='temporary task fixture',content=json.dumps({'message':'Task-scoped proposal; nothing authorized or executed.','plan':proposed}))
        if 'ext_order_identity' in request.messages[1].content:
            from geoagent_harness.operations.packages import installed_packages,package_sha
            package=installed_packages(root)['ext_order_identity']
            adapted={'summary':'Installed adapter browser fixture','steps':[
                {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect CSV','arguments':{'path':'data/input/sample_orders.csv'},'requires_approval':False,'validation_required':False},
                {'step_id':'step_2','skill':'ext_order_identity','purpose':'Extract fixed order identifiers','arguments':{'path':'data/input/sample_orders.csv','target_path':'data/output/interface_identity.csv','package_sha256':package_sha(package)},'requires_approval':True,'validation_required':True},
                {'step_id':'step_3','skill':'export_csv','purpose':'Export validated adapter result','arguments':{'source_step':'step_2','target_path':'data/output/interface_identity_final.csv'},'requires_approval':True,'validation_required':True}]}
            return ModelResult(model='temporary deterministic browser fixture',content=json.dumps({'message':'Review the installed adapter; nothing authorized or executed.','plan':adapted}))
        return ModelResult(model='temporary deterministic browser fixture',content=json.dumps({'message':'Review regional totals; no operation has run.', 'plan':plan}))
conversation.SharedModelClient=lambda settings:FixtureModel()
method_memory.SharedModelClient=lambda settings:FixtureModel()
method_helper.SharedModelClient=lambda settings:FixtureModel()
from geoagent_harness.interface_api import run_assessment
run_assessment.SharedModelClient=lambda settings:FixtureModel()
if args.recipe_runs_fixture:
    from geoagent_harness.planner import recipe_authoring
    from geoagent_harness.recipes import runner
    recipe_authoring.SharedModelClient=lambda settings:FixtureModel()
    original_verify=runner.validate_tabular_output
    def bounded_fixture_verify(*arguments,**keywords):
        import time
        if (root/'hold-validation').exists():
            (root/'validation-entered').write_text('fixture only')
            deadline=time.monotonic()+20
            while (root/'hold-validation').exists():
                if time.monotonic()>deadline:raise ValueError('Fixture validation gate timed out')
                time.sleep(.02)
        return original_verify(*arguments,**keywords)
    runner.validate_tabular_output=bounded_fixture_verify
os.chdir(root)
http=ThreadingHTTPServer(('127.0.0.1',0),server._handler(root))
print(json.dumps({'port':http.server_port,'root':str(root)}),flush=True)
http.serve_forever()
