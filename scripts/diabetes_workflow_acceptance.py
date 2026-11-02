"""Real diabetes sample → governed preparation → disposable PostgreSQL → exact reconciliation.

Never connects to configured/live services. Reports only aggregates and hashes; all
row-level outputs and throwaway credentials live in a temporary project.
"""
import argparse
from collections import Counter,defaultdict
import csv
from decimal import Decimal
import json
import os
from pathlib import Path
import secrets
import shutil
import tempfile
import time
import uuid
import psycopg
from diabetes_reference import reference,read_book,sha,CODES
from diabetes_test_flow import make_plan,SELECTED,LABELS,EXPORTED
from postgres_workflow_acceptance import docker,rejection
from geoagent_harness.interface_api import server as api
from geoagent_harness.interface_api.workflow import WorkflowRequest,prepare_workflow,authorize_workflow,execute_workflow
from geoagent_harness.approvals import plan_sha256
from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.postgres.service import inspect
from geoagent_harness.write_policy import session
from geoagent_harness.tabular.analytical_service import profile_table

REPO=Path(__file__).resolve().parents[1]
def execute(plan,root):
    stored=api.save_interface_reviewed_plan(api.InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=plan,confirmed_plan_sha256=plan_sha256(plan.plan),allowed_skill_ids=list(dict.fromkeys(s.skill for s in plan.plan.steps))),project_root=root)
    req=WorkflowRequest(action='prepare_workflow',plan_filename=stored['plan_filename'],confirmed_plan_sha256=stored['plan_sha256'])
    review=prepare_workflow(req,project_root=root)
    rejection(lambda:execute_workflow(req.model_copy(update={'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True}),project_root=root))
    approved=authorize_workflow(req.model_copy(update={'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,'approver':'real-data-fixture','reason':'Exact temporary diabetes sample outputs and disposable database only'}),project_root=root)
    assert not list((root/'data/output').iterdir()),'Authorization must not execute preparation or database work'
    from geoagent_harness.interface_api.workflow_runs import RunRequest,run_action
    workflow=req.model_copy(update={'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True,'plan_approval_filename':approved['plan_approval_filename'],'recipe_approval_filename':approved['recipe_approval_filename']})
    record=run_action(RunRequest(action='start',workflow=workflow),project_root=root,background=False)
    assert record['status']=='completed',str(record.get('finding','Inspect temporary durable evidence; no automatic retry'))
    report=run_action(RunRequest(action='report',run_id=record['run_id']),project_root=root)
    return {'status':'validated_success','step_results':record['steps'],'run_id':record['run_id'],'handoff':report['handoff']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full-preparation',action='store_true',help='Qualify streaming preparation and mapping preflight on the complete supplied file')
    parser.add_argument('--csv',type=Path,default=REPO/'data/input/test/diabetic_sample_5000.csv');parser.add_argument('--codebook',type=Path,default=REPO/'data/input/test/IDS_mapping.csv');parser.add_argument('--full',type=Path,default=REPO/'data/input/test/diabetic_data.csv');parser.add_argument('--report',type=Path)
    args=parser.parse_args();started=time.monotonic();expected=reference(args.csv,args.codebook,args.full)
    assert 0<expected['sample']['rows']<=(200000 if args.full_preparation else 10000),'Preparation bound exceeded; never silently sample'
    assert expected['sample']['duplicate_encounters']==0 and not expected['sample']['empty_counts'].get('encounter_id')
    book=read_book(args.codebook);name='actioncharter-diabetes-acceptance-'+uuid.uuid4().hex[:12];created=False
    with tempfile.TemporaryDirectory(prefix='actioncharter-diabetes-roundtrip-') as directory:
        root=Path(directory)
        for d in ['context','agents']:shutil.copytree(REPO/d,root/d)
        (root/'data/input/test').mkdir(parents=True);(root/'data/output').mkdir()
        source_name=args.csv.name if args.full_preparation else 'diabetic_sample_5000.csv'
        shutil.copyfile(args.csv,root/'data/input/test'/source_name);shutil.copyfile(args.codebook,root/'data/input/test/IDS_mapping.csv')
        password=secrets.token_hex(24);secret=root/'throwaway-password';secret.write_text(password);secret.chmod(0o600)
        old=os.environ.copy()
        try:
            docker('run','--detach','--rm','--name',name,'--label','actioncharter.acceptance=temporary','--publish','127.0.0.1::5432','--tmpfs','/var/lib/postgresql/data:rw','--env','POSTGRES_PASSWORD='+password,'postgres:17');created=True
            port=int(docker('port',name,'5432/tcp').split(':')[-1])
            for _ in range(100):
                try:
                    with psycopg.connect(host='127.0.0.1',port=port,dbname='postgres',user='postgres',password=password,connect_timeout=1) as db:db.execute('CREATE SCHEMA agent_sandbox')
                    break
                except psycopg.Error:time.sleep(.1)
            else:raise AssertionError('Disposable database did not start')
            settings=MCPSettings(project_root=root,input_root=root/'data/input',output_root=root/'data/output',postgres_host='127.0.0.1',postgres_port=port,postgres_database='postgres',postgres_user='postgres',postgres_password_file=secret,enable_write_tools=True)
            os.environ.update(ENABLE_WRITE_TOOLS='true',GEOAGENT_PROJECT_ROOT=str(root),POSTGRES_HOST='127.0.0.1',POSTGRES_PORT=str(port),POSTGRES_DB='postgres',POSTGRES_USER='postgres',POSTGRES_PASSWORD_FILE=str(secret),ALLOWED_SCHEMAS='agent_sandbox')
            for key,suffix in {'INPUT':'data/input','OUTPUT':'data/output','TRACE':'traces','REPORT':'reports','PLAN':'plans','APPROVAL':'approvals','STATE':'workflow-state','RECIPE':'workflow-recipes','RECIPE_RUN':'recipe-runs','RECIPE_EVIDENCE':'recipe-evidence','SPATIAL_CONTRACT':'spatial-contracts'}.items():os.environ['GEOAGENT_'+key+'_ROOT']=str(root/suffix)
            plan=make_plan(settings,sample='data/input/test/'+source_name,streaming=args.full_preparation)
            with session(root,enabled=True):run=execute(plan,root)
            outputs={s['step_id']:s for s in run['step_results']}
            # Inspector uses the existing complete-file analytical reader; verify independent counters.
            quality=outputs['step_1']['outcome']['table_analysis']
            assert quality['matched_row_count']==expected['sample']['rows']
            assert quality['quality']['duplicate_key']['candidate_key'] and quality['quality']['duplicate_rows']['excess_occurrences']==0
            assert quality['distinct_counts']['patient_nbr']==expected['sample']['distinct_patients']
            decoded_path=root/'data/output/diabetes_trial_01_decoded.csv'
            with decoded_path.open(newline='') as stream:decoded=list(csv.DictReader(stream))
            with args.csv.open(newline='',encoding='utf-8-sig') as stream:original=list(csv.DictReader(stream))
            assert len(decoded)==len(original)
            for source,row in zip(original,decoded):
                assert all(row[c]==source[c] for c in SELECTED)
                assert all(row[c+'_label']==book[c][source[c]] for c in CODES)
            assert outputs['step_3']['outcome']['codebook_coverage']=={k:{'label_column':k+'_label','matched_rows':expected['sample']['rows'],'unmatched_rows':0,'source_codes_preserved':True} for k in CODES}
            with (root/'data/output/diabetes_trial_01_groups.csv').open(newline='') as stream:groups=list(csv.DictReader(stream))
            counts=Counter((r['age'],r['readmitted']) for r in original);sums=defaultdict(int)
            for r in original:sums[r['age'],r['readmitted']]+=int(r['time_in_hospital'])
            assert {(g['age'],g['readmitted']):int(g['encounters']) for g in groups}==counts
            for g in groups:
                key=(g['age'],g['readmitted']);assert abs(Decimal(g['mean_stay'])-Decimal(sums[key])/counts[key])<Decimal('1e-12')
            with (root/'data/output/diabetes_trial_01_roundtrip.csv').open(newline='') as stream:exported=list(csv.DictReader(stream))
            # Compare the complete projected row multiset, not just a preview or sample.
            wanted=Counter(tuple([('\\N' if args.full_preparation and c in {'race','weight','payer_code','medical_specialty'} and r[c]=='?' else r[c]) for c in SELECTED]+[book[c][r[c]] for c in CODES]+['false']) for r in original)
            observed=Counter(tuple(r[c] for c in EXPORTED) for r in exported)
            assert observed==wanted
            table=inspect('inspect_postgres_table',{'target_schema':'agent_sandbox','target_table':'diabetes_sample_trial_01'},settings)
            assert table['row_count']==expected['sample']['rows'] and any(k['kind']=='primary' and k['columns']==['encounter_id'] for k in table['key_constraints'])
            if args.full_preparation:
                preflight=outputs['step_5']['outcome']
                assert preflight['passed'] and preflight['row_count']==len(original)
                actual_types={c['name']:c['type'] for c in table['column_metadata']}
                assert actual_types['encounter_id']=='text' and actual_types['patient_nbr']=='text'
                assert actual_types['time_in_hospital']=='bigint' and actual_types['is_deleted']=='boolean'
                for field in ('race','weight','payer_code','medical_specialty'):
                    assert table['missing_counts'][field]==sum(r[field] in {'','?'} for r in original)
                imported=outputs['step_6']['outcome']
                assert imported['mapping_sha256']==preflight['mapping_sha256']
                assert imported['executed_ddl']==preflight['proposed_ddl']
                documents=run['handoff']
                assert '101766' in documents['analytical_markdown'] if len(original)==101766 else str(len(original)) in documents['analytical_markdown']
                assert 'Executed CREATE statement' in documents['technical_markdown']
                assert 'time_in_hospital' in documents['technical_markdown'] and not documents['omitted_documents']
            # Independently query the disposable DB; fixed test SQL only, never agent input.
            with psycopg.connect(host='127.0.0.1',port=port,dbname='postgres',user='postgres',password=password) as db:
                count,patients,marked=db.execute('SELECT count(*),count(DISTINCT patient_nbr),count(*) FILTER (WHERE is_deleted) FROM agent_sandbox.diabetes_sample_trial_01').fetchone()
                assert (count,patients,marked)==(expected['sample']['rows'],expected['sample']['distinct_patients'],0)
            result={'status':'passed','reference':expected,'workflow':{'operations':[s.skill for s in plan.plan.steps],'status':run['status'],'output_rows':len(exported),'decoded_columns':len(decoded[0]),'database_columns':len(EXPORTED),'group_rows':len(groups),'complete_row_multiset_matches':True,'authorization_alone_executed':False,'database':'disposable postgres:17','live_services_touched':False},'planner_model_called':False,'elapsed_seconds':round(time.monotonic()-started,3)}
            if args.report:
                with args.report.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
            print(json.dumps({'status':'passed','source_rows':expected['sample']['rows'],'distinct_patients':expected['sample']['distinct_patients'],'groups':len(groups),'decoded_columns':len(decoded[0]),'database_columns':len(EXPORTED),'all_projected_values_match':True,'model_calls':0,'live_services_touched':False,'elapsed_seconds':result['elapsed_seconds']}))
        finally:
            os.environ.clear();os.environ.update(old)
            if created:docker('rm','--force',name)
            assert sha(args.csv)==expected['source']['sha256'] and sha(args.codebook)==expected['codebook']['sha256'],'Original source changed'

if __name__=='__main__':main()
