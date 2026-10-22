"""One installed-model result-view acceptance on temporary synthetic data."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from time import monotonic


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',required=True)
    parser.add_argument('--case',choices=['chart','raster','explanation'],default='chart')
    parser.add_argument('--endpoint',default='http://127.0.0.1:11434/v1')
    parser.add_argument('--timeout',type=float,default=90)
    parser.add_argument('--output',type=Path,default=Path('/tmp/actioncharter-checkpoint28-result-view.json'))
    args=parser.parse_args()
    from geoagent_harness.model import SharedModelClient
    from geoagent_harness.model.settings import ModelSettings
    from geoagent_harness.model.schemas import ModelResult
    from geoagent_harness.interface_api.conversation import TurnRequest,conversation_turn
    from geoagent_harness.interface_api.planner_submission import SubmissionRequest,submission_action
    from geoagent_harness.interface_api.workflow_runs import RunRequest,run_action
    from geoagent_harness.interface_api.exploration_contracts import ResultViewSpec
    model=SharedModelClient(ModelSettings(base_url=args.endpoint,model=args.model,timeout_seconds=args.timeout,
        max_tokens=1024,reasoning_effort='none',response_format='json_schema'))
    class Seed:
        def complete(self,request):
            if args.case!='chart':
                return ModelResult(model='fixture seed only',content=json.dumps({'message':'Inspect raster','plan':{'summary':'Inspect raster','steps':[{'step_id':'step_1','skill':'inspect_raster','purpose':'Inspect','arguments':{'path':'dem.tif'}}]}}))
            return ModelResult(model='fixture seed only',content=json.dumps({'message':'Inspect fixture.','plan':{
                'summary':'Inspect orders','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect CSV','arguments':{'path':'orders.csv'}}]}}))
    class Measured:
        def __init__(self):self.calls=[]
        def complete(self,request):
            item={'prompt_bytes':sum(len(message.content.encode()) for message in request.messages)}
            self.calls.append(item);started=monotonic()
            try:
                response=model.complete(request)
                item.update(completion_tokens=response.completion_tokens,finish_reason=response.finish_reason)
                try:item['reply']=json.loads(response.content)
                except ValueError:item['reply_shape']='not_json'
                return response
            finally:item['seconds']=round(monotonic()-started,3)
    measured=Measured();started=monotonic()
    report={'status':'failed','model':args.model,'model_calls':measured.calls,
            'scope':'one_synthetic_result_view_acceptance_not_benchmark','live_database_calls':0,'model_training':False}
    repo=Path(__file__).resolve().parents[1]
    with TemporaryDirectory(prefix='actioncharter-result-view-') as directory:
        root=Path(directory)
        for name in ('agents','context'):copytree(repo/name,root/name)
        (root/'README.md').write_text((repo/'README.md').read_text())
        (root/'data/input').mkdir(parents=True)
        source=root/'data/input/orders.csv'
        content='order_id,region,amount\n001,North,10\n002,North,20\n003,South,5\n'
        source.write_text(content)
        if args.case!='chart':
            import numpy as np
            import rasterio
            from rasterio.transform import from_origin
            with rasterio.open(root/'data/input/dem.tif','w',driver='GTiff',width=4,height=3,count=1,dtype='uint8',crs='EPSG:4326',transform=from_origin(1,4,1,1)) as dataset:
                dataset.write(np.ones((1,3,4),dtype='uint8'))

        try:
            seed=submission_action(SubmissionRequest(action='submit',submission_id='d'*32,conversation_id='c'*32,
                inspect_on_send=True,turn=TurnRequest(action='turn',conversation_id='c'*32,
                message='Inspect orders.csv. Return row count and column names. No writes.' if args.case=='chart' else 'Inspect dem.tif. Return dimensions, bands, bounds and CRS. No writes.')),
                project_root=root,model_client=Seed(),background=False)
            assert seed['run']['status']=='completed'
            response=conversation_turn(TurnRequest(action='turn',conversation_id='c'*32,expected_revision=1,
                message={'chart':'Show total amount by region as a bar chart.','raster':'Display band 1 as a color ramp.','explanation':'Explain the current result dimensions and band count.'}[args.case]),project_root=root,model_client=measured)
            assert not response['proposal_changed'] and response['planner_result']==seed['conversation']['planner_result']
            report['planner_reply']={'message':response['messages'][-1]['content'][:600],'has_result_view':response['context_usage'].get('result_view') is not None}
            spec=ResultViewSpec.model_validate(response['context_usage']['result_view'])
            if args.case=='chart':
                assert spec.view=='Chart' and spec.chart_kind=='bar'
                assert spec.chart.group_by=='region' and spec.chart.value=='amount' and spec.chart.aggregation=='sum'
                result=run_action(RunRequest(action='explore',run_id=spec.run_id,conversation_id='c'*32,
                    confirmed_plan_sha256=spec.plan_sha256,step_id=spec.step_id,query=spec.query,analysis=spec.chart),project_root=root)
                assert result['chart_analysis']['preview']==[{'category':'North','value':30.0},{'category':'South','value':5.0}]
            elif args.case=='raster':
                assert spec.view=='Map' and spec.spatial and spec.spatial.bands==[1] and spec.spatial.render=='ramp'
                result=run_action(RunRequest(action='spatial_view',run_id=spec.run_id,conversation_id='c'*32,confirmed_plan_sha256=spec.plan_sha256,step_id=spec.step_id,spatial=spec.spatial),project_root=root)
                assert result['kind']=='raster'
            else:
                assert {'width','height','band_count'}.issubset(spec.explanation_fields)
                assert 'Source width (pixels): 4.' in response['messages'][-1]['content']
            assert len(list((root/'workflow-state/interface-runs').glob('*.json')))==1
            assert not (root/'approvals').exists() and not (root/'data/output').exists() and source.read_text()==content
            report.update(status='passed',workflow_preserved=True,additional_workflow_runs=0,case=args.case,verified_result=True,dataset_writes=0)
        except Exception as error:
            report.update(failure_type=type(error).__name__,findings=getattr(error,'findings',[])[:3])
    report['seconds']=round(monotonic()-started,3)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if report['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
