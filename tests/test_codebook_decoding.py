"""Exact mapping, unknown handling, preserved rows and safe governed CSV outputs."""
from pathlib import Path
import hashlib
import json
from types import SimpleNamespace
import pytest
from geoagent_harness.platform.settings import MCPSettings
from geoagent_harness.data.tabular.service import run_operation, validate_output
from geoagent_harness.contracts.paths import TabularError

@pytest.fixture
def settings(tmp_path):
 (tmp_path/'data/input').mkdir(parents=True);(tmp_path/'data/output').mkdir()
 (tmp_path/'data/input/visits.csv').write_text('encounter_id,admission_type_id,amount\n001,1,3\n002,2,5\n003,1,\n')
 (tmp_path/'data/input/book.csv').write_text('admission_type_id,description\n1,Emergency\n2,NULL\n,\nadmission_source_id,description\n1,Referral\n')
 return MCPSettings(project_root=tmp_path,input_root=tmp_path/'data/input',output_root=tmp_path/'data/output',enable_write_tools=True)

def arguments():return {'path':'data/input/visits.csv','target_path':'data/output/decoded.csv','codebook_path':'data/input/book.csv','columns':['admission_type_id'],'unknown_policy':'error'}

def test_sectioned_codebook_preserves_raw_codes_and_literal_labels(settings):
 result=run_operation('decode_csv_codes',arguments(),settings)
 assert result['row_count']==3
 assert result['preview'][0]['encounter_id']=='001'
 assert result['preview'][0]['admission_type_id']=='1'
 assert result['preview'][1]['admission_type_id_label']=='NULL'
 assert result['codebook_coverage']['admission_type_id']['unmatched_rows']==0
 assert len(result['sources'])==2
 assert validate_output(result,settings)['passed']


def test_unknown_codes_fail_before_publication_or_explicitly_preserve(settings):
 p=settings.input_root/'visits.csv';p.write_text(p.read_text()+'004,99,7\n')
 with pytest.raises(TabularError,match='unmatched'):run_operation('decode_csv_codes',arguments(),settings)
 assert not (settings.output_root/'decoded.csv').exists()
 result=run_operation('decode_csv_codes',{**arguments(),'unknown_policy':'preserve'},settings)
 assert result['preview'][-1]['admission_type_id']=='99' and result['preview'][-1]['admission_type_id_label'] is None
 assert result['codebook_coverage']['admission_type_id']['unmatched_rows']==1
 assert validate_output(result,settings)['passed']


def test_changed_codebook_or_output_does_not_validate(settings):
 result=run_operation('decode_csv_codes',arguments(),settings)
 book=settings.input_root/'book.csv';book.write_text(book.read_text().replace('Emergency','Different'))
 assert not validate_output(result,settings)['passed']
 with pytest.raises(TabularError):run_operation('decode_csv_codes',arguments(),settings)


@pytest.mark.parametrize('patch',[{'columns':['absent']},{'columns':['admission_type_id','admission_type_id']},{'codebook_path':'data/input/../book.csv'},{'target_path':'data/input/overwrite.csv'}])
def test_contract_rejections_do_not_write(settings,patch):
 with pytest.raises(ValueError):run_operation('decode_csv_codes',{**arguments(),**patch},settings)
 assert not list(settings.output_root.iterdir())


def test_validated_intermediate_input(settings):
 initial=run_operation('select_csv_columns',{'path':'data/input/visits.csv','target_path':'data/output/selected.csv','columns':['encounter_id','admission_type_id']},settings)
 prior=SimpleNamespace(validation_performed=True,validation_result=validate_output(initial,settings),execution=SimpleNamespace(result=initial))
 args={**arguments(),'source_step':'step_1'};args.pop('path')
 result=run_operation('decode_csv_codes',args,settings,{'step_1':prior})
 assert result['sources'][0]['source_step']=='step_1' and validate_output(result,settings)['passed']


def test_labels_are_independently_checked_when_hash_is_updated(settings):
 result=run_operation('decode_csv_codes',arguments(),settings)
 p=settings.output_root/'decoded.csv';p.write_text(p.read_text().replace('Emergency','Wrong'))
 result['output']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 assert not validate_output(result,settings)['checks']['decoded_labels_and_preserved_rows']


def test_durable_preview_keeps_counts_and_mapping_coverage_when_rows_exceed_budget():
 from geoagent_harness.task_actions.workflow_runs import fit_table_preview
 value={'data_contract':'table/csv-v1','row_count':5000,'columns':['code','code_label'],'preview':[{'code':'1','code_label':'x'*1000} for _ in range(10)],'preview_truncated':False,'codebook_coverage':{'code':{'matched_rows':5000,'unmatched_rows':0}}}
 result=fit_table_preview(value)
 assert len(json.dumps(result).encode())<=6000
 assert result['row_count']==5000 and result['codebook_coverage']==value['codebook_coverage']
 assert result['preview_truncated'] and len(result['preview'])<10
 assert len(value['preview'])==10
