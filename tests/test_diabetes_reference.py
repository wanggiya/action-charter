"""Small independent-oracle fixtures; CI does not need the user's diabetes files."""
import csv
from pathlib import Path
import importlib.util
import pytest

path=Path(__file__).parents[1]/'scripts/diabetes_reference.py'
spec=importlib.util.spec_from_file_location('diabetes_reference_oracle',path)
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)


def fixture(tmp_path,*,prefix=True):
 book=tmp_path/'book.csv';book.write_text('admission_type_id,description\n1,Emergency\n,\ndischarge_disposition_id,description\n1,Home\n,\nadmission_source_id,description\n1,Referral\n')
 rows=[]
 for i,days in enumerate([1,3,5]):
  row={f:'?' for f in oracle.FIELDS}
  row.update(encounter_id=str(i),patient_nbr='a' if i<2 else 'b',age='[40-50)',gender='Female',time_in_hospital=str(days),readmitted='NO')
  row.update({c:'1' for c in oracle.CODES});rows.append(row)
 def write(name,values):
  p=tmp_path/name
  with p.open('w',newline='') as stream:
   writer=csv.DictWriter(stream,fieldnames=oracle.FIELDS);writer.writeheader();writer.writerows(values)
  return p
 return write('sample.csv',rows[:2] if prefix else rows[1:]),book,write('full.csv',rows)


def test_reference_distinguishes_people_encounters_markers_and_prefix(tmp_path):
 sample,book,full=fixture(tmp_path)
 result=oracle.reference(sample,book,full);r=result['sample']
 assert r['rows']==2 and r['distinct_patients']==1 and r['repeated_patients']==1
 assert r['excess_patient_occurrences']==1 and r['duplicate_encounters']==0
 assert r['question_mark_counts']['payer_code']==2
 assert r['time_in_hospital']['mean']=='2' and r['time_in_hospital']['median']=='2'
 assert r['codebook_coverage']['admission_type_id']=={'matched_rows':2,'unmatched_rows':0}
 assert result['sample_provenance']=={'all_sample_rows_found_with_multiplicity':True,'is_first_n_rows':True,'random_or_representative_sample_proven':False}
 assert 'patient_nbr' not in str(result['sample']['age_readmitted'])


def test_subset_does_not_imply_prefix_or_randomness(tmp_path):
 sample,book,full=fixture(tmp_path,prefix=False)
 proof=oracle.reference(sample,book,full)['sample_provenance']
 assert proof['all_sample_rows_found_with_multiplicity'] and not proof['is_first_n_rows'] and not proof['random_or_representative_sample_proven']


def test_invalid_codebook_does_not_invent_unique_mapping(tmp_path):
 _,book,_=fixture(tmp_path)
 book.write_text('admission_type_id,description\n1,A\n1,B\n')
 with pytest.raises(ValueError,match='duplicate'):oracle.read_book(book)
