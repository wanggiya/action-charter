"""One bounded actual-model OFF/ON/reuse evaluation; all data/authority are temporary."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from shutil import copytree,copyfile
from tempfile import TemporaryDirectory
from time import monotonic


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',required=True)
    parser.add_argument('--endpoint',default='http://127.0.0.1:11434/v1')
    parser.add_argument('--timeout',type=float,default=120)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--output',type=Path,default=Path('/tmp/actioncharter-checkpoint28-acquisition.json'))
    args=parser.parse_args()
    from geoagent_harness.model import SharedModelClient
    from geoagent_harness.model.settings import ModelSettings
    from geoagent_harness.interface_api.conversation import TurnRequest,conversation_turn
    from geoagent_harness.interface_api.server import save_interface_reviewed_plan,InterfaceReviewedPlanSaveRequest
    from geoagent_harness.interface_api.workflow import WorkflowRequest,prepare_workflow,authorize_workflow,execute_workflow
    from geoagent_harness.interface_api.workflow import validate_edit,EditRequest
    from geoagent_harness.planner.schemas import PlannerResult
    from geoagent_harness.tabular.service import read_frame
    from geoagent_harness.operations.packages import installed_packages
    repo=Path(__file__).resolve().parents[1]
    os.environ.update(ENABLE_WRITE_TOOLS='true',ALLOW_OVERWRITE='false',PLANNER_TURN_TIMEOUT_SECONDS='300')
    calls=[];client=SharedModelClient(ModelSettings(base_url=args.endpoint,model=args.model,timeout_seconds=args.timeout,max_tokens=1024,reasoning_effort='none'))
    class Counted:
        def complete(self,request):
            started=monotonic();item={'role':json.loads(request.messages[0].content).get('agent',{}).get('id','planner'),'prompt_bytes':sum(len(m.content.encode()) for m in request.messages)};calls.append(item)
            try:
                result=client.complete(request);item.update(finish_reason=result.finish_reason,prompt_tokens=result.prompt_tokens,completion_tokens=result.completion_tokens);return result
            except Exception as error:item['error_code']=getattr(error,'code',type(error).__name__);raise
            finally:item['elapsed_seconds']=round(monotonic()-started,3)
    report={'model':args.model,'scope':'temporary_synthetic_csv_only','live_database_calls':0,'threshold':{
        'off_registers_nothing':True,'on_correct_result':True,'reuse_without_candidate':True,'on_phase_model_calls_max':5},'phases':[],'calls':calls}
    counted=Counted()
    with TemporaryDirectory(prefix='actioncharter-acquisition-eval-') as directory:
        root=Path(directory)
        for name in ('agents','context'):copytree(repo/name,root/name)
        copyfile(repo/'README.md',root/'README.md');(root/'data/input').mkdir(parents=True)
        (root/'data/input/sample_orders.csv').write_text('order_id,region,amount\n001, north ,10\n002, SOUTH ,20\n003,,5\n')
        (root/'data/input/changed_orders.csv').write_text('order_id,region,amount\n007, east ,50\n008, West ,60\n')
        request='Inspect sample_orders.csv. Trim whitespace and uppercase region into a new region_clean column, preserve all original columns, and save a fresh CSV. Do not execute.'
        def turn(identity,revision,message):return conversation_turn(TurnRequest(action='turn',conversation_id=identity,expected_revision=revision,message=message),project_root=root,model_client=counted,critic_client=counted)
        def execute(result):
            plan=PlannerResult.model_validate({k:v for k,v in result['planner_result'].items() if k in PlannerResult.model_fields})
            assert all(step.skill in {'inspect_csv','export_csv',candidate['operation_id']} for step in plan.plan.steps), 'Unexpected operation; no execution attempted'
            assert sum(step.skill==candidate['operation_id'] for step in plan.plan.steps)==1
            validation=validate_edit(EditRequest(action='validate_plan_edit',planner_result=plan),project_root=root)
            saved=save_interface_reviewed_plan(InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=plan,confirmed_plan_sha256=validation['plan_sha256'],allowed_skill_ids=validation['allowed_skill_ids']),project_root=root)
            base={'plan_filename':saved['plan_filename'],'confirmed_plan_sha256':saved['plan_sha256']}
            review=prepare_workflow(WorkflowRequest(action='prepare_workflow',**base),project_root=root)
            auth=authorize_workflow(WorkflowRequest(action='authorize_workflow',**base,confirmed_review_sha256=review['review_sha256'],approve_required_steps=True,approver='temporary-evaluation',reason='Only temporary synthetic fixture outputs'),project_root=root)
            outcome=execute_workflow(WorkflowRequest(action='execute_workflow',**base,confirmed_review_sha256=review['review_sha256'],confirm_execution=True,plan_approval_filename=auth['plan_approval_filename'],recipe_approval_filename=auth['recipe_approval_filename']),project_root=root)
            assert outcome['status']=='validated_success'
            generated=next(step['outcome'] for step in outcome['step_results'] if step['skill_id'].startswith('ext_text_'))
            actual=read_frame((root/generated['output']['path']).read_bytes())
            source=read_frame((root/generated['sources'][0]['path']).read_bytes())
            assert list(actual.columns)==[*source.columns,'region_clean'] and actual[list(source.columns)].equals(source)
            assert actual['region_clean'].fillna('').tolist()==source['region'].fillna('').str.strip().str.upper().tolist()
            return {'status':'correct','row_count':len(actual),'source':generated['sources'][0]['path'],'output':generated['output']['path']}
        if not args.prepare_only:
            phase={'phase':'OFF'};report['phases'].append(phase)
            try:
                result=turn('a'*32,0,request)
                assert result['capability_candidate'] is None and not installed_packages(root)
                proposed=result['planner_result']
                phase.update(status='no_capability_registered',proposal_skills=[step['skill'] for step in proposed['plan']['steps']] if proposed else [],model_calls=len(calls))
            except Exception as error:phase.update(status='failed',error_code=getattr(error,'code',type(error).__name__),finding=str(error)[:400],schema_findings=getattr(error,'findings',[]))
        identity='b'*32;phase={'phase':'ON'};report['phases'].append(phase);before=len(calls)
        try:
            enabled=conversation_turn(TurnRequest(action='configure_acquisition',conversation_id=identity,acquisition_enabled=True),project_root=root)
            result=turn(identity,enabled['revision'],request)
            phase['planner_diagnostics']=result['context_usage']['model_request']
            phase['planner_message']=result['messages'][-1]['content'][:1000]
            candidate=result['capability_candidate'];assert candidate and candidate['status']=='tested', 'Candidate not eligible: '+str(candidate.get('critic') if candidate else phase['planner_message'])
            assert not installed_packages(root) and not list((root/'data').glob('output/*.csv'))
            phase['preparation_budget']=result['context_usage']['effort_budget'];phase['critic']=candidate['critic'];phase['tests']=candidate['tests']
            if args.prepare_only:
                phase.update(status='prepared',model_calls=len(calls)-before)
                report.update(passed=True,scope='preparation_only',threshold={'tested_candidate':True})
                args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'scope':'preparation_only','report':str(args.output)}));return 0
            installed=conversation_turn(TurnRequest(action='install_capability',conversation_id=identity,expected_revision=result['revision'],confirmed_candidate_sha256=candidate['candidate_sha256']),project_root=root)
            assert not list((root/'data').glob('output/*.csv'))
            continuation=f"Use registered operation {candidate['operation_id']} to complete this exact workflow, without new acquisition: {request}"
            result=turn(identity,installed['revision'],continuation)
            phase.update(execute(result));phase['model_calls']=len(calls)-before
            assert phase['model_calls']<=5
            phase={'phase':'reuse_changed_input_OFF'};report['phases'].append(phase);before=len(calls)
            result=turn('c'*32,0,request.replace('sample_orders.csv','changed_orders.csv'))
            assert not result['acquisition_enabled'] and result['capability_candidate'] is None
            phase.update(execute(result));phase['model_calls']=len(calls)-before
        except Exception as error:phase.update(status='failed',error_code=getattr(error,'code',type(error).__name__),finding=str(error)[:400],schema_findings=getattr(error,'findings',[]),diagnostics=getattr(error,'planner_diagnostics',None))
    report['passed']=len(report['phases'])==3 and [p.get('status') for p in report['phases']]==['no_capability_registered','correct','correct']
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'phases':[{k:v for k,v in p.items() if k not in {'tests','critic','preparation_budget'}} for p in report['phases']],'model_calls':len(calls),'report':str(args.output)},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
