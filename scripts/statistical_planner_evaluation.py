"""Explicit installed-model acceptance in a temporary project; no downloads/live writes."""
import argparse
import json
import shutil
import tempfile
import time
from pathlib import Path

from geoagent_harness.interface_api.conversation import TurnRequest, conversation_turn
from geoagent_harness.interface_api.workflow import WorkflowRequest, prepare_workflow
from geoagent_harness.interface_api.workflow_runs import RunRequest, run_action
from geoagent_harness.model import SharedModelClient
from geoagent_harness.model.settings import ModelSettings
from geoagent_harness.tabular.analytical_service import profile_table


def execute(root, state):
    from geoagent_harness.interface_api.server import InterfaceReviewedPlanSaveRequest,save_interface_reviewed_plan
    from geoagent_harness.planner.schemas import PlannerResult
    result=state['planner_result'];sha=result['plan_sha256']
    proposal=PlannerResult.model_validate({k:result[k] for k in PlannerResult.model_fields if k in result})
    save_interface_reviewed_plan(InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=proposal,confirmed_plan_sha256=sha,allowed_skill_ids=['inspect_csv']),project_root=root)
    request=WorkflowRequest(action='prepare_workflow',conversation_id=state['conversation_id'],
        plan_filename=f'planner-plan.{sha}.json',confirmed_plan_sha256=sha)
    review=prepare_workflow(request,project_root=root)
    request=request.model_copy(update={'action':'execute_workflow','confirm_execution':True,'confirmed_review_sha256':review['review_sha256']})
    return run_action(RunRequest(action='start',workflow=request,conversation_id=state['conversation_id']),project_root=root,background=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',default='qwen3.5:9b')
    parser.add_argument('--base-url',default='http://127.0.0.1:11434/v1')
    parser.add_argument('--timeout',type=float,default=180)
    parser.add_argument('--formats-only',action='store_true',help='Evaluate XLSX/JSON Lines proposals instead of the statistical baseline')
    args=parser.parse_args()
    repo=Path(__file__).resolve().parents[1]
    client=SharedModelClient(ModelSettings(base_url=args.base_url,model=args.model,timeout_seconds=args.timeout,max_tokens=1200,reasoning_effort='none'))
    with tempfile.TemporaryDirectory(prefix='actioncharter-statistical-model-') as folder:
        root=Path(folder)
        for name in ('context','agents'):shutil.copytree(repo/name,root/name)
        (root/'data/input').mkdir(parents=True)
        (root/'data/output').mkdir()
        (root/'data/input/measures.csv').write_text('patient_nbr,x,y,region\np1,0,1,A\np1,1,3,A\np2,2,4,B\np2,3,5,B\n')
        identity='a'*32
        state=conversation_turn(TurnRequest(action='turn',conversation_id=identity,message='Inspect measures.csv. Return row count and column names. No writes.'),project_root=root,model_client=client)
        run=execute(root,state)
        assert run['status']=='completed',run['status']
        cases=[('recommendations','What statistical analysis should I do next? Suggestions only; preserve the current workflow.'),
            ('grouped_description','Compute descriptive statistics for x grouped by region in measures.csv. Use missing_policy=error. Replace the inspection with one inspect_csv analysis step. No writes. Prepare only.'),
            ('relationship','Compute Pearson correlation for x and y in measures.csv. Use missing_policy=error. Replace the current analysis with this one method. No regression or writes. Prepare only.')]
        if args.formats_only:
            from openpyxl import Workbook
            rows=[{'patient_nbr':'p1','x':0,'region':'A'},{'patient_nbr':'p1','x':1,'region':'A'},{'patient_nbr':'p2','x':2,'region':'B'},{'patient_nbr':'p2','x':3,'region':'B'}]
            book=Workbook();sheet=book.active;sheet.title='Data';sheet.append(list(rows[0]))
            for row in rows:sheet.append(list(row.values()))
            book.save(root/'data/input/measures.xlsx')
            (root/'data/input/measures.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
            cases=[('xlsx','Compute descriptive statistics for x grouped by region in measures.xlsx, worksheet Data. Set analysis.source_options.sheet to Data and statistics.missing_policy to error. Replace the inspection with one inspect_csv analysis step. No writes. Prepare only.'),
                   ('jsonl','Compute descriptive statistics for x grouped by region in measures.jsonl. This is JSON Lines, not a worksheet; omit spreadsheet source options. Use missing_policy=error. Replace the current analysis with one inspect_csv step. No writes. Prepare only.')]
        failed=False
        for name,message in cases:
            started=time.monotonic()
            try:
                before=state['planner_result']['plan_sha256']
                result=conversation_turn(TurnRequest(action='turn',conversation_id=identity,expected_revision=state['revision'],message=message),project_root=root,model_client=client)
                state=result
                if args.formats_only:
                    print(json.dumps({'case':name,'proposal_changed':result['proposal_changed'],'answer':result['messages'][-1]['content'][:1800],'arguments':result['planner_result']['plan']['steps'][0]['arguments'],'diagnostics':result.get('context_usage',{}).get('model_request')}),flush=True)
                assert not result['execution_performed'] and not result['approval_performed']
                if name=='recommendations':
                    assert result['planner_result']['plan_sha256']==before and not result['proposal_changed']
                    # Actual wording needs human assessment; this checks the mode/binding only.
                    print(json.dumps({'case':name,'advice':result['messages'][-1]['content'][:2000]}),flush=True)
                else:
                    steps=result['planner_result']['plan']['steps']
                    assert len(steps)==1 and steps[0]['skill']=='inspect_csv'
                    arguments=steps[0]['arguments'];spec=arguments['analysis']['statistics']
                    expected='data/input/measures.'+(name if name in {'xlsx','jsonl'} else 'csv')
                    assert arguments['path']==expected and spec.get('missing_policy','error')=='error'
                    if name=='xlsx':assert arguments['analysis']['source_options']['sheet']=='Data'
                    if name in {'grouped_description','xlsx','jsonl'}:assert spec['columns']==['x'] and spec['by']==['region'] and spec['methods']==['describe']
                    else:assert spec['columns']==['x','y'] and spec['methods']==['pearson']
                    # Explicit evaluation read only: no workflow dispatch for model proposals.
                    evidence=profile_table(root,arguments['path'],arguments['analysis'])['table_analysis']['statistics']
                    assert evidence['analysis_rows']==4
                    if name in {'grouped_description','xlsx','jsonl'}:assert evidence['descriptive'][0]['mean']==1.5
                    else:assert abs(evidence['correlations'][0]['coefficients'][0][1]-.9827076298239908)<1e-10
                print(json.dumps({'case':name,'status':'passed','elapsed_seconds':round(time.monotonic()-started,2),'diagnostics':result.get('context_usage',{}).get('model_request'),'proposal_executed':False}),flush=True)
            except Exception as error:
                failed=True
                print(json.dumps({'case':name,'status':'failed','error_type':type(error).__name__,'elapsed_seconds':round(time.monotonic()-started,2),'error':str(error)[:1200]}),flush=True)
                state=conversation_turn(TurnRequest(action='read',conversation_id=identity),project_root=root)
        assert not list((root/'data/output').iterdir())
        if failed:raise SystemExit(1)


if __name__=='__main__':main()
