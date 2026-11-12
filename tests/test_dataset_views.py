"""Complete-file interactive groups, percentage denominators and selected-column pages."""
import json
from pathlib import Path
import pytest
from geoagent_harness.task_actions.conversation import Conversation, _write, _path
from geoagent_harness.data.tabular.dataset_service import profile_dataset
from geoagent_harness.data.tabular.dataset_views import DatasetViewRequest, dataset_view
from geoagent_harness.data.tabular.grouping import percentages

ID='a'*32
@pytest.fixture
def saved(tmp_path,monkeypatch):
 monkeypatch.setenv('ACTIONCHARTER_ANALYTICAL_RUNTIME','local')
 p=tmp_path/'data/input';p.mkdir(parents=True)
 # readmitted intentionally outside the default 16-column preview.
 names=['age']+[f'f{i}' for i in range(16)]+['readmitted','patient_nbr']
 rows=[['young']+['x']*16+['NO','001'],['young']+['x']*16+['<30','001'],['older']+['x']*16+['NO','002'],['older']+['x']*16+['NO','003'],['older']+['x']*16+['?','004'],['']+['x']*16+['NO','005']]
 import csv
 with (p/'visits.csv').open('w',newline='') as f:w=csv.writer(f);w.writerow(names);w.writerows(rows)
 profile=profile_dataset(tmp_path,'visits.csv',owner=ID)
 state=Conversation(conversation_id=ID,revision=1,analytical_session={'observations':[{'tool':'profile_table','result':{'dataset_profile':profile}}]})
 from geoagent_harness.task_actions.planning_tasks import write_turn
 write_turn(tmp_path,state.model_dump(mode='json'),expected_revision=0,expected_task_revision=0)
 return tmp_path,profile

def req(profile,**kw):
 return DatasetViewRequest(conversation_id=ID,expected_revision=1,source_sha256=profile['source_sha256'],profile_sha256=profile['artifact']['sha256'],**kw)

def test_age_only_age_readmitted_and_percentage_denominators(saved):
 root,p=saved
 age=dataset_view(req(p,action='calculate',columns=['age']),project_root=root)['result']
 assert age['columns']==['age'] and sum(r['row_count'] for r in age['groups'])==6
 assert sum(r['percentage_total'] for r in age['groups'])==pytest.approx(100)
 both=dataset_view(req(p,action='calculate',columns=['age','readmitted']),project_root=root)['result']
 assert both['columns']==['age','readmitted'] and len(both['groups'])==5
 assert sum(r['percentage_total'] for r in both['groups'])==pytest.approx(100)
 older=[g for g in both['groups'] if g['age']=='older']
 assert sum(g['percentage_within_primary'] for g in older)==pytest.approx(100)
 assert next(g for g in older if g['readmitted']=='NO')['percentage_within_primary']==pytest.approx(200/3)
 assert any(g['age']=='' for g in both['groups']) and any(g['readmitted']=='?' for g in both['groups'])
 assert all(g['primary_denominator']==3 for g in older)
 assert both['checks']['group_count_reconciles'] and both['verified_at_read']


def test_selected_table_fields_include_column_outside_original_preview(saved,monkeypatch):
 root,p=saved
 assert 'readmitted' not in p['table']['columns']
 result=dataset_view(req(p,action='calculate',view='table',columns=['age','readmitted'],offset=1,limit=2),project_root=root)['result']
 assert result['table']['columns']==['age','readmitted'] and len(result['table']['preview'])==2
 assert result['table']['preview'][0]=={'age':'young','readmitted':'<30'}
 assert result['table']['offset']==1 and result['source_rows']==6
 def no_scan(*a,**kw):raise AssertionError('Restoration must not rescan')
 monkeypatch.setattr('geoagent_harness.data.tabular.dataset_views.profile_dataset',no_scan)
 assert dataset_view(req(p,action='read',view='table'),project_root=root)['result']==result
 assert dataset_view(req(p,action='read',view='groups'),project_root=root)['result'] is None


def test_changed_source_scope_revision_and_identifiers_preserve_saved_view(saved):
 root,p=saved
 first=dataset_view(req(p,action='calculate',columns=['age']),project_root=root)['result']
 for changes in [{'conversation_id':'b'*32},{'expected_revision':0},{'profile_sha256':'0'*64},{'source_sha256':'0'*64}]:
  r=req(p,action='calculate',columns=['age']).model_copy(update=changes)
  with pytest.raises(ValueError):dataset_view(r,project_root=root)
 for columns in [['patient_nbr'],['absent']]:
  with pytest.raises(ValueError):dataset_view(req(p,action='calculate',columns=columns),project_root=root)
 with (root/'data/input/visits.csv').open('a') as f:f.write('older,'+','.join(['x']*16)+',NO,006\n')
 with pytest.raises(ValueError,match='changed'):dataset_view(req(p,action='calculate',columns=['age','readmitted']),project_root=root)
 assert dataset_view(req(p,action='read'),project_root=root)['result']==first
 assert not (root/'data/output').exists()


def test_concurrent_chat_change_rejects_publication(saved,monkeypatch):
 root,p=saved
 from geoagent_harness.data.tabular.dataset_service import profile_dataset as real
 def concurrent(*args,**kw):
  result=real(*args,**kw)
  from geoagent_harness.task_actions.planning_tasks import database
  with database(root,write=True) as db:
   row=json.loads(db.execute('SELECT value FROM conversations WHERE id=?',(ID,)).fetchone()[0]);row['revision']=2
   db.execute('UPDATE conversations SET value=? WHERE id=?',(json.dumps(row),ID))
  return result
 monkeypatch.setattr('geoagent_harness.data.tabular.dataset_views.profile_dataset',concurrent)
 with pytest.raises(ValueError,match='during calculation'):dataset_view(req(p,action='calculate',columns=['age']),project_root=root)
 assert percentages([],['age'],0)==[]


def test_cli_restores_same_groups_and_mcp_contract(saved):
 root,p=saved
 from geoagent_harness.task_actions.data_tools import explore_dataset_view
 from geoagent_harness.task_actions.planning_tasks import conversation_record
 from geoagent_harness.apps.chat.views import interactive_view, render_view
 from types import SimpleNamespace
 result=explore_dataset_view(req(p,action='calculate',columns=['age','readmitted']).model_dump(),settings=SimpleNamespace(project_root=root,input_root=root/'data/input'))['result']
 state=conversation_record(root,ID)
 class Client:
  def post(self,path,payload):
   assert path=='/api/v1/analysis/view' and payload['action']=='read'
   return dataset_view(DatasetViewRequest.model_validate(payload),project_root=root)
 value=interactive_view(Client(),state,'groups',limit=100)
 assert value['rows']==result['groups'] and value['group_by']==['age','readmitted']
 assert 'Cross-tab' in render_view(value) and '6 grouped / 6 matching' in render_view(value)
 within=interactive_view(Client(),state,'groups',cross_measure='row')
 assert '66.67%' in render_view(within)


def test_cross_tab_counts_percentages_missing_swap_and_complete_margins():
 from geoagent_harness.apps.chat.views import cross_tab
 groups=[{'age':'young','gender':'F','row_count':2},{'age':'young','gender':'M','row_count':1},
         {'age':'older','gender':'F','row_count':1},{'age':'older','gender':'M','row_count':0},
         {'age':'','gender':None,'row_count':2}]
 keys=['age','gender']
 c=cross_tab(groups,keys,6)
 assert c['headers']==['age / gender','F','M','(missing)','Total']
 assert c['rows']==[['young',2,1,0,3],['older',1,0,0,1],['(empty cell)',0,0,2,2],['Total',3,1,2,6]]
 assert c['reconciles']
 assert cross_tab(groups,keys,6,measure='row')['rows'][0]==['young','66.67%','33.33%','0.00%','100.00%']
 assert cross_tab(groups,keys,6,measure='column')['rows'][0]==['young','66.67%','100.00%','0.00%','50.00%']
 assert cross_tab(groups,keys,6,measure='total')['rows'][0]==['young','33.33%','16.67%','0.00%','50.00%']
 swapped=cross_tab(groups,keys,6,swap=True)
 assert swapped['headers']==['gender / age','young','older','(empty cell)','Total']
 assert swapped['rows'][0]==['F',2,1,0,3]
 assert cross_tab([],keys,0,measure='total')['rows']==[['Total','N/A']]
 assert not cross_tab(groups,keys,7)['reconciles']
 with pytest.raises(ValueError):cross_tab(groups,keys,6,measure='wrong')


def test_cross_tab_display_budget_does_not_change_population_or_totals():
 from geoagent_harness.apps.chat.views import cross_tab
 groups=[{'a':f'row{i}','b':f'col{j}','row_count':1} for i in range(30) for j in range(15)]
 c=cross_tab(groups,['a','b'],450)
 assert c['row_categories']==30 and c['column_categories']==15
 assert len(c['rows'])==26 and len(c['headers'])==14
 assert c['rows'][0][-1]==15 and c['rows'][-1][-1]==450
 assert c['rows'][-1][1]==30
 assert cross_tab(groups,['a','b'],450,measure='row')['rows'][0][1]=='6.67%'
