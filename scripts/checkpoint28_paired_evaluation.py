"""Paired Planner ON/OFF evaluation; disposable fixtures and fresh authority only.

Default fixture mode tests the harness. --model uses the installed local model;
no dependency installation, model training, live database or project-data writes.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import platform
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from time import monotonic

REPO = Path(__file__).resolve().parents[1]
CHAT = 'b' * 32
THRESHOLDS = {'minimum_cases': 6, 'minimum_repetitions_for_benefit': 2,
              'all_safety_checks_pass': True, 'on_correct_not_less_than_off': True,
              'benefit_requires_more_correct_or_fewer_model_calls': True,
              'on_latency_ratio_max': 1.20}


def step(skill, arguments, *, after=None):
    item = {'step_id': 'step_1', 'skill': skill, 'purpose': 'Perform the explicitly requested fixture operation',
            'arguments': arguments, 'requires_approval': skill not in {'inspect_csv','inspect_vector'},
            'validation_required': skill not in {'inspect_csv','inspect_vector'}}
    if after: item['depends_on'] = [after]
    return item


def fixed_plan(case, *, training=False):
    prefix = 'seed_' if training else ''
    table = f'data/input/{prefix}orders.csv'
    vector = f'data/input/{prefix}boundaries.geojson'
    target = f'data/output/{prefix}{case}.csv'
    if case == 'vector_inspection':
        steps = [step('inspect_vector', {'path':vector})]
    else:
        steps = [step('inspect_csv', {'path':table})]
    if case == 'selection':
        steps.append(step('select_csv_columns', {'path':table,'columns':['order_id','region'],'target_path':target}, after='step_1'))
    elif case == 'filter':
        steps.append(step('filter_csv_rows', {'path':table,'predicates':[{'column':'amount','operator':'ge','value':5,'value_type':'number'}],'match':'all','target_path':target}, after='step_1'))
    elif case == 'calculation':
        steps.append(step('calculate_csv_columns', {'path':table,'target_path':target,'missing_policy':'propagate',
            'calculations':[{'output_column':'doubled','expression':{'kind':'binary','operator':'multiply','left':{'kind':'column','name':'amount'},'right':{'kind':'number','value':2}}}]}, after='step_1'))
    elif case == 'combined':
        steps = [step('inspect_vector', {'path':vector}),
            step('vector_attributes_to_csv', {'path':vector,'target_path':f'data/output/{prefix}attributes.csv'}, after='step_1'),
            step('aggregate_csv', {'source_step':'step_2','target_path':target,'by':['region'],
                'aggregations':[{'column':'amount','function':'sum','output_column':'total_amount'}]}, after='step_2')]
    for index, item in enumerate(steps,1): item['step_id'] = f'step_{index}'
    return {'summary':f'{case} with declared fixtures','steps':steps}


CASES = {
    'csv_inspection': 'Inspect orders.csv. Return row count, column names and a bounded preview. No writes.',
    'selection': 'Inspect orders.csv, then select only order_id and region into a fresh CSV. Read the original CSV for selection.',
    'filter': 'Inspect orders.csv, then keep rows where numeric amount is at least 5. Preserve all columns and write a fresh CSV. Read the original CSV for filtering.',
    'calculation': 'Inspect orders.csv, then calculate doubled = amount * 2, preserving all original columns and propagating missing values. Save the calculated table to a fresh CSV.',
    'vector_inspection': 'Inspect boundaries.geojson. Return feature count, fields and CRS. No writes.',
    'combined': 'Inspect boundaries.geojson. Extract its flat attributes to a fresh CSV, explicitly dropping geometry. Then group that CSV by region and sum amount as total_amount into another fresh CSV. Use source_step for aggregation.'}


def fixture_project(root):
    for directory in ('context','agents'): copytree(REPO/directory,root/directory)
    (root/'README.md').write_text((REPO/'README.md').read_text())
    (root/'data/input').mkdir(parents=True); (root/'data/output').mkdir()
    (root/'data/input/seed_orders.csv').write_text('order_id,region,amount\n001,North,10\n002,North,20\n003,South,5\n')
    (root/'data/input/orders.csv').write_text('order_id,region,amount\n101,North,7\n102,South,12\n103,North,3\n104,West,0\n')
    for prefix,amounts in [('seed_',[10,20,5]),('',[7,12,3])]:
        features=[{'type':'Feature','properties':{'order_id':str(index+1),'region':region,'amount':amount},
                   'geometry':{'type':'Point','coordinates':[-71+index/10,42+index/10]}}
                  for index,(region,amount) in enumerate(zip(['North','South','North'],amounts))]
        (root/f'data/input/{prefix}boundaries.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features}))


class FixtureModel:
    """Harness self-test only; this is never reported as a model benchmark."""
    def __init__(self, plan): self.plan=plan
    def complete(self, request):
        from geoagent_harness.model.schemas import ModelResult
        return ModelResult(model='deterministic-harness-fixture',content=json.dumps({'message':'Fixture proposal; nothing executed','plan':self.plan}))


class Measured:
    def __init__(self, client): self.client=client; self.calls=[]
    def complete(self, request):
        system=json.loads(request.messages[0].content)
        usage={'prompt_bytes':sum(len(m.content.encode()) for m in request.messages),'temperature':request.temperature,
               'recommendations_supplied':system.get('outcome_recommendations'),'seconds':None}
        self.calls.append(usage); start=monotonic()
        try:
            result=self.client.complete(request)
            usage.update(prompt_tokens=result.prompt_tokens,completion_tokens=result.completion_tokens,finish_reason=result.finish_reason)
            return result
        except Exception as error:
            usage['error_code']=getattr(error,'code',type(error).__name__);raise
        finally: usage['seconds']=round(monotonic()-start,3)


def save_review(root, response):
    from geoagent_harness.planner.schemas import PlannerResult
    from geoagent_harness.interface_api.server import save_interface_reviewed_plan, InterfaceReviewedPlanSaveRequest
    from geoagent_harness.interface_api.workflow import WorkflowRequest, prepare_workflow
    from geoagent_harness.approvals import plan_sha256
    result=PlannerResult.model_validate({key:value for key,value in response['planner_result'].items() if key in PlannerResult.model_fields})
    saved=save_interface_reviewed_plan(InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=result,
        confirmed_plan_sha256=plan_sha256(result.plan),allowed_skill_ids=response['allowed_skill_ids']),project_root=root)
    base={'plan_filename':saved['plan_filename'],'confirmed_plan_sha256':saved['plan_sha256']}
    review=prepare_workflow(WorkflowRequest(action='prepare_workflow',**base),project_root=root)
    return result,base,review


def execute(root, response, *, check_gates=False):
    from geoagent_harness.interface_api.workflow import WorkflowRequest, prepare_workflow, authorize_workflow
    from geoagent_harness.interface_api.workflow_runs import RunRequest, run_action
    from geoagent_harness import write_policy
    result,base,review=save_review(root,response)
    writes=bool(review['write_step_ids']); auth={}
    gate_checks={}
    if writes:
        if check_gates:
            assert not review['execution_available']
            blocked=False
            try:
                denied=run_action(RunRequest(action='start',workflow=WorkflowRequest(action='execute_workflow',**base,
                    confirmed_review_sha256=review['review_sha256'],confirm_execution=True),conversation_id=CHAT),project_root=root,background=False)
                blocked=denied['status']=='failed' and not denied['execution_performed']
            except (ValueError, RuntimeError): blocked=True
            assert blocked,'Write attempt was not blocked with writes OFF'
            gate_checks['writes_off_blocked']=True
        policy=write_policy.snapshot(root)
        write_policy.update(root,write_policy.PolicyUpdate(enabled=True,session_id=policy['session_id'],revision=policy['revision']))
        review=prepare_workflow(WorkflowRequest(action='prepare_workflow',**base),project_root=root)
        if check_gates:
            blocked=False
            try:
                denied=run_action(RunRequest(action='start',workflow=WorkflowRequest(action='execute_workflow',**base,
                    confirmed_review_sha256=review['review_sha256'],confirm_execution=True),conversation_id=CHAT),project_root=root,background=False)
                blocked=denied['status']=='failed' and not denied['execution_performed']
            except (ValueError, RuntimeError): blocked=True
            assert blocked,'Write attempt was not blocked without exact authority'
            gate_checks['missing_authority_blocked']=True
    if review['approval_required_step_ids']:
        auth=authorize_workflow(WorkflowRequest(action='authorize_workflow',**base,confirmed_review_sha256=review['review_sha256'],
            approve_required_steps=True,approver='paired-fixture-evaluation',reason='Explicit evaluation authority for disposable fixture outputs only'),project_root=root)
    else:
        assert not writes
        gate_checks['read_only_no_authorize']=True
    record=run_action(RunRequest(action='start',conversation_id=CHAT,workflow=WorkflowRequest(action='execute_workflow',**base,
        confirmed_review_sha256=review['review_sha256'],confirm_execution=True,plan_approval_filename=auth.get('plan_approval_filename'),
        recipe_approval_filename=auth.get('recipe_approval_filename'))),project_root=root,background=False)
    if record['status']!='completed':raise ValueError('Fixture execution did not complete: '+str(record.get('finding')))
    return record,gate_checks,bool(auth)


def verify(case, record, root):
    """Independent task oracle, in addition to operation-level validation."""
    producer=fixed_plan(case)['steps'][-1]['skill']
    last=next(step['outcome'] for step in reversed(record['steps']) if step['skill_id']==producer)
    if case=='csv_inspection':
        assert last['row_count']==4 and [c['name'] if isinstance(c,dict) else c for c in last['columns']]==['order_id','region','amount']
        assert len(last['preview'])<=20
    elif case=='vector_inspection':
        assert last['layers'][0]['feature_count']==3 and last['layers'][0]['crs']
    else:
        with (root/last['output']['path']).open() as f:rows=list(csv.DictReader(f))
        with (root/'data/input/orders.csv').open() as f:source=list(csv.DictReader(f))
        if case=='selection':assert rows==[{k:r[k] for k in ['order_id','region']} for r in source]
        elif case=='filter':assert rows==[r for r in source if float(r['amount'])>=5]
        elif case=='calculation':assert rows==[{**r,'doubled':str(float(r['amount'])*2).removesuffix('.0')} for r in source] or (len(rows)==len(source) and all(all(r[k]==original[k] for k in original) and float(r['doubled'])==float(original['amount'])*2 for r,original in zip(rows,source)))
        elif case=='combined':assert {r['region']:float(r['total_amount']) for r in rows}=={'North':10,'South':12}
        assert all(s['validation_outcome']['passed'] for s in record['steps'] if s['skill_id'] not in {'inspect_csv','inspect_vector'})


def summarize(attempts, repetitions, *, actual_model):
    sides={name:[a for a in attempts if a['recommendations']==name] for name in ('OFF','ON')}
    metrics={name:{'attempts':len(rows),'correct':sum(a['correct_output'] for a in rows),'valid_plans':sum(a['valid_plan'] for a in rows),
        'model_calls':sum(len(a['calls']) for a in rows),'seconds':round(sum(a['seconds'] for a in rows),3),
        'corrections':sum(a['correction_attempted'] for a in rows),'failed':sum(not a['correct_output'] for a in rows),'extra_read_steps':sum(a.get('extra_read_steps',0) for a in rows),
        'prompt_tokens':sum(c.get('prompt_tokens') or 0 for a in rows for c in a['calls']),
        'completion_tokens':sum(c.get('completion_tokens') or 0 for a in rows for c in a['calls']),
        'token_usage_complete':all(c.get('prompt_tokens') is not None and c.get('completion_tokens') is not None for a in rows for c in a['calls'])}
        for name,rows in sides.items()}
    off,on=metrics['OFF'],metrics['ON']
    sufficient=all(m['attempts']>=THRESHOLDS['minimum_cases']*repetitions for m in metrics.values()) and repetitions>=2
    no_regression=on['correct']>=off['correct']
    benefit=on['correct']>off['correct'] or (on['correct']==off['correct'] and on['model_calls']<off['model_calls'])
    latency=on['seconds']<=off['seconds']*THRESHOLDS['on_latency_ratio_max']
    pairs={(a['case'],a['repetition']) for a in attempts}
    paired_no_regression=all(not any(a['correct_output'] for a in sides['OFF'] if (a['case'],a['repetition'])==key) or any(a['correct_output'] for a in sides['ON'] if (a['case'],a['repetition'])==key) for key in pairs)
    all_correct=all(a['correct_output'] for a in attempts)
    return {'metrics':metrics,'paired_no_regression':paired_no_regression,'all_expected_results_passed':all_correct,'representative_threshold_met':bool(actual_model and sufficient and all_correct and paired_no_regression and no_regression and benefit and latency),
            'decision':'optional_OFF_until_representative_benefit_is_demonstrated','model_adoption':'not_measured',
            'human_interventions':0,'scripted_authorizations':sum(a.get('scripted_authorization',False) for a in attempts)}


def evaluate(*, model=None, endpoint='http://127.0.0.1:11434/v1', timeout=90, max_tokens=1024, repetitions=1, cases=None, output=None):
    from geoagent_harness.interface_api.conversation import TurnRequest, conversation_turn
    from geoagent_harness.planner.schemas import PlannerResult
    from geoagent_harness import write_policy
    from geoagent_harness.model import SharedModelClient
    from geoagent_harness.model.settings import ModelSettings
    chosen=list(cases or CASES)
    unknown=set(chosen)-set(CASES)
    if unknown:raise ValueError('Unknown evaluation case')
    # These settings affect this evaluation process only, not .env or a launcher.
    os.environ.update(ENABLE_WRITE_TOOLS='false',ALLOW_OVERWRITE='false',MODEL_NAME=model or 'fixture',MODEL_BASE_URL=endpoint,
                      MODEL_TIMEOUT_SECONDS=str(timeout),MODEL_MAX_TOKENS=str(max_tokens),MODEL_REASONING_EFFORT='none',PLANNER_TURN_TIMEOUT_SECONDS=str(min(timeout*2,240)))
    settings=ModelSettings(endpoint,model or 'fixture',timeout,max_tokens,'none')
    report={'schema_version':'1.0','evaluation':'actual_model_paired' if model else 'deterministic_harness_self_test',
        'thresholds':THRESHOLDS,'policy_version':'own-chat-checks-v1','training':'Fixed temporary workflows executed and checked before cloning; fixture Planner, no model training',
        'machine':{'platform':platform.system(),'architecture':platform.machine(),'logical_cpus':os.cpu_count()},
        'case_definition_sha256':hashlib.sha256(json.dumps({'requests':CASES,'plans':{name:fixed_plan(name) for name in CASES}},sort_keys=True).encode()).hexdigest(),'settings':settings.__dict__,'repetitions':repetitions,'cases':chosen,'attempts':[],
        'live_database_calls':0,'scope':'temporary fixtures only','limitations':['No statistical reliability claim from a small trial','Model adoption not inferred from supplied recommendations']}
    def persist():
        if output:output.write_text(json.dumps(report,indent=2)+'\n')
    with TemporaryDirectory(prefix='actioncharter-paired-') as directory:
        parent=Path(directory)
        for index,case in enumerate(chosen):
            seed=parent/f'seed-{case}';seed.mkdir();fixture_project(seed)
            # Execute real training fixtures once, then clone identical history/evidence.
            with write_policy.session(seed):
                initial=conversation_turn(TurnRequest(action='turn',conversation_id=CHAT,message='Prepare a declared training fixture',allowed_skill_ids=[s['skill'] for s in fixed_plan(case,training=True)['steps']]),project_root=seed,model_client=FixtureModel(fixed_plan(case,training=True)))
                execute(seed,initial)
            for repetition in range(repetitions):
                order=['OFF','ON'] if (index+repetition)%2==0 else ['ON','OFF']
                for side in order:
                    root=parent/f'{case}-{repetition}-{side}';copytree(seed,root)
                    attempt={'case':case,'repetition':repetition+1,'recommendations':side,'order':order,'valid_plan':False,'correct_output':False,
                             'correction_attempted':False,'calls':[],'scripted_authorization':False}
                    report['attempts'].append(attempt);start=monotonic()
                    measured=Measured(SharedModelClient(settings) if model else FixtureModel(fixed_plan(case)))
                    try:
                        with write_policy.session(root):
                            state=conversation_turn(TurnRequest(action='read',conversation_id=CHAT),project_root=root)
                            state=conversation_turn(TurnRequest(action='configure_recommendations',conversation_id=CHAT,expected_revision=state['revision'],recommendations_enabled=side=='ON'),project_root=root)
                            request='Replace the current workflow with the following complete task using the NEW original input. Allocate fresh outputs. Do not execute from conversation text. '+CASES[case]
                            allowed=list(dict.fromkeys(s['skill'] for s in fixed_plan(case)['steps']))
                            response=conversation_turn(TurnRequest(action='turn',conversation_id=CHAT,expected_revision=state['revision'],message=request,allowed_skill_ids=allowed),project_root=root,model_client=measured)
                            diagnostic=response['context_usage']['model_request']
                            attempt['correction_attempted']=diagnostic['stage'].startswith('planner_correction')
                            if not response['planner_result']:raise ValueError('No complete proposal')
                            parsed=PlannerResult.model_validate({key:value for key,value in response['planner_result'].items() if key in PlannerResult.model_fields})
                            skills=[s.skill for s in parsed.plan.steps]
                            attempt['observed_skills']=skills
                            assert set(skills)==set(allowed) and skills[0]==allowed[0],'Missing requested operation or unexpected operation/order; nothing executed'
                            assert [skill for skill in skills if skill not in {'inspect_csv','inspect_vector'}]==[skill for skill in allowed if skill not in {'inspect_csv','inspect_vector'}],'Repeated or reordered writes; nothing executed'
                            attempt['extra_read_steps']=max(0,len(skills)-len(allowed))
                            expected_source='data/input/boundaries.geojson' if case in {'vector_inspection','combined'} else 'data/input/orders.csv'
                            assert all(s.arguments.get('path',expected_source)==expected_source for s in parsed.plan.steps),'Wrong source; nothing executed'
                            assert len(parsed.plan.steps)<=len(allowed)+1,'Unexpected repetition; nothing executed'
                            attempt['valid_plan']=True;attempt['skills']=skills
                            attempt['recommendation_receipt']=response['context_usage']['outcome_recommendations']
                            record,gates,authorized=execute(root,response,check_gates=True)
                            attempt.update(gates=gates,scripted_authorization=authorized,run_status=record['status'])
                            verify(case,record,root);attempt['correct_output']=True
                            attempt['input_sha256']=hashlib.sha256((root/expected_source).read_bytes()).hexdigest()
                    except Exception as error:
                        attempt['error']={'code':getattr(error,'code',type(error).__name__),'finding':str(error)[:700],'findings':getattr(error,'findings',[])}
                        diagnostic=getattr(error,'planner_diagnostics',{}) or {}
                        attempt['correction_attempted']=diagnostic.get('stage','').startswith('planner_correction')
                    finally:
                        attempt['seconds']=round(monotonic()-start,3);attempt['calls']=measured.calls
                        print(json.dumps({key:attempt.get(key) for key in ('case','repetition','recommendations','valid_plan','correct_output','seconds','error')}),flush=True)
                        persist()
    report['summary']=summarize(report['attempts'],repetitions,actual_model=bool(model));persist()
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model');parser.add_argument('--endpoint',default='http://127.0.0.1:11434/v1')
    parser.add_argument('--timeout',type=float,default=90);parser.add_argument('--max-tokens',type=int,default=1024)
    parser.add_argument('--repetitions',type=int,choices=[1,2,3],default=1)
    parser.add_argument('--case',choices=list(CASES),action='append')
    parser.add_argument('--output',type=Path,default=Path('/tmp/actioncharter-checkpoint28-paired.json'))
    args=parser.parse_args()
    if args.output.exists() and args.output.is_symlink():parser.error('Output must not be a symlink')
    report=evaluate(model=args.model,endpoint=args.endpoint,timeout=args.timeout,max_tokens=args.max_tokens,repetitions=args.repetitions,cases=args.case,output=args.output)
    print(json.dumps(report['summary'],indent=2))
    return 0 if all(a['correct_output'] for a in report['attempts']) else 1

if __name__=='__main__':raise SystemExit(main())
