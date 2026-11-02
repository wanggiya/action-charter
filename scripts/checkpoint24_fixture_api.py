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
parser.add_argument('--acquisition-fixture',action='store_true')
parser.add_argument('--planning-task-fixture',action='store_true')
parser.add_argument('--analytical-fixture',action='store_true')
parser.add_argument('--statistics-fixture',action='store_true')
parser.add_argument('--csv-discovery-fixture',action='store_true')
parser.add_argument('--spatial-view-fixture',action='store_true')
parser.add_argument('--recipe-runs-fixture',action='store_true')
parser.add_argument('--calculation-fixture',action='store_true')
parser.add_argument('--write-policy-fixture',action='store_true')
parser.add_argument('--critic-graph-fixture',action='store_true')
parser.add_argument('--report-authorization-fixture',action='store_true')
parser.add_argument('--postgres-authorization-fixture',action='store_true')
parser.add_argument('--diabetes-decoding-fixture',action='store_true')
parser.add_argument('--agent-modes-fixture',action='store_true')
parser.add_argument('--visualization-fixture',action='store_true')
parser.add_argument('--calculation-deferral-fixture',action='store_true')
parser.add_argument('--calculation-invalid-json-fixture',action='store_true')
parser.add_argument('--calculation-omission-fixture',action='store_true')
parser.add_argument('--calculation-reuse-claim-fixture',action='store_true')
args=parser.parse_args()
root=Path(args.root).resolve()
repo=Path(__file__).resolve().parents[1]
for directory in ['context','agents']:
    copytree(repo/directory,root/directory,dirs_exist_ok=True)
(root/'data/input').mkdir(parents=True,exist_ok=True)
for name in ['sample_orders.csv','sample_regions.csv','sample_points.geojson','sample_dem.tif']:
    (root/'data/input'/name).write_bytes((repo/'data/input'/name).read_bytes())
if args.csv_discovery_fixture:
    with (root/'data/input/large_orders.csv').open('wb') as stream:
        stream.write(b'id,note\n')
        for _ in range(12000):stream.write(b'001,'+b'x'*1000+b'\n')
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.windows import Window
    with rasterio.open(root/'data/input/large_terrain.tif','w',driver='GTiff',width=2048,height=2048,count=1,dtype='float32',crs='EPSG:4326',transform=from_origin(10,20,.001,.001)) as target:
        for row in range(0,2048,64):target.write(np.zeros((1,64,2048),dtype='float32'),window=Window(0,row,2048,64))
    from geoagent_harness.interface_api.workflow_runs import _Observer
    original_progress=_Observer.progress
    def hold_discovery(self,step,skill,status,outcome=None,validation=None):
        original_progress(self,step,skill,status,outcome,validation)
        if isinstance(outcome,dict) and outcome.get('discovery',{}).get('phase')=='verifying' and (root/'hold-discovery').exists():
            import time
            (root/'discovery-entered').write_text('temporary test gate')
            deadline=time.monotonic()+20
            while (root/'hold-discovery').exists():
                self.checkpoint()
                if time.monotonic()>deadline:raise ValueError('Discovery fixture gate timed out')
                time.sleep(.02)
    _Observer.progress=hold_discovery
if args.spatial_view_fixture:
    import geopandas as gpd
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    gpd.GeoDataFrame({'name':['Projected point']},geometry=gpd.points_from_xy([111319.490793],[0]),crs='EPSG:3857').to_file(root/'data/input/layers.gpkg',layer='projected',driver='GPKG')
    from shapely.geometry import Polygon,LineString
    gpd.GeoDataFrame({'name':['Boundary <b>literal</b>']},geometry=[Polygon([(0,0),(4,0),(4,4),(0,4),(0,0)],holes=[[(1,1),(2,1),(2,2),(1,2),(1,1)]])],crs='EPSG:4326').to_file(root/'data/input/layers.gpkg',layer='boundaries',driver='GPKG')
    gpd.GeoDataFrame({'name':['Route']},geometry=[LineString([(0,0),(4,4)])],crs='EPSG:4326').to_file(root/'data/input/layers.gpkg',layer='routes',driver='GPKG')
    with rasterio.open(root/'data/input/image.tif','w',driver='GTiff',width=2,height=2,count=3,dtype='int16',nodata=-9999,crs='EPSG:4326',transform=from_origin(10,20,2,2)) as dataset:
        dataset.write(np.array([[[0,10],[20,-9999]],[[100,110],[120,-9999]],[[200,210],[220,-9999]]],dtype='int16'))
        dataset.units=('metres',None,None)
        dataset.descriptions=('Elevation <b>literal</b>',None,None)
        dataset.update_tags(owner='Synthetic spatial fixture')
(root/'data/output').mkdir(exist_ok=True)
if args.statistics_fixture:
    from openpyxl import Workbook
    rows=[{'record_id':'001','x':1.5,'region':'A'},{'record_id':'002','x':2.5,'region':'A'},{'record_id':'003','x':4.5,'region':'B'}]
    (root/'data/input/table_fixture.json').write_text(json.dumps(rows))
    (root/'data/input/table_fixture.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
    book=Workbook();sheet=book.active;sheet.title='Data';sheet.append(list(rows[0]))
    for row in rows:sheet.append(list(row.values()))
    book.save(root/'data/input/table_fixture.xlsx')
plan=json.loads((repo/'examples/checkpoint24/regional_csv_plan.json').read_text())
if args.calculation_omission_fixture:
    # A temporary historical record reproduces the real inspection-only bug.
    # Never read, migrate or rewrite the operator's actual conversation database.
    historical_request='Inspect sample_orders.csv. Create a new numeric column doubled equal to amount multiplied by 2. Preserve all original columns and propagate missing values. Save to a fresh CSV. Do not execute yet.'
    historical_plan={'summary':historical_request,'steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect metadata and preview','arguments':{'path':'data/input/sample_orders.csv'}}]}
    historical_result={'model':'historical fixture','original_request':historical_request,'context_references':[],'plan':historical_plan}
    historical_id='c'*32
    historical_state=conversation.Conversation(conversation_id=historical_id,revision=1,
        planner_result=historical_result,messages=[
            {'role':'user','content':historical_request},
            {'role':'assistant','content':'The calculation workflow is planned.','plan_skill_ids':['inspect_csv']},
        ])
    conversation._write(conversation._path(root,historical_id),historical_state)
class FixtureModel:
    def complete(self,request):
        system=json.loads(request.messages[0].content)
        if 'analysis_goal_capabilities' in system:
            guide=system['result_view_context']['results'][0]['field_guidance']
            numeric=next(f['name'] for f in guide['field_evidence'] if f['role'] in {'numerical','count'})
            grouping=next((f['name'] for f in guide['field_evidence'] if f['role'] in {'categorical','ordered_category'}),numeric)
            goals=[{'title':'Describe observed measurements','question':'How are observed measurements distributed?','method':'describe','fields':[numeric],'rationale':'A measurement candidate is present.','prerequisites':['Review units and the analysis unit.']},
                   {'title':'Assess prediction feasibility','question':'Could a future model predict a chosen category?','method':'classification_evaluation','fields':list(dict.fromkeys([numeric,grouping])),'target_candidate':grouping,'rationale':'A candidate category would require a defined outcome.','prerequisites':['Define labels before model training.']}]
            return ModelResult(model='temporary goal fixture',content=json.dumps({'message':'Two proposed analysis goals; no statistics were computed.','plan':None,'source_sha256':guide['source_sha256'],'analysis_goals':goals}))
        if any('report_scope_fixture' in m.content for m in request.messages):
            steps=[{'step_id':'step_1','skill':'inspect_csv','purpose':'Read-only data-quality report','arguments':{'path':'data/input/sample_orders.csv','analysis':{'numeric_columns':['amount']}}}]
            if not any('Remove the unrequested generate_report' in m.content for m in request.messages):
                steps.append({'step_id':'step_2','skill':'generate_report','purpose':'Extra report','arguments':{}})
            return ModelResult(model='temporary report fixture',content=json.dumps({'message':'Prepared inspection report.','plan':{'summary':'Inspect and report','steps':steps}}))
        if any('diagnostics_timeout_fixture' in m.content for m in request.messages):
            from geoagent_harness.model import ModelClientError
            raise ModelClientError.timeout()
        control=json.loads(request.messages[0].content).get('task_coordinator')
        if args.agent_modes_fixture and control and control['phase']!='planning':
            evidence=json.loads(request.messages[1].content)['evidence']
            return ModelResult(model='temporary task role fixture',prompt_tokens=20,completion_tokens=10,content=json.dumps({'conclusion':'ready' if control['phase']=='preflight' else 'supported','summary':'Review supplied evidence only.','findings':[],'evidence_step_ids':[s['step_id'] for s in evidence.get('steps',[])],'limitations':['Fixture, not a model capability evaluation.']}))

        if args.analytical_fixture and json.loads(request.messages[0].content).get('role')=='analytical_reasoning':
            observed=json.loads(request.messages[-1].content.split('Recorded read-only evidence: ',1)[1])
            question=json.loads(request.messages[1].content)['question']
            filename=next((n for n in ['diabetic_sample_5000.csv','diabetic_data.csv'] if n in question),'encounters.csv')
            source='data/input/test/'+filename
            if 'simulate a partial analytical' in request.messages[1].content.lower() and any(o['tool']=='assess_table' for o in observed):
                from geoagent_harness.model import ModelClientError
                raise ModelClientError.timeout()
            if not any(o['tool']=='assess_table' for o in observed):action={'action':'assess_table','path':source,'operation':'profile'}
            elif not any(o['tool']=='profile_table' for o in observed):action={'action':'profile_table','path':source,'options':{'numeric_columns':['time_in_hospital'],'distinct_columns':['patient_nbr']}}
            else:
                profile=next(o['result'] for o in observed if o['tool']=='profile_table')
                mean=next(p['numeric']['mean'] for p in profile['profiles'] if p['name']=='time_in_hospital')
                action={'action':'answer','message':f"The complete {filename} contains {profile['source_rows']:,} encounters and {profile['distinct_counts']['patient_nbr']:,} distinct patients. Mean time_in_hospital is {mean:.6g}. The neighbouring sample has unverified provenance; I used the explicitly selected source. Next examine missingness and readmission groups."}
            return ModelResult(model='temporary analytical fixture',content=json.dumps(action))

        role=json.loads(request.messages[0].content).get('agent',{}).get('id')
        with (root/'model-calls.jsonl').open('a') as handle:
            handle.write(json.dumps({'role':role or json.loads(request.messages[0].content).get('agent_id')})+'\n')
        context=json.loads(request.messages[0].content).get('result_view_context')
        latest=json.loads(request.messages[1].content).get('latest_message','')
        if args.statistics_fixture and latest.startswith('Which fields are suitable for statistics based on the recorded inspection'):
            return ModelResult(model='temporary field-guidance fixture',content=json.dumps({'message':'x and y are candidate measurements for distributions and spread. Confirm their units and your objective before choosing a regression outcome. These suggestions preserve the workflow.','plan':None}))
        if args.statistics_fixture and latest.startswith('Compute descriptive statistics for "') and 'typed arguments: ' in latest:
            arguments,_=json.JSONDecoder().raw_decode(latest.split('typed arguments: ',1)[1])
            proposed={'summary':'Selected descriptive analysis','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Describe the selected measurement and groups','arguments':arguments}]}
            return ModelResult(model='temporary selected-analysis fixture',content=json.dumps({'message':'Review the selected methods and source; nothing executed.','plan':proposed}))
        if args.statistics_fixture and any(name in latest for name in ('table_fixture.xlsx','table_fixture.json','table_fixture.jsonl')):
            name=next(name for name in ('table_fixture.xlsx','table_fixture.jsonl','table_fixture.json') if name in latest)
            options={'statistics':{'columns':['x'],'by':['region'],'question':'How does x vary by region?'}}
            if name.endswith('.xlsx'):options['source_options']={'sheet':'Data'}
            proposed={'summary':'Analyze selected record table','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Describe selected measurement by region','arguments':{'path':'data/input/'+name,'analysis':options}}]}
            return ModelResult(model='temporary format fixture',content=json.dumps({'message':'Review the selected table and methods.','plan':proposed}))
        if args.statistics_fixture and any(name in latest for name in ('statistical_fixture.csv','statistical_wide.csv')):
            statistics={'methods':['describe','pearson','covariance','linear_regression'],'columns':['x','y'],'question':'How does y vary with x?','regression':{'outcome':'y','predictors':['x']}}
            wide='statistical_wide.csv' in latest
            if wide:statistics={'methods':['covariance'],'columns':[f'x{i}' for i in range(9)]}
            proposed={'summary':'Numeric statistical analysis','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Compute declared statistical methods','arguments':{'path':'data/input/'+('statistical_wide.csv' if wide else 'statistical_fixture.csv'),'analysis':{'statistics':statistics}},'requires_approval':False,'validation_required':False}]}
            return ModelResult(model='temporary statistics fixture',content=json.dumps({'message':'Review numeric methods, then execute.','plan':proposed}))
        if context and latest in {'Show boundaries layer on the map.','Display band 2 as a color ramp.','Explain the current result.'}:
            candidate=context['results'][0]
            spec={'run_id':context['run_id'],'plan_sha256':context['plan_sha256'],'step_id':candidate['step_id'],'view':'Map'}
            if latest.startswith('Explain'):
                spec['explanation_fields']=[key for key in ('layer_count','layer_features','width','height','band_count') if key in candidate.get('recorded_facts',{})]
            elif latest.startswith('Show boundaries'):
                spec['spatial']={'mode':'vector','layer':'boundaries'}
            else:spec['spatial']={'mode':'raster','bands':[2],'render':'ramp'}
            return ModelResult(model='temporary spatial-view fixture',content=json.dumps({'message':'99999 invented result values must not become evidence.','plan':None,'result_view':spec}))
        if context and latest=='Show total amount by region as a bar chart.':
            candidate=next(item for item in context['results'] if 'Chart' in item['views'])
            return ModelResult(model='temporary result-view fixture',content=json.dumps({'message':'Show recorded regional totals.','plan':None,'result_view':{
                'run_id':context['run_id'],'plan_sha256':context['plan_sha256'],'step_id':candidate['step_id'],
                'view':'Chart','chart':{'group_by':'region','value':'amount','aggregation':'sum'},'chart_kind':'bar'}}))
        if role=='critic' and json.loads(request.messages[0].content).get('required_json_schema',{}).get('title')=='OutcomeAssessment':
            if args.critic_graph_fixture:
                import time
                (root/'critic-entered').write_text('fixture only')
                deadline=time.monotonic()+25
                while (root/'hold-critic').exists():
                    if time.monotonic()>deadline:raise TimeoutError('Fixture review hold expired')
                    time.sleep(.02)
                if (root/'fail-critic').exists():raise TimeoutError('Fixture Critic unavailable')
            source=json.loads(request.messages[1].content)
            return ModelResult(model='temporary Critic fixture',content=json.dumps({'deterministic_status':source['deterministic_status'],
                'conclusion':'supported' if source['deterministic_status']=='completed' else 'needs_attention',
                'summary':'Recorded operations completed and their reported validation is available.' if source['deterministic_status']=='completed' else 'The run stopped; inspect completed steps and partial outputs before recovery.',
                'findings':[],'limitations':['Fixture observations do not prove suitability for other inputs.'],'reusable_method':None}))
        if args.acquisition_fixture:
            from geoagent_harness.operations.packages import installed_packages,package_sha
            if role=='critic':return ModelResult(model='temporary capability Critic',content=json.dumps({'assessment':'suitable','reason':'Trim then uppercase matches the request.','limitations':['Synthetic fixtures only.']}))
            payload=json.loads(request.messages[1].content);latest=payload.get('latest_message','').lower()
            text=next((p for p in installed_packages(root).values() if p.text_transform is not None),None)
            if 'uppercase' in latest or 'registered operation ext_text_' in latest:
                if text:
                    proposed={'summary':'Inspect and normalize region','steps':[
                        {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect CSV','arguments':{'path':'data/input/sample_orders.csv'}},
                        {'step_id':'step_2','skill':text.id,'purpose':'Normalize region','arguments':{'path':'data/input/sample_orders.csv','package_sha256':package_sha(text)},'depends_on':['step_1']}]}
                    return ModelResult(model='temporary capability Planner',content=json.dumps({'message':'Review normalized region workflow.','plan':proposed}))
                if json.loads(request.messages[0].content).get('capability_acquisition',{}).get('enabled'):
                    return ModelResult(model='temporary capability Planner',content=json.dumps({'message':'Prepare a missing text adapter.','plan':None,'capability_request':{'gap_reason':'No installed string normalization operation.','definition':{'source_column':'region','output_column':'region_clean','steps':[{'kind':'strip'},{'kind':'upper'}]}}}))
                return ModelResult(model='temporary capability Planner',content=json.dumps({'message':'String normalization is not registered. Optional capability acquisition is OFF.','plan':None}))
            return ModelResult(model='temporary capability Planner',content=json.dumps({'message':'Inspection ready.','plan':{'summary':'Inspect CSV','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect CSV','arguments':{'path':'data/input/sample_orders.csv'}}]}}))
        if args.recipe_runs_fixture and role in {'planner','critic'}:
            if role=='planner':
                from geoagent_harness.recipe_catalog.composition import catalog
                value=catalog(root)['recipe_clean_csv'].model_dump(mode='json')
                value['id']='recipe_browser_clean'
                value['name']='Browser verified cleaner'
            else:
                value={'conclusion':'supported','findings':[],'limitations':['Synthetic fixtures cover a small scope only.']}
            return ModelResult(model='temporary recipe role fixture',content=json.dumps(value))
        if args.diabetes_decoding_fixture:
            from diabetes_test_flow import make_plan
            from geoagent_harness.mcp_server.settings import load_settings
            proposed=make_plan(load_settings()).plan.model_dump(mode='json')
            proposed['steps']=proposed['steps'][:4]
            proposed['summary']='Prepare the real diabetes sample and verify supplied codebook labels'
            return ModelResult(model='temporary diabetes proposal fixture',content=json.dumps({'message':'Preparation proposed; original records and code values will be preserved. Nothing approved or executed.','plan':proposed}))
        if args.postgres_authorization_fixture:
            import hashlib
            from geoagent_harness.postgres.service import connection_sha256
            from geoagent_harness.mcp_server.settings import load_settings
            if 'soft delete' in latest.lower():
                skill='soft_delete_postgres_rows'
                arguments={'target_schema':'agent_sandbox','target_table':'visits','expected_table_sha256':'a'*64,'key_column':'encounter_id','keys':['001'],'deleted_column':'is_deleted','expected_affected_rows':1}
            else:
                skill='import_csv_to_postgres'
                arguments={'connection_sha256':connection_sha256(load_settings()),'target_schema':'agent_sandbox','target_table':'visits','path':'data/input/sample_orders.csv','source_sha256':hashlib.sha256((root/'data/input/sample_orders.csv').read_bytes()).hexdigest(),'columns':[{'source':'order_id','name':'order_id','type':'text','nullable':False},{'source':'amount','name':'amount','type':'numeric'}],'key_columns':['order_id']}
            return ModelResult(model='temporary PostgreSQL scope fixture',content=json.dumps({'message':'Review the exact database changes beside the graph. Nothing executed.','plan':{'summary':'Review PostgreSQL operation','steps':[{'step_id':'step_1','skill':skill,'purpose':'Prepare a reviewed database operation','arguments':arguments,'requires_approval':True,'validation_required':True}]}}))
        if args.calculation_fixture:
            proposed={'summary':'Calculate doubled amount','steps':[
                {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect CSV','arguments':{'path':'data/input/sample_orders.csv'},'requires_approval':False,'validation_required':False},
                {'step_id':'step_2','skill':'calculate_csv_columns','purpose':'Double amount and propagate missing values','arguments':{'path':'data/input/sample_orders.csv','missing_policy':'propagate','calculations':[{'output_column':'doubled','expression':{'kind':'binary','operator':'multiply','left':{'kind':'column','name':'amount'},'right':{'kind':'number','value':2}}}],'assumptions':['amount uses the original source units']},'depends_on':['step_1'],'requires_approval':True,'validation_required':True}]}
            if args.visualization_fixture and (root/'vector-visualization').exists():
                proposed={'summary':'Inspect vector fixture', 'steps':[
                    {'step_id':'step_1','skill':'inspect_vector','purpose':'Inspect vector metadata',
                     'arguments':{'path':'data/input/sample_points.geojson'},'requires_approval':False,'validation_required':False}]}
            if args.report_authorization_fixture:
                proposed={'summary':'Inspect CSV and assess an existing fixture table; record evidence', 'steps':[
                    {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect CSV metadata','arguments':{'path':'data/input/sample_orders.csv'},'requires_approval':False,'validation_required':False},
                    {'step_id':'step_2','skill':'validate_postgis_layer','purpose':'Assess existing fixture table','arguments':{'target_schema':'public','target_table':'fixture_points'},'requires_approval':True,'validation_required':True},
                    {'step_id':'step_3','skill':'generate_report','purpose':'Record evidence report','arguments':{'task_id':'fixture-report'},'requires_approval':True,'validation_required':False},
                ]}
            if args.write_policy_fixture:
                proposed['steps'].append({'step_id':'step_3','skill':'export_csv','purpose':'Export calculated table','arguments':{'source_step':'step_2'},'depends_on':['step_2'],'requires_approval':True,'validation_required':True})
            if args.calculation_deferral_fixture or args.calculation_invalid_json_fixture or args.calculation_omission_fixture:
                system=json.loads(request.messages[0].content)
                assert 'calculate_csv_columns' in system['operation_argument_schemas']
                assert system['reply_shape_example']['plan'] is not None
                assert request.response_schema and request.response_schema['type']=='object'
                if len(request.messages)==2:
                    if args.calculation_reuse_claim_fixture:
                        branches=request.response_schema.get('anyOf',[request.response_schema])
                        assert all('reused_recipe_ids' not in branch['properties'] for branch in branches)
                        return ModelResult(model='temporary calculation fixture',content=json.dumps({'message':'Calculation ready','plan':proposed,'reused_recipe_ids':['recipe_inspect_csv']}))
                    if args.calculation_omission_fixture:
                        return ModelResult(model='temporary calculation fixture',content=json.dumps({'message':'The calculation workflow is planned.','plan':historical_plan}))
                    if args.calculation_invalid_json_fixture:
                        return ModelResult(model='temporary calculation fixture',content='{"message":"Ready","plan":',finish_reason='stop',response_format='json_schema')
                    return ModelResult(model='temporary calculation fixture',content=json.dumps({
                        'message':'The proposal contains invalid schema structure. I will correct the plan using required_json_schema. Please confirm if you would like me to proceed.', 'plan':None}))
                correction=json.loads(request.messages[-1].content)
                assert correction['failure_kind']==('reuse_claim' if args.calculation_reuse_claim_fixture else 'request_coverage' if args.calculation_omission_fixture else 'JSON' if args.calculation_invalid_json_fixture else 'repair_deferral')
                assert correction['valid_reply_structure_example']['plan']
            return ModelResult(model='temporary calculation fixture',content=json.dumps({'message':'Review the typed formula; no calculation has run.','plan':proposed}))
        if args.recipe_runs_fixture:
            payload=json.loads(request.messages[1].content)
            latest=payload.get('latest_message','').casefold()
            if 'find a suitable method automatically' in latest:
                observations=[]
                for message in request.messages[2:]:
                    if message.role=='user':
                        try:observations.append(json.loads(message.content).get('recipe_discovery_result'))
                        except ValueError:pass
                observations=[value for value in observations if value]
                if not observations:
                    return ModelResult(model='temporary Planner fixture',content=json.dumps({'message':'Searching methods','recipe_discovery':{'action':'search','query':'csv cleaning'}}))
                inspected=next((item.get('own_chat_example') for item in observations if item.get('own_chat_example')),None)
                if inspected is None:
                    matches=observations[-1].get('matches',[])
                    method=next((item for item in matches if 'method_id' in item),None)
                    return ModelResult(model='temporary Planner fixture',content=json.dumps({'message':'Inspecting method','recipe_discovery':{'action':'inspect',**({'method_id':method['method_id']} if method else {'recipe_id':'recipe_clean_csv'})}}))
                requirements={item['skill']:item for item in json.loads(request.messages[0].content)['selected_skill_requirements']}
                steps=[]
                for step in inspected['historical_operations']:
                    arguments=dict(step['arguments'])
                    if 'path' in arguments:arguments['path']='data/input/next_orders.csv'
                    gate=requirements[step['skill']]
                    steps.append({'step_id':step['step_id'],'skill':step['skill'],'purpose':'Adapt discovered method','arguments':arguments,'depends_on':step['depends_on'],
                                  'requires_approval':gate['requires_approval'],'validation_required':gate['validation_required']})
                return ModelResult(model='temporary Planner fixture',content=json.dumps({'message':'Prepared CSV cleaning from the discovered method.','reused_recipe_ids':[inspected['method_id']],
                    'plan':{'summary':'Clean the new CSV using a discovered method','steps':steps}}))
            if 'reusable' in latest and 'make' in latest:
                return ModelResult(model='temporary Planner fixture',content=json.dumps({'message':'Prepare a reusable recipe.','workflow_action':'prepare_recipe'}))
            if payload.get('successful_method_examples') and (payload.get('selected_successful_method_id') or 'saved successful method' in latest or 'repeat cleaning' in latest):
                example=payload['successful_method_examples'][0]
                requirements={item['skill']:item for item in json.loads(request.messages[0].content)['selected_skill_requirements']}
                steps=[]
                for step in example['historical_operations']:
                    arguments=dict(step['arguments'])
                    if 'next_orders.csv' in latest and 'path' in arguments:arguments['path']='data/input/next_orders.csv'
                    gate=requirements[step['skill']]
                    steps.append({'step_id':step['step_id'],'skill':step['skill'],'purpose':'Adapt saved method','arguments':arguments,'depends_on':step['depends_on'],
                                  'requires_approval':gate['requires_approval'],'validation_required':gate['validation_required']})
                return ModelResult(model='temporary Planner fixture',content=json.dumps({'message':'Adapted saved successful method '+example['method_id'],'plan':{'summary':'Adapt successful method to current CSV','steps':steps,'assumptions':['Uses method '+example['method_id']]}}))
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
            from geoagent_harness.planner.request_coverage import inspection_only_skill
            from geoagent_harness.interface_api.inspection_policy import request_source
            inspector=inspection_only_skill(latest)
            if args.spatial_view_fixture and inspector in {'inspect_vector','inspect_raster'}:
                proposed={'summary':'Spatial viewing fixture','steps':[{'step_id':'step_1','skill':inspector,'purpose':'Inspect spatial source','arguments':{'path':request_source(latest)},'requires_approval':False,'validation_required':False}]}
            elif latest.startswith('Inspect large_orders.csv'):
                proposed={'summary':'Inspect large CSV','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect large CSV without writes','arguments':{'path':'data/input/large_orders.csv'}}]}
            elif latest.startswith('Inspect large_terrain.tif'):
                proposed={'summary':'Inspect large TIFF','steps':[{'step_id':'step_1','skill':'inspect_raster','purpose':'Inspect raster metadata without loading pixels','arguments':{'path':'data/input/large_terrain.tif'}}]}
            elif latest.startswith('Inspect sample_points.geojson'):
                proposed={'summary':'Vector inspection fixture','steps':[{'step_id':'step_1','skill':'inspect_vector','purpose':'Inspect vector metadata','arguments':{'path':'data/input/sample_points.geojson'},'requires_approval':False,'validation_required':False}]}
            elif latest.startswith('Inspect sample_dem.tif'):
                proposed={'summary':'Raster inspection fixture','steps':[{'step_id':'step_1','skill':'inspect_raster','purpose':'Inspect raster metadata','arguments':{'path':'data/input/sample_dem.tif'},'requires_approval':False,'validation_required':False}]}
            elif 'Vector task inspection' in latest:
                proposed={'summary':'Vector task fixture','steps':[{'step_id':'step_1','skill':'inspect_vector','purpose':'Inspect vector','arguments':{'path':'data/input/sample_points.geojson'},'requires_approval':False,'validation_required':False}]}
            elif 'Read-only CSV inspection' in latest or latest.strip() == 'Inspect sample_orders.csv. Return row count and column names. No writes.':
                proposed={'summary':'Read-only CSV fixture','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect CSV without writing','arguments':{'path':'data/input/sample_orders.csv'},'requires_approval':False,'validation_required':False}]}
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
from geoagent_harness.capabilities import service as capability_service
capability_service.SharedModelClient=lambda settings:FixtureModel()
conversation.SharedModelClient=lambda settings:FixtureModel()
if args.agent_modes_fixture:
    import geoagent_harness.orchestrator.task_agents as task_agents
    task_agents.SharedModelClient=lambda settings:FixtureModel()
if args.analytical_fixture:
    os.environ['ACTIONCHARTER_ANALYTICAL_RUNTIME']='docker' if os.environ.get('ACTIONCHARTER_BROWSER_DOCKER')=='1' else 'local'
    from geoagent_harness.tabular import analyst
    analyst.SharedModelClient=lambda settings:FixtureModel()
method_memory.SharedModelClient=lambda settings:FixtureModel()
method_helper.SharedModelClient=lambda settings:FixtureModel()
from geoagent_harness.interface_api import run_assessment
run_assessment.SharedModelClient=lambda settings:FixtureModel()
if args.recipe_runs_fixture or args.write_policy_fixture:
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
from geoagent_harness.write_policy import session
policy_session=session(root,enabled=os.environ.get('ENABLE_WRITE_TOOLS')=='true')
policy_session.__enter__()
http=ThreadingHTTPServer(('127.0.0.1',0),server._handler(root))
print(json.dumps({'port':http.server_port,'root':str(root)}),flush=True)
http.serve_forever()
