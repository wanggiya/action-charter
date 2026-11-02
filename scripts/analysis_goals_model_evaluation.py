"""Evaluate goal advice from saved aggregate metadata, never data rows or execution."""
import argparse,csv,json,shutil,tempfile
from pathlib import Path
from geoagent_harness.interface_api import conversation,result_exploration
from geoagent_harness.model import SharedModelClient
from geoagent_harness.model.settings import ModelSettings
from geoagent_harness.model.telemetry import read,error_code


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--conversation-id',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 repo=Path(__file__).resolve().parents[1]
 original=conversation._read(conversation._path(repo,args.conversation_id),args.conversation_id)
 context=result_exploration.view_context(repo,args.conversation_id,original.planner_result,goal_schema=True)
 if not context:raise SystemExit('No saved matching inspection metadata')
 with tempfile.TemporaryDirectory(prefix='actioncharter-goal-evaluation-') as directory:
  root=Path(directory)
  for name in ('context','agents'):shutil.copytree(repo/name,root/name)
  # Header-only stand-ins satisfy proposal path-existence checks. Saved metadata
  # remains historical; these files are never inspected or sent to the model.
  from geoagent_harness.discovery.source import relative_path
  for step in original.planner_result.plan.steps:
   path=step.arguments.get('path')
   if path:
    target=root/relative_path(path,'input');target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('w',newline='') as f:csv.writer(f).writerow([v['name'] for v in context['results'][0]['field_guidance']['field_evidence']])
  identity='a'*32
  seeded=conversation.Conversation(conversation_id=identity,planner_result=original.planner_result)
  conversation._write(conversation._path(root,identity),seeded)
  lookup=result_exploration.view_context
  result_exploration.view_context=lambda *a,**k:context
  invalid_fields=[]
  try:
   client=SharedModelClient(ModelSettings(base_url='http://127.0.0.1:11434/v1',model='qwen3.5:9b',timeout_seconds=120,max_tokens=1200,reasoning_effort='none'))
   complete=client.complete
   def observed_complete(request):
    response=complete(request)
    try:conversation.AnalysisGoalsReply.model_validate_json(response.content)
    except Exception as error:
     if hasattr(error,'errors'):invalid_fields.append([{'path':list(e['loc']),'type':e['type']} for e in error.errors(include_input=False,include_context=False)])
    return response
   client.complete=observed_complete
   state=conversation.conversation_turn(conversation.TurnRequest(action='turn',conversation_id=identity,message='Propose analysis goals from the recorded inspection. Let the agent prioritize useful scientific questions, applicable metrics and prerequisites. Suggestions only; preserve the current workflow.'),project_root=root,model_client=client)
   goals=state['context_usage'].get('analysis_goals')
   from geoagent_harness.approvals import plan_sha256
   assert goals and state['planner_result']['plan_sha256']==plan_sha256(original.planner_result.plan)
   result={'status':'passed','scope':'temporary saved-metadata and header-only fixture','goals':goals,'diagnostics':read(root,identity),'execution_performed':False}
  except Exception as error:result={'status':'failed','error_code':error_code(error),'schema_findings':getattr(error,'findings',[]),'invalid_reply_fields':invalid_fields,'diagnostics':read(root,identity),'execution_performed':False}
  finally:result_exploration.view_context=lookup
  with args.output.open('x') as f:json.dump(result,f,indent=2)
  print(json.dumps({'status':result['status'],'methods':[g['method'] for g in (result.get('goals') or {}).get('goals',[])],'execution_performed':False}))

if __name__=='__main__':main()
