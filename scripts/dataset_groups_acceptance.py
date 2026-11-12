"""Compare real source grouping percentages/selected-column pages using disposable Docker-backed projects."""
import csv,json,os,shutil,tempfile,time,uuid
from collections import Counter
from pathlib import Path
from geoagent_harness.data.tabular.dataset_service import profile_dataset
from geoagent_harness.data.tabular.dataset_views import DatasetViewRequest
from geoagent_harness.data.tabular.dataset_views import dataset_view
from geoagent_harness.task_actions.conversation import Conversation
from geoagent_harness.task_actions.planning_tasks import write_turn


def main():
 os.environ['ACTIONCHARTER_ANALYTICAL_RUNTIME']='docker';repo=Path(__file__).resolve().parents[1];evidence=[]
 with tempfile.TemporaryDirectory(prefix='actioncharter-real-groups-') as temp:
  root=Path(temp);folder=root/'data/input';folder.mkdir(parents=True)
  for name in ['diabetic_sample_5000.csv','diabetic_data.csv']:
   started=time.monotonic();shutil.copyfile(repo/'data/input/test'/name,folder/name)
   with (folder/name).open(newline='') as f:rows=list(csv.DictReader(f))
   identity=uuid.uuid4().hex;p=profile_dataset(root,name,owner=identity)
   state=Conversation(conversation_id=identity,revision=1,analytical_session={'observations':[{'tool':'profile_table','result':{'dataset_profile':p}}]})
   write_turn(root,state.model_dump(mode='json'),expected_revision=0,expected_task_revision=0)
   def request(view,columns):return DatasetViewRequest(action='calculate',conversation_id=identity,expected_revision=1,source_sha256=p['source_sha256'],profile_sha256=p['artifact']['sha256'],view=view,columns=columns)
   for keys in [['age'],['age','readmitted']]:
    result=dataset_view(request('groups',keys),project_root=root)['result'];reference=Counter(tuple(row[k] for k in keys) for row in rows)
    assert {tuple(g[k] for k in keys):g['row_count'] for g in result['groups']}==reference
    assert abs(sum(g['percentage_total'] for g in result['groups'])-100)<1e-9
    totals=Counter(row['age'] for row in rows)
    for g in result['groups']:
     assert abs(g['percentage_total']-100*g['row_count']/len(rows))<1e-10
     assert abs(g['percentage_within_primary']-100*g['row_count']/totals[g['age']])<1e-10
    assert result['runtime']['mode']=='docker'
   page=dataset_view(request('table',['age','readmitted']),project_root=root)['result']
   assert page['table']['columns']==['age','readmitted']
   assert page['table']['preview']==[{k:row[k] or None for k in ['age','readmitted']} for row in rows[:20]]
   evidence.append({'file':name,'rows':len(rows),'age_groups':len(totals),'age_readmitted_groups':len(reference),'percentage_checks':'all rows and within age exact','selected_table_columns':page['table']['columns'],'seconds':round(time.monotonic()-started,2)})
 print(json.dumps({'status':'passed','runtime':'docker','temporary_copies_only':True,'cases':evidence},indent=2))
if __name__=='__main__':main()
