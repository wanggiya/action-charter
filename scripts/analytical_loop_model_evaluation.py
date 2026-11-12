"""Explicit installed-model evaluation on temporary synthetic data; no downloads."""
import argparse,json,tempfile,shutil,statistics,csv
from pathlib import Path
from geoagent_harness.platform.model_gateway.client import SharedModelClient
from geoagent_harness.platform.model_settings import ModelSettings
from geoagent_harness.agents.runtime.analyst import run_session

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--model',default='qwen3:4b-instruct')
 parser.add_argument('--base-url',default='http://127.0.0.1:11434/v1')
 parser.add_argument('--output',type=Path)
 parser.add_argument('--real-data',action='store_true')
 args=parser.parse_args()
 with tempfile.TemporaryDirectory(prefix='actioncharter-analyst-evaluation-') as folder:
  root=Path(folder);d=root/'data/input/test';d.mkdir(parents=True)
  (d/'visits.csv').write_text('encounter_id,patient_nbr,stay\n'+''.join(f'{i},{i//2},{1+i%5}\n' for i in range(5000)))
  (d/'visits_sample_2.csv').write_text('encounter_id,patient_nbr,stay\n0,0,1\n1,0,2\n')
  filename='visits.csv';field='stay';expected_rows=5000;expected_distinct=2500;expected_mean=3
  if args.real_data:
   for p in d.glob('*.csv'):p.unlink()
   source=Path(__file__).resolve().parents[1]/'data/input/test'
   for name in ['diabetic_data.csv','diabetic_sample_5000.csv','IDS_mapping.csv']:shutil.copyfile(source/name,d/name)
   filename='diabetic_data.csv';field='time_in_hospital'
   with (d/filename).open(newline='') as f:rows=list(csv.DictReader(f))
   expected_rows=len(rows);expected_distinct=len({r['patient_nbr'] for r in rows});expected_mean=statistics.mean(float(r[field]) for r in rows)
  client=SharedModelClient(ModelSettings(base_url=args.base_url,model=args.model,timeout_seconds=30,max_tokens=1200,reasoning_effort='none'))
  result=run_session(root,f'Explore data/input/test. Assess {filename} for full-source analysis. Compute distinct patient_nbr and numeric mean {field}; use full {filename} when eligible, and explain any neighbouring sample limitations. No writes.','test',model_client=client)
  if args.output:
   args.output.write_text(json.dumps(result,indent=2));args.output.chmod(0o600)
  print(json.dumps({k:result[k] for k in ['status','message','model_calls','tool_calls','elapsed_seconds','prompt_bytes']},indent=2))
  profiles=[o['result'] for o in result['observations'] if o['tool']=='profile_table' and o['result'].get('source_sha256')]
  assert profiles and profiles[-1]['source_rows']==expected_rows,result['journal']
  assert profiles[-1]['distinct_counts']['patient_nbr']==expected_distinct
  assert abs(next(p for p in profiles[-1]['profiles'] if p['name']==field)['numeric']['mean']-expected_mean)<1e-10
  assert result['status']=='completed'
if __name__=='__main__':main()
