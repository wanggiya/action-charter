"""Real-input discovery/strategy checks using temporary copies; no model or live writes."""
import argparse,csv,json,shutil,tempfile
from pathlib import Path
from geoagent_harness.tabular.strategy import discover_inputs,assess_table
from geoagent_harness.tabular.analytical_service import profile_table

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source',type=Path,default=Path('data/input/diabetic_data.csv'))
 parser.add_argument('--sample',type=Path,default=Path('data/input/diabetic_sample_5000.csv'))
 parser.add_argument('--codebook',type=Path,default=Path('data/input/IDS_mapping.csv'))
 args=parser.parse_args()
 def count(path):
  with path.open(newline='',encoding='utf-8-sig') as stream:
   rows=csv.reader(stream);columns=next(rows);return columns,sum(bool(row) for row in rows)
 source_columns,source_rows=count(args.source);sample_columns,sample_rows=count(args.sample)
 with tempfile.TemporaryDirectory(prefix='actioncharter-strategy-real-') as name:
  root=Path(name);folder=root/'data/input/test';folder.mkdir(parents=True)
  for path in [args.source,args.sample,args.codebook]:shutil.copyfile(path,folder/path.name)
  inventory=discover_inputs(root,'test')
  full='test/'+args.source.name;sample='test/'+args.sample.name
  stream=assess_table(root,full,'profile');frame=assess_table(root,full,'calculate_csv_columns');sample_frame=assess_table(root,sample,'calculate_csv_columns')
  assert stream['strategy']=='full_stream'
  assert frame['strategy']=='needs_alternative'
  assert sample_frame['strategy']=='bounded_dataframe'
  src=profile_table(root,full,{'codebook_path':'test/'+args.codebook.name,'numeric_columns':['time_in_hospital'],'distinct_columns':['patient_nbr']})
  preview=profile_table(root,sample,{})
  assert src['row_count']==source_rows and preview['row_count']==sample_rows
  item=next(f for f in inventory['files'] if f['path'].endswith(args.sample.name))
  assert item['sample_provenance']=='unverified'
  assert source_columns==sample_columns
  assert 'data/input/test/'+args.source.name in item['compatible_schema_sources']
  print(json.dumps({'status':'passed','source_rows':source_rows,'sample_rows':sample_rows,'source_profile_strategy':stream['strategy'],
   'source_calculation_strategy':frame['strategy'],'sample_calculation_strategy':sample_frame['strategy'],
   'schema_compatible':True,'sample_provenance':'unverified','model_calls':0,'originals_changed':False},indent=2))
if __name__=='__main__':main()
