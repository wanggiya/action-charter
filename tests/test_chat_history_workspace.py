"""Snapshots, read-only historical outcomes, fresh drafts and persistent terminal control."""
import json
from pathlib import Path
from shutil import copytree
import pytest
from geoagent_harness.interface_api.conversation import Conversation,TurnRequest,conversation_turn
from geoagent_harness.interface_api.planning_tasks import write_turn,conversation_record,database
from geoagent_harness.interface_api.chat_history import HistoryRequest,history_action
from geoagent_harness.interface_api.planner_submission import SubmissionRequest,submission_action
from geoagent_harness.chat.workspace import Workspace,terminal_text
from geoagent_harness.tabular.dataset_service import profile_dataset
from geoagent_harness.tabular.dataset_views import DatasetViewRequest,dataset_view

ID='d'*32
@pytest.fixture
def root(tmp_path,monkeypatch):
 repo=Path(__file__).parents[1]
 for name in ['context','agents']:copytree(repo/name,tmp_path/name)
 (tmp_path/'README.md').write_text((repo/'README.md').read_text())
 (tmp_path/'data/input').mkdir(parents=True)
 for name in ['sample_orders.csv','sample_points.geojson']:(tmp_path/'data/input'/name).write_bytes((repo/'data/input'/name).read_bytes())
 monkeypatch.setenv('ACTIONCHARTER_ANALYTICAL_RUNTIME','local')
 return tmp_path

def turn(root,identity,message,revision=0):
 import uuid
 return submission_action(SubmissionRequest(action='submit',submission_id=uuid.uuid4().hex,conversation_id=identity,turn=TurnRequest(action='turn',conversation_id=identity,expected_revision=revision,message=message)),project_root=root,background=False)['conversation']

def history(root,action='list',**kw):return history_action(HistoryRequest(action=action,conversation_id=ID,**kw),project_root=root)

def test_versions_are_immutable_scoped_and_restore_new_draft_without_authority(root):
 first=turn(root,ID,'Inspect sample_orders.csv.')
 old=history(root)['entries'][0]
 second=turn(root,ID,'Inspect sample_orders.csv. Return row count and column names. No writes.',1)
 entries=history(root)['entries'];assert {e['revision'] for e in entries}=={1,2}
 read=history(root,'read',entry_id=old['id'])
 assert read['planner_result']==first['planner_result'] and not read['execution_performed']
 assert conversation_record(root,ID)['revision']==2
 with pytest.raises(ValueError):history(root,'continue',entry_id=old['id'],expected_revision=1)
 restored=history(root,'continue',entry_id=old['id'],expected_revision=2)['conversation']
 assert restored['task_revision']==restored['revision']==3 and len(restored['messages'])==len(second['messages'])+2
 assert restored['planner_result']['plan']==first['planner_result']['plan']
 assert not restored['approval_performed'] and not restored['execution_performed']
 assert 3 in [e['revision'] for e in history(root)['entries']]
 assert history(root,'read',entry_id=old['id'])['planner_result']==read['planner_result']
 with pytest.raises(ValueError):history_action(HistoryRequest(action='read',conversation_id='e'*32,entry_id=old['id']),project_root=root)
 assert not (root/'approvals').exists() and not (root/'inspection-runs').exists()


def test_analysis_and_interactive_view_snapshots_survive_later_changes(root):
 p=profile_dataset(root,'sample_orders.csv',owner=ID)
 session={'directory':'data/input','status':'completed','message':'Original analysis','observations':[{'tool':'profile_table','result':{'dataset_profile':p}}],'journal':[],'inventory':{'files':[]},'model_calls':0,'tool_calls':1,'elapsed_seconds':0,'data_written':False,'workflow_changed':False}
 state=Conversation(conversation_id=ID,revision=1,analytical_session=session)
 write_turn(root,state.model_dump(mode='json'),expected_revision=0,expected_task_revision=0)
 analysis=history(root)['entries'][0]
 request=DatasetViewRequest(action='calculate',conversation_id=ID,expected_revision=1,source_sha256=p['source_sha256'],profile_sha256=p['artifact']['sha256'],columns=['region'])
 view=dataset_view(request,project_root=root)['result']
 entry=next(e for e in history(root)['entries'] if e['kind']=='view')
 dataset_view(request.model_copy(update={'columns':['category']}),project_root=root) if 'category' in p['columns'] else None
 recorded=history(root,'read',entry_id=entry['id'])
 assert recorded['view']==view
 restored=history(root,'continue',entry_id=entry['id'],expected_revision=1)['conversation']
 assert restored['revision']==restored['task_revision']==2
 assert restored['context_usage']['model_request']['stage']=='analytical_history_restore'
 active=dataset_view(request.model_copy(update={'action':'read','expected_revision':2}),project_root=root)['result']
 assert active['groups']==view['groups'] and active['revision']==2
 assert history(root,'read',entry_id=analysis['id'])['analytical_session']==session
 with database(root) as db:
  assert db.execute('SELECT COUNT(*) FROM chat_history_blobs_v1 WHERE sha=?',(recorded['entry']['analytical_session'],)).fetchone()[0]==1


def test_digest_corruption_and_unknown_run_are_rejected(root):
 turn(root,ID,'Inspect sample_orders.csv.')
 entry=history(root)['entries'][0]
 with database(root,write=True) as db:
  e=json.loads(db.execute('SELECT value FROM chat_history_v1 WHERE id=?',(entry['id'],)).fetchone()[0]);db.execute('UPDATE chat_history_blobs_v1 SET value=? WHERE sha=?',('{}',e['planner_result']))
 with pytest.raises(ValueError,match='digest'):history(root,'read',entry_id=entry['id'])
 with pytest.raises(ValueError):history(root,'read',entry_id='run:'+'f'*32)


class LocalClient:
 url='http://127.0.0.1:8765'
 def __init__(self,root):self.root=root
 def conversation(self,action,identity):return conversation_turn(TurnRequest(action=action,conversation_id=identity),project_root=self.root)
 def post(self,path,payload):
  if path=='/api/v1/chat/history':return history_action(HistoryRequest.model_validate(payload),project_root=self.root)
  if path=='/api/v1/analysis/view':return dataset_view(DatasetViewRequest.model_validate(payload),project_root=self.root)
  raise AssertionError(path)
 def send(self,identity,message,expected_revision,submission_id):
  r=submission_action(SubmissionRequest(action='submit',submission_id=submission_id,conversation_id=identity,turn=TurnRequest(action='turn',conversation_id=identity,expected_revision=expected_revision,message=message)),project_root=self.root,background=False)
  return r


def test_persistent_workspace_chat_history_and_no_send_in_historical_mode(root):
 w=Workspace(LocalClient(root),ID);w.refresh()
 assert 'inspect_csv' in w.execute('Inspect sample_orders.csv.')
 assert w.state['revision']==1 and w.pending_receipt is None
 assert 'workflow' in w.execute('/history')
 assert 'HISTORICAL' in w.execute('/view 1')
 with pytest.raises(ValueError):w.execute('Inspect sample_orders.csv.')
 assert w.state['revision']==1
 assert 'new draft' in w.execute('/continue 1') and w.state['revision']==2
 assert 'Chat' in w.execute('/current')
 assert '/open' in w.execute('/help')
 assert ID in w.execute('/chats')
 assert 'Chat' in w.execute('/open 1')
 assert w.execute('/quit')=='__QUIT__'
 assert '\x1b' not in terminal_text('line\n\x1b]52;clipboard\x07')


def test_run_history_is_scoped_without_restarting(root):
 turn(root,ID,'Inspect sample_orders.csv.')
 directory=root/'workflow-state/interface-runs';directory.mkdir(parents=True)
 run={'run_id':'1'*32,'conversation_id':ID,'status':'completed','started_at':'2026-10-25T12:00:00+00:00','finished_at':'2026-10-25T12:01:00+00:00','plan_sha256':'0'*64,'steps':[]}
 (directory/(run['run_id']+'.json')).write_text(json.dumps(run))
 foreign={**run,'run_id':'2'*32,'conversation_id':'e'*32}
 (directory/(foreign['run_id']+'.json')).write_text(json.dumps(foreign))
 listed=history(root)['entries'];assert any(e['id']=='run:'+'1'*32 for e in listed)
 assert not any(e['id']=='run:'+'2'*32 for e in listed)
 assert history(root,'read',entry_id='run:'+'1'*32)['run']==run
 with pytest.raises(ValueError):history(root,'read',entry_id='run:'+'2'*32)
 with pytest.raises(ValueError):history(root,'continue',entry_id='run:'+'1'*32,expected_revision=1)


def test_terminal_explicit_execution_respects_write_authority_and_uncertain_dispatch():
 from geoagent_harness.chat.client import ChatError
 class Client:
  url='http://127.0.0.1:8765'
  def __init__(self):self.calls=[];self.write_required=True;self.fail_start=False
  def conversation(self,*args):return {'conversation_id':ID,'revision':1,'planner_result':{'plan_sha256':'a'*64,'allowed_skill_ids':['inspect_csv'],'agent_id':'planner','model':'fixture','original_request':'fixture','context_references':[],'warnings':[],'plan':{'summary':'fixture','steps':[]}}}
  def post(self,path,payload):
   self.calls.append((path,payload))
   if path.endswith('/save-generated'):return {'plan_filename':'planner-plan.'+'a'*64+'.json','plan_sha256':'a'*64}
   if path.endswith('/prepare'):return {'review_sha256':'b'*64,'plan_sha256':'a'*64,'plan_filename':'planner-plan.'+'a'*64+'.json','approval_required_step_ids':['step_1'] if self.write_required else [],'steps':[]}
   if path.endswith('/authorize'):return {'review_sha256':'b'*64,'plan_approval_filename':'approved.json','recipe_approval_filename':'recipe-approved.json'}
   if path.endswith('/runs'):
    if self.fail_start:raise ChatError('uncertain',uncertain=True)
    return {'run_id':'3'*32,'conversation_id':ID,'plan_sha256':'a'*64,'status':'queued','steps':[]}
   raise AssertionError(path)
 c=Client();w=Workspace(c,ID);w.state=c.conversation()
 with pytest.raises(ChatError,match='authorization'):w.execute('/execute')
 assert not any(p.endswith('/runs') for p,_ in c.calls)
 assert 'Nothing executed' in w.execute('/authorize operator temporary-fixture-only')
 assert not any(p.endswith('/runs') for p,_ in c.calls)
 assert 'queued' in w.execute('/execute')
 assert c.calls[-1][1]['workflow']['plan_approval_filename']=='approved.json'
 assert w.authorization is None
 c.write_required=False;c.fail_start=True
 with pytest.raises(ChatError):w.execute('/execute')
 before=len(c.calls)
 with pytest.raises(ChatError,match='unconfirmed'):w.execute('/execute')
 assert len(c.calls)==before
 with pytest.raises(ChatError,match='unconfirmed'):w.execute('/new')
