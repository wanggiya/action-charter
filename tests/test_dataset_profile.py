import csv,math
from pathlib import Path
import pytest
from geoagent_harness.tabular.dataset_profile import inspect_dataset
from geoagent_harness.tabular.dataset_service import profile_dataset

@pytest.fixture
def data(tmp_path):
 (tmp_path/'data/input').mkdir(parents=True)
 (tmp_path/'data/input/a.csv').write_text('patient_nbr,admission_source_id,time_in_hospital,number_inpatient,age,weight,diag_1,race\n001,1,2,0,[50-60),?,250,White\n001,2,4,2,[60-70),[75-100),401,?\n002,1,6,1,[50-60),?,V12,Black\n')
 return tmp_path

def test_types_statistics_markers_and_groups(data):
 r=inspect_dataset(data,'a.csv',{'group_by':['age'],'numeric_columns':['time_in_hospital'],'distinct_columns':['patient_nbr']})
 p={v['name']:v for v in r['profiles']}
 assert p['patient_nbr']['analytical_role']=='identifier' and p['patient_nbr']['numeric'] is None
 assert p['patient_nbr']['distinct_count']==2 and p['patient_nbr']['frequency']['once_only_values']==1
 assert p['number_inpatient']['analytical_role']=='count'
 assert p['admission_source_id']['analytical_role']=='categorical'
 assert p['age']['analytical_role']=='ordered_category' and p['weight']['analytical_role']=='ordered_category'
 assert p['diag_1']['analytical_role']=='categorical'
 n=p['time_in_hospital']['numeric']
 assert (n['mean'],n['minimum'],n['maximum'],n['standard_deviation'])==(4,2,6,2)
 assert n['quantiles']=={'q1':3,'median':4,'q3':5}
 assert sum(b['count'] for b in n['histogram'])==3
 assert p['weight']['candidate_missing_markers']=={'?':2} and p['weight']['missing_count']==0
 assert r['table']['preview'][0]['patient_nbr']=='001'
 assert sum(g['row_count'] for g in r['groups'])==3
 assert r['distinct_counts']['patient_nbr']==2

def test_overrides_missing_policy_local_runtime_and_no_fallback(data,monkeypatch):
 monkeypatch.setenv('ACTIONCHARTER_ANALYTICAL_RUNTIME','local')
 r=profile_dataset(data,'a.csv',{'missing_values':{'weight':['?']},'role_overrides':{'number_inpatient':'categorical'}})
 assert r['runtime']['mode']=='local_bounded_process'
 assert next(p for p in r['profiles'] if p['name']=='weight')['missing_count']==2
 assert next(p for p in r['profiles'] if p['name']=='number_inpatient')['numeric_status']=='not_applicable'
 assert (data/'workflow-state/analytical-artifacts'/ (r['artifact']['sha256']+'.json')).exists()
 monkeypatch.setenv('ACTIONCHARTER_ANALYTICAL_RUNTIME','docker')
 def unavailable(*a,**kw):raise ValueError('Docker unavailable')
 monkeypatch.setattr('geoagent_harness.sandbox.manager.docker',unavailable)
 with pytest.raises(ValueError,match='Docker unavailable'):profile_dataset(data,'a.csv')

def test_policies_invalid_rows_and_nonfinite_values(data):
 with pytest.raises(ValueError):inspect_dataset(data,'a.csv',{'role_overrides':{'missing':'text'}})
 with pytest.raises(ValueError):inspect_dataset(data,'a.csv',{'role_overrides':{'race':'made_up'}})
 (data/'data/input/n.csv').write_text('x\n1\nNaN\ninf\n?\n')
 r=inspect_dataset(data,'n.csv',{'role_overrides':{'x':'numerical'}})
 p=r['profiles'][0]
 assert p['numeric']['count']==1 and p['numeric']['invalid_count']==3
 assert p['numeric']['standard_deviation'] is None

def test_codebook_coverage_and_full_source_stats(data):
 (data/'data/input/codes.csv').write_text('admission_source_id,description\n1,Emergency\n')
 r=inspect_dataset(data,'a.csv',{'codebook_path':'codes.csv'})
 assert r['codebook']['coverage']['admission_source_id']=={'matched_rows':2,'unmatched_rows':1}
 assert next(p for p in r['profiles'] if p['name']=='admission_source_id')['numeric'] is None
 assert r['checks']['profile_count_matches_columns']
 r=inspect_dataset(data,'a.csv',{'filters':[{'column':'age','value':'[50-60)'}]})
 assert r['source_rows']==3 and r['matching_rows']==2
 assert next(p for p in r['profiles'] if p['name']=='time_in_hospital')['numeric']['mean']==4


def test_source_paths_identity_and_artifact_boundary(data,monkeypatch):
 monkeypatch.setenv('ACTIONCHARTER_ANALYTICAL_RUNTIME','local')
 for path in ['../a.csv','data/input/../a.csv','/etc/passwd','data/input/a.csv/../a.csv']:
  with pytest.raises(ValueError):profile_dataset(data,path)
 (data/'data/input/link.csv').symlink_to(data/'data/input/a.csv')
 with pytest.raises(Exception):profile_dataset(data,'link.csv')
 with pytest.raises(ValueError,match='changed'):profile_dataset(data,'a.csv',expected_sha256='0'*64)
 assert not list((data/'workflow-state').rglob('*.json')) if (data/'workflow-state').exists() else True
 r=profile_dataset(data,'a.csv',owner='chat-one')
 stored=data/'workflow-state/analytical-artifacts'/ (r['artifact']['sha256']+'.json')
 import json,hashlib
 assert hashlib.sha256(stored.read_bytes()).hexdigest()==r['artifact']['sha256']
 assert json.loads(stored.read_text())['owner']=='chat-one'
 assert not r['artifact']['execution_authority']
 assert stored.stat().st_mode&0o077==0


def test_mcp_uses_same_typed_profile_service(data,monkeypatch):
 from types import SimpleNamespace
 from geoagent_harness.mcp_server.tools import profile_dataset as mcp_profile
 monkeypatch.setenv('ACTIONCHARTER_ANALYTICAL_RUNTIME','local')
 r=mcp_profile('a.csv',settings=SimpleNamespace(project_root=data,input_root=data/'data/input'))
 assert len(r['profiles'])==8 and r['source_rows']==3
 assert r['runtime']['mode']=='local_bounded_process'
 with pytest.raises(ValueError):mcp_profile('a.csv',{'code':'print(1)'},settings=SimpleNamespace(project_root=data,input_root=data/'data/input'))
