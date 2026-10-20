#!/usr/bin/env python3
"""Sequential real-model evaluation using disposable synthetic files only.

This explicitly authorizes fresh writes inside its temporary project, never the
operator's project or a database. It neither installs nor trains a model.
"""
import argparse
import csv
import json
import os
import platform
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--endpoint', default='http://127.0.0.1:11434/v1')
    parser.add_argument('--timeout', type=float, default=90)
    parser.add_argument('--domain', choices=['spatial','tabular','combined'])
    parser.add_argument('--max-tokens',type=int,default=1024)
    parser.add_argument('--output', type=Path, default=Path('/tmp/actioncharter-checkpoint27-model-evaluation.json'))
    args = parser.parse_args()
    from geoagent_harness.model import SharedModelClient
    from geoagent_harness.model.settings import ModelSettings
    from geoagent_harness.planner.schemas import PlannerResult
    from geoagent_harness.interface_api.conversation import TurnRequest, conversation_turn
    from geoagent_harness.interface_api.workflow import WorkflowRequest, prepare_workflow, authorize_workflow
    from geoagent_harness.interface_api.workflow_runs import RunRequest, run_action
    from geoagent_harness.interface_api.run_assessment import assess_run
    from geoagent_harness.interface_api.server import save_interface_reviewed_plan, InterfaceReviewedPlanSaveRequest
    from geoagent_harness.recipe_catalog.successful import inventory
    from geoagent_harness.approvals import plan_sha256
    # This process only. No launcher, .env or running service policy is changed.
    os.environ.update(ENABLE_WRITE_TOOLS='true', ALLOW_OVERWRITE='false', MODEL_NAME=args.model,
                      MODEL_BASE_URL=args.endpoint, MODEL_TIMEOUT_SECONDS=str(args.timeout),
                      MODEL_MAX_TOKENS=str(args.max_tokens), MODEL_REASONING_EFFORT='none')
    metrics = []
    settings = ModelSettings(args.endpoint, args.model, args.timeout, args.max_tokens, 'none')

    class MeasuredClient:
        def __init__(self):
            self.client = SharedModelClient(settings)
        def __getattr__(self, key):
            return getattr(self.client, key)
        def complete(self, request):
            start = time.monotonic()
            metric = {'prompt_bytes': sum(len(m.content.encode()) for m in request.messages), 'request_timeout_seconds':request.timeout_seconds or settings.timeout_seconds, 'decoder_schema':request.response_schema is not None}
            try:
                reply = self.client.complete(request)
                metric.update(status='returned', prompt_tokens=reply.prompt_tokens, completion_tokens=reply.completion_tokens)
                return reply
            except Exception as error:
                metric.update(status='failed', code=getattr(error, 'code', type(error).__name__))
                raise
            finally:
                metric['seconds'] = round(time.monotonic() - start, 3)
                metrics.append(metric)

    client = MeasuredClient()
    report = {'schema_version': '1.0', 'evaluation': 'actual_local_model_synthetic_data',
              'model': args.model, 'endpoint': args.endpoint, 'settings': settings.__dict__,
              'machine': {'platform': platform.system(), 'architecture': platform.machine(), 'logical_cpus': os.cpu_count()},
              'attempts': [], 'model_calls': metrics, 'live_database_calls': 0,
              'manual_frontend_acceptance': 'not measured by this service evaluation',
              'manual_baseline': 'not measured; no speedup claim', 'human_interventions': 0}
    cases = [
        ('spatial', ['inspect_vector'], 'Inspect boundaries.geojson. Return feature count, fields and CRS. No writes.'),
        ('tabular', ['inspect_csv', 'calculate_csv_columns'], 'Inspect orders.csv, then calculate doubled = amount * 2, preserving all original columns and propagating missing values. Save the calculated table to a fresh CSV.'),
        ('combined', ['vector_attributes_to_csv', 'aggregate_csv'], 'Extract the attributes of boundaries.geojson to a fresh CSV, explicitly dropping geometry. Then group that CSV by region and sum amount as total_amount into another fresh CSV. Use source_step for the second operation.')]
    with tempfile.TemporaryDirectory(prefix='actioncharter-model-eval-') as temp:
        root = Path(temp)
        shutil.copytree(REPO/'context', root/'context')
        shutil.copytree(REPO/'agents', root/'agents')
        (root/'data/input').mkdir(parents=True)
        (root/'data/output').mkdir()
        (root/'data/input/orders.csv').write_text('region,amount\nNorth,10\nNorth,20\nSouth,5\n')
        features = [{'type':'Feature','properties':{'region':region,'amount':amount},'geometry':geometry} for region,amount,geometry in [
            ('North',10,{'type':'Point','coordinates':[-71,42]}),
            ('North',20,{'type':'LineString','coordinates':[[-72,41],[-70,43]]}),
            ('South',5,{'type':'Polygon','coordinates':[[[-72,41],[-70,41],[-70,43],[-72,41]]]})]]
        (root/'data/input/boundaries.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features}))
        for name, skills, prompt in cases:
            if args.domain and name != args.domain:
                continue
            chat = uuid.uuid4().hex
            revision = 0
            for phase in ['initial', 'reuse']:
                message = prompt
                if phase == 'reuse':
                    for filename in ['orders.csv','boundaries.geojson']:
                        target = filename.replace('.', '_again.', 1)
                        shutil.copyfile(root/'data/input'/filename, root/'data/input'/target)
                        message = message.replace(filename, target)
                    (root/'data/input/orders_again.csv').write_text('region,amount\nNorth,20\nNorth,40\nSouth,10\n')
                    changed=json.loads((root/'data/input/boundaries_again.geojson').read_text())
                    for feature in changed['features']:
                        feature['properties']['amount']*=2
                    changed['features'][0]['geometry']['coordinates']=[-70.8,42.2]
                    (root/'data/input/boundaries_again.geojson').write_text(json.dumps(changed))
                    message = 'Repeat this method with the new input. Allocate fresh outputs; never reuse earlier authorization. ' + message
                attempt = {'domain':name, 'phase':phase, 'prompt':message, 'allowed_skill_ids':skills,
                           'valid_plan':False, 'executed':False, 'correct_output':False, 'human_interventions':0}
                attempt['prior_success_records']=len(inventory(root,conversation_id=chat))
                start, calls = time.monotonic(), len(metrics)
                print(f'{name}/{phase}: planning', flush=True)
                try:
                    response = conversation_turn(TurnRequest(action='turn', conversation_id=chat, expected_revision=revision,
                        message=message, allowed_skill_ids=skills), project_root=root, model_client=client)
                    revision = response['revision']
                    attempt['retrieval_receipt']=response.get('context_usage',{}).get('successful_methods')
                    proposal = response.get('planner_result')
                    if not proposal:
                        attempt['planner_message']=response.get('messages',[])[-1].get('content','') if response.get('messages') else ''
                        raise ValueError('Model returned dialogue without an executable proposal')
                    result = PlannerResult.model_validate({k:proposal[k] for k in PlannerResult.model_fields})
                    if not set(skills).issubset({s.skill for s in result.plan.steps}):
                        raise ValueError('Proposal omitted required operations')
                    expected_file=('orders' if name=='tabular' else 'boundaries')+('_again' if phase=='reuse' else '')+('.csv' if name=='tabular' else '.geojson')
                    paths=[s.arguments['path'] for s in result.plan.steps if 'path' in s.arguments]
                    if not paths or any(path!='data/input/'+expected_file for path in paths):
                        raise ValueError('Proposal did not bind the requested current input')
                    if name=='combined':
                        exported=next(s for s in result.plan.steps if s.skill=='vector_attributes_to_csv')
                        aggregated=next(s for s in result.plan.steps if s.skill=='aggregate_csv')
                        if aggregated.arguments.get('source_step')!=exported.step_id:
                            raise ValueError('Aggregation did not bind the exported attribute table')
                    attempt['source_paths']=paths
                    attempt['valid_plan'] = True
                    stored = save_interface_reviewed_plan(InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=result,
                        confirmed_plan_sha256=plan_sha256(result.plan),allowed_skill_ids=response['allowed_skill_ids']),project_root=root)
                    base = dict(plan_filename=stored['plan_filename'],confirmed_plan_sha256=stored['plan_sha256'])
                    review = prepare_workflow(WorkflowRequest(action='prepare_workflow',**base),project_root=root)
                    auth = {}
                    if review['approval_required_step_ids']:
                        auth = authorize_workflow(WorkflowRequest(action='authorize_workflow',**base,
                            confirmed_review_sha256=review['review_sha256'],approve_required_steps=True,
                            approver='synthetic-evaluation',reason='Fresh disposable fixture outputs only; no live data or service.'),project_root=root)
                    request = WorkflowRequest(action='execute_workflow',**base,confirmed_review_sha256=review['review_sha256'],confirm_execution=True,
                        plan_approval_filename=auth.get('plan_approval_filename'),recipe_approval_filename=auth.get('recipe_approval_filename'))
                    record = run_action(RunRequest(action='start',workflow=request,conversation_id=chat),project_root=root,background=False)
                    attempt.update(executed=record['execution_performed'],run_status=record['status'])
                    if record['status'] != 'completed':
                        raise ValueError('Execution failed: '+str(record.get('finding')))
                    last = record['steps'][-1]['outcome']
                    if name == 'spatial':
                        assert last['layers'][0]['feature_count'] == 3
                        assert len(last['spatial_preview']['features']) == 3
                        if phase=='reuse':
                            assert last['spatial_preview']['features'][0]['geometry']['coordinates']==[-70.8,42.2]
                    else:
                        path = root/last['output']['path']
                        with path.open() as stream:
                            rows = list(csv.DictReader(stream))
                        if name == 'tabular':
                            assert [float(row['doubled']) for row in rows] == ([40,80,20] if phase=='reuse' else [20,40,10])
                        else:
                            assert {row['region']:float(row['total_amount']) for row in rows} == ({'North':60,'South':10} if phase=='reuse' else {'North':30,'South':5})
                    attempt['correct_output'] = True
                    attempt['retained'] = bool(inventory(root,conversation_id=chat))
                    assessed = assess_run(root,record['run_id'],model_client=client)
                    attempt['critic_status'] = assessed['critic_review']['status']
                    attempt['annotation_status'] = assessed['critic_review'].get('annotation_status')
                    attempt['reused_recipe_ids'] = response.get('reused_recipe_ids', [])
                except Exception as error:
                    attempt['error'] = {'type':type(error).__name__,'code':str(getattr(error,'code','')),'finding':str(error)[:1000],'schema_findings':getattr(error,'findings',[]),'reason':getattr(error,'reason',None)}
                attempt.update(seconds=round(time.monotonic()-start,3),model_calls=len(metrics)-calls)
                report['attempts'].append(attempt)
                print(json.dumps(attempt), flush=True)
                args.output.parent.mkdir(parents=True,exist_ok=True)
                args.output.write_text(json.dumps(report,indent=2)+'\n')
    report['summary'] = {'attempts':len(report['attempts']), 'valid_plans':sum(a['valid_plan'] for a in report['attempts']),
                         'correct_executions':sum(a['correct_output'] for a in report['attempts']), 'model_calls':len(metrics),
                         'timeouts':sum(m.get('code')=='model_timeout' for m in metrics)}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary']), flush=True)
    return 0 if report['summary']['correct_executions']==(2 if args.domain else 6) else 1


if __name__ == '__main__':
    raise SystemExit(main())
