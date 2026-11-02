"""Bounded real-model mode comparison on a full CSV copy; no database connections.

Proposes and executes one row-preserving preparation through normal exact approval,
then requests an outcome review. This is not certification of arbitrary full workflows.
"""
import argparse,csv,hashlib,json,os,shutil,tempfile,time
from pathlib import Path
from geoagent_harness.model import SharedModelClient
from geoagent_harness.model.settings import ModelSettings
from geoagent_harness.interface_api.conversation import TurnRequest,conversation_turn
from geoagent_harness.interface_api.workflow_runs import RunRequest,run_action
from geoagent_harness.interface_api.workflow import WorkflowRequest,prepare_workflow,authorize_workflow
from geoagent_harness.interface_api import server as api
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.approvals import plan_sha256
from geoagent_harness.write_policy import session


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--columns',required=True);p.add_argument('--model',default='qwen3.5:9b')
    p.add_argument('--mode',choices=['single','three'],required=True);p.add_argument('--timeout',type=float,default=120)
    p.add_argument('--base-url',default='http://127.0.0.1:11434/v1');args=p.parse_args()
    before=hashlib.sha256(args.source.read_bytes()).hexdigest();columns=args.columns.split(',');started=time.monotonic()
    with args.source.open(newline='') as f:expected=sum(1 for _ in csv.DictReader(f))
    client=SharedModelClient(ModelSettings(base_url=args.base_url,model=args.model,timeout_seconds=args.timeout,max_tokens=1200,reasoning_effort='none'))
    with tempfile.TemporaryDirectory(prefix='actioncharter-agent-mode-') as folder:
        root=Path(folder);repo=Path(__file__).resolve().parents[1]
        for name in ('context','agents'):shutil.copytree(repo/name,root/name)
        (root/'data/input').mkdir(parents=True);(root/'data/output').mkdir();shutil.copyfile(args.source,root/'data/input/source.csv')
        old=os.environ.copy()
        try:
            os.environ.update(GEOAGENT_PROJECT_ROOT=str(root),ENABLE_WRITE_TOOLS='true',MODEL_NAME=args.model,
                              MODEL_BASE_URL=args.base_url,MODEL_REASONING_EFFORT='none',MODEL_TIMEOUT_SECONDS=str(args.timeout),MODEL_MAX_TOKENS='1200')
            for key,suffix in {'INPUT':'data/input','OUTPUT':'data/output','TRACE':'traces','REPORT':'reports','PLAN':'plans','APPROVAL':'approvals','STATE':'workflow-state','RECIPE':'workflow-recipes','RECIPE_RUN':'recipe-runs','RECIPE_EVIDENCE':'recipe-evidence','SPATIAL_CONTRACT':'spatial-contracts'}.items():os.environ['GEOAGENT_'+key+'_ROOT']=str(root/suffix)
            with session(root,enabled=True):
                state=conversation_turn(TurnRequest(action='turn',conversation_id='a'*32,agent_mode=args.mode,allowed_skill_ids=['select_csv_columns'],
                    message='Select columns '+', '.join(columns)+' from source.csv. Preserve every record and textual identifiers. This is the full source, not a sample. Prepare one CSV operation with qualified streaming preparation; prepare only.'),project_root=root,model_client=client)
                result=state['planner_result'];assert result is not None,'Model did not propose a workflow'
                plan=PlannerResult.model_validate({k:result[k] for k in PlannerResult.model_fields if k in result})
                assert len(plan.plan.steps)==1 and plan.plan.steps[0].skill=='select_csv_columns'
                assert plan.plan.steps[0].arguments['columns']==columns and plan.plan.steps[0].arguments.get('streaming') is True
                saved=api.save_interface_reviewed_plan(api.InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=plan,confirmed_plan_sha256=plan_sha256(plan.plan),allowed_skill_ids=['select_csv_columns']),project_root=root)
                req=WorkflowRequest(action='prepare_workflow',conversation_id='a'*32,plan_filename=saved['plan_filename'],confirmed_plan_sha256=saved['plan_sha256'])
                review=prepare_workflow(req,project_root=root)
                approved=authorize_workflow(req.model_copy(update={'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,'approver':'temporary-acceptance','reason':'Only a full CSV copy and generated output in the temporary evaluation project.'}),project_root=root)
                assert not list((root/'data/output').iterdir())
                req=req.model_copy(update={'action':'execute_workflow','confirm_execution':True,'confirmed_review_sha256':review['review_sha256'],'plan_approval_filename':approved['plan_approval_filename'],'recipe_approval_filename':approved['recipe_approval_filename']})
                run=run_action(RunRequest(action='start',workflow=req,conversation_id='a'*32),project_root=root,background=False)
                assert run['status']=='completed',run.get('finding')
                outcome=run['steps'][0]['outcome'];assert outcome['row_count']==expected
                with (root/outcome['output']['path']).open(newline='') as f:
                    rows=csv.DictReader(f);assert rows.fieldnames==columns
                    with args.source.open(newline='') as original:
                        expected_rows=csv.DictReader(original)
                        for got,wanted in zip(rows,expected_rows,strict=True):assert got=={k:wanted[k] for k in columns}
                coordination=state.get('agent_coordination') or {};review=run.get('agent_report') or {}
                advisory=bool(review.get('assessment',{}).get('assessment')) and all(r.get('status')=='complete' for r in coordination.get('reviews',[]))
                print(json.dumps({'status':'passed' if advisory else 'partial','execution_status':'passed',
                    'scope':'one full-file selection; not the complete database workflow','advisory_reviews_complete':advisory,
                    'mode':args.mode,'model':args.model,'rows':expected,'planning_calls':coordination.get('model_calls'),
                    'planning_metrics':coordination.get('metrics'),'outcome_assessment':review.get('assessment'),
                    'outcome_metrics':review.get('metrics'),'elapsed_seconds':round(time.monotonic()-started,3),
                    'database_connections':0,'original_unchanged':before==hashlib.sha256(args.source.read_bytes()).hexdigest()},default=str),flush=True)
        except Exception as error:
            print(json.dumps({'status':'failed','mode':args.mode,'code':getattr(error,'code',type(error).__name__),'finding':str(error)[:1000],
                              'diagnostics':getattr(error,'planner_diagnostics',None),'elapsed_seconds':round(time.monotonic()-started,3),'database_connections':0}),flush=True)
            raise SystemExit(1)
        finally:
            os.environ.clear();os.environ.update(old)
            assert before==hashlib.sha256(args.source.read_bytes()).hexdigest()

if __name__=='__main__':main()
