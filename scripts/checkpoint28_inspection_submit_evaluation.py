"""Single local-model submit acceptance; synthetic temporary data, not a benchmark."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from time import monotonic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--sequence',action='store_true',help='Vector → raster in one chat, then typed display, recorded explanation and CSV')
    parser.add_argument('--kind', choices=['csv','vector','raster'], default='csv')
    parser.add_argument('--endpoint', default='http://127.0.0.1:11434/v1')
    parser.add_argument('--timeout', type=float, default=90)
    parser.add_argument('--output', type=Path, default=Path('/tmp/actioncharter-checkpoint28-inspection-submit.json'))
    args = parser.parse_args()
    if args.sequence:args.kind='vector'
    from geoagent_harness.interface_api.conversation import TurnRequest
    from geoagent_harness.interface_api.planner_submission import SubmissionRequest, submission_action
    from geoagent_harness.model import SharedModelClient
    from geoagent_harness.model.settings import ModelSettings
    repo = Path(__file__).resolve().parents[1]
    client = SharedModelClient(ModelSettings(base_url=args.endpoint, model=args.model,
        timeout_seconds=args.timeout, max_tokens=1024, reasoning_effort='none', response_format='json_schema'))
    class Measured:
        def __init__(self):
            self.calls = []
        def complete(self, request):
            item = {'prompt_bytes': sum(len(message.content.encode()) for message in request.messages)}
            self.calls.append(item)
            started = monotonic()
            try:
                result = client.complete(request)
                item.update(completion_tokens=result.completion_tokens, finish_reason=result.finish_reason)
                if args.sequence:
                    try:item['reply']=json.loads(result.content)
                    except ValueError:item['reply_shape']='not_json'
                return result
            finally:
                item['seconds'] = round(monotonic() - started, 3)
    measured = Measured()
    report = {'model': args.model, 'scope': 'synthetic_same_chat_vector_raster_display_facts_csv' if args.sequence else f'one_temporary_{args.kind}_acceptance_not_benchmark',
              'live_database_calls': 0, 'model_training': False, 'model_calls': measured.calls, 'status': 'failed'}
    started = monotonic()
    with TemporaryDirectory(prefix='actioncharter-submit-acceptance-') as directory:
        root = Path(directory)
        for name in ('context', 'agents'):
            copytree(repo / name, root / name)
        (root / 'README.md').write_text((repo / 'README.md').read_text())
        (root / 'data/input').mkdir(parents=True)
        (root / 'data/input/orders.csv').write_text('order_id,region,amount\n001,North,10\n002,South,20\n003,North,5\n')
        if args.kind == 'vector':
            (root / 'data/input/points.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[
                {'type':'Feature','properties':{'id':1},'geometry':{'type':'Point','coordinates':[1,2]}}]}))
        if args.kind == 'raster' or args.sequence:
            import numpy as np
            import rasterio
            from rasterio.transform import from_origin
            with rasterio.open(root/'data/input/dem.tif','w',driver='GTiff',width=4,height=3,count=1,dtype='uint8',crs='EPSG:4326',transform=from_origin(1,4,1,1)) as dataset:
                dataset.write(np.ones((1,3,4),dtype='uint8'))
        message = {'csv':'Inspect orders.csv. Return row count and column names. No writes.',
                   'vector':'Inspect points.geojson. Return feature count, fields and CRS. No writes.',
                   'raster':'Inspect dem.tif. Return CRS. No writes.'}[args.kind]
        request = SubmissionRequest(action='submit', submission_id='d'*32, conversation_id='c'*32,
            inspect_on_send=True, turn=TurnRequest(action='turn', conversation_id='c'*32,
                message=message))
        try:
            response = submission_action(request, project_root=root, model_client=measured, background=False)
            run = response['run']
            assert run and run['status'] == 'completed', response['submission']['finding']
            assert len(run['steps']) == 1 and run['steps'][0]['skill_id'] == {'csv':'inspect_csv','vector':'inspect_vector','raster':'inspect_raster'}[args.kind]
            outcome = run['steps'][0]['outcome']
            if args.kind == 'csv':
                assert outcome['row_count'] == 3 and outcome['columns'] == ['order_id', 'region', 'amount']
            elif args.kind == 'vector':
                assert outcome['layers'][0]['feature_count'] == 1 and outcome['layers'][0]['crs'] == 'EPSG:4326'
            else:
                assert (outcome['width'],outcome['height'],outcome['band_count'],outcome['crs']) == (4,3,1,'EPSG:4326')
            count = len(measured.calls)
            repeated = submission_action(request, project_root=root, model_client=measured, background=False)
            assert repeated['run']['run_id'] == run['run_id'] and len(measured.calls) == count
            assert not (root / 'data/output').exists() and not (root / 'approvals').exists()
            if args.sequence:
                second=SubmissionRequest(action='submit',submission_id='e'*32,conversation_id='c'*32,inspect_on_send=True,
                    turn=TurnRequest(action='turn',conversation_id='c'*32,expected_revision=response['conversation']['revision'],
                                     message='Inspect dem.tif. Return dimensions, bands, bounds and CRS. No writes.'))
                raster=submission_action(second,project_root=root,model_client=measured,background=False)
                assert raster['run']['status']=='completed' and raster['run']['steps'][0]['outcome']['source']=='data/input/dem.tif'
                from geoagent_harness.interface_api.conversation import conversation_turn
                from geoagent_harness.interface_api.workflow_runs import RunRequest,run_action
                spec_reply=conversation_turn(TurnRequest(action='turn',conversation_id='c'*32,expected_revision=raster['conversation']['revision'],
                    message='Display band 1 as a color ramp.'),project_root=root,model_client=measured)
                spec=spec_reply['context_usage']['result_view']
                assert spec and spec['spatial']['mode']=='raster' and spec['spatial']['bands']==[1] and spec['spatial']['render']=='ramp'
                view=run_action(RunRequest(action='spatial_view',run_id=spec['run_id'],conversation_id='c'*32,
                    confirmed_plan_sha256=spec['plan_sha256'],step_id=spec['step_id'],spatial=spec['spatial']),project_root=root)
                assert view['kind']=='raster'
                explained=conversation_turn(TurnRequest(action='turn',conversation_id='c'*32,expected_revision=spec_reply['revision'],
                    message='Explain the current result dimensions and band count.'),project_root=root,model_client=measured)
                assert {'width','height','band_count'}.issubset(explained['context_usage']['result_view']['explanation_fields'])
                assert 'saved inspection evidence' in explained['messages'][-1]['content']
                assert explained['planner_result']==raster['conversation']['planner_result']
                assert len(list((root/'workflow-state/interface-runs').glob('*.json')))==2
                third=SubmissionRequest(action='submit',submission_id='f'*32,conversation_id='c'*32,inspect_on_send=True,
                    turn=TurnRequest(action='turn',conversation_id='c'*32,expected_revision=explained['revision'],
                                     message='Inspect orders.csv. Return row count and column names. No writes.'))
                csv=submission_action(third,project_root=root,model_client=measured,background=False)
                assert csv['run']['status']=='completed'
                assert csv['run']['steps'][0]['skill_id']=='inspect_csv'
                assert csv['run']['steps'][0]['outcome']['row_count']==3
                assert csv['run']['steps'][0]['outcome']['source']=='data/input/orders.csv'
                assert len(list((root/'workflow-state/interface-runs').glob('*.json')))==3
                assert not (root/'data/output').exists() and not (root/'approvals').exists()
                report.update(csv_transition=True)
                report.update(same_chat_transition=True,typed_raster_display=True,recorded_explanation=True,explanation_model_calls=explained['context_usage']['model_request'].get('model_calls'),explanation_fields=explained['context_usage']['result_view']['explanation_fields'],display_and_explanation_processing_runs=0)
            report.update(status='passed', kind=args.kind, verified_metadata=True,
                          duplicate_reused_same_run=True, approval_performed=False, dataset_writes=0)
        except Exception as error:
            report.update(failure_type=type(error).__name__, finding=str(error), retry_performed=False)
    report['seconds'] = round(monotonic() - started, 3)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if report['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
