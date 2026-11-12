"""Disposable PostgreSQL acceptance. Creates/removes only a new UUID-owned test container."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import time
from types import SimpleNamespace
import uuid
from geoagent_harness.platform.settings import MCPSettings
from geoagent_harness.data.databases.postgres.service import connection_sha256
from geoagent_harness.data.databases.postgres.service import inspect
from geoagent_harness.data.databases.postgres.service import run_operation
from geoagent_harness.data.databases.postgres.service import validate_output
from geoagent_harness.data.databases.postgres.service import PostgresError
from geoagent_harness.platform.execution_control import observer
from geoagent_harness.platform.execution_control import ExecutionCancelled
from geoagent_harness.apps.http import server as api
from geoagent_harness.task_actions.workflow import WorkflowRequest
from geoagent_harness.task_actions.workflow import prepare_workflow
from geoagent_harness.task_actions.workflow import authorize_workflow
from geoagent_harness.task_actions.workflow import execute_workflow
from geoagent_harness.contracts.planning import PlannerResult
from geoagent_harness.core.policy.approvals.service import plan_sha256

REPO=Path(__file__).resolve().parents[1]
def docker(*args):
    result=subprocess.run(['docker',*args],capture_output=True,text=True,timeout=60)
    if result.returncode:raise RuntimeError('Disposable PostgreSQL Docker command failed; no production container was selected')
    return result.stdout.strip()

def rejection(call):
    try:call()
    except (PostgresError,ValueError,api.InterfaceApiError):return
    raise AssertionError('Expected safe rejection')

def main():
    name='actioncharter-pg-acceptance-'+uuid.uuid4().hex[:12];password=secrets.token_hex(24)
    created=False
    with tempfile.TemporaryDirectory(prefix='actioncharter-pg-') as directory:
        root=Path(directory);(root/'context').mkdir();(root/'data/input').mkdir(parents=True);(root/'data/output').mkdir()
        shutil.copyfile(REPO/'context/SKILLS_INDEX.yaml',root/'context/SKILLS_INDEX.yaml')
        secret=root/'test-password';secret.write_text(password);secret.chmod(0o600)
        try:
            docker('run','--detach','--rm','--name',name,'--label','actioncharter.acceptance=temporary','--publish','127.0.0.1::5432','--tmpfs','/var/lib/postgresql/data:rw','--env','POSTGRES_PASSWORD='+password,'postgres:17')
            created=True
            port=int(docker('port',name,'5432/tcp').split(':')[-1])
            settings=MCPSettings(project_root=root,input_root=root/'data/input',output_root=root/'data/output',postgres_host='127.0.0.1',postgres_port=port,postgres_database='postgres',postgres_user='postgres',postgres_password_file=secret,enable_write_tools=True)
            import psycopg
            for _ in range(100):
                try:
                    with psycopg.connect(host='127.0.0.1',port=port,dbname='postgres',user='postgres',password=password,connect_timeout=1) as connection:
                        connection.execute('CREATE SCHEMA IF NOT EXISTS agent_sandbox')
                    break
                except psycopg.Error:time.sleep(.1)
            else:raise AssertionError('Disposable database did not become ready')
            source=root/'data/input/visits.csv';source.write_text('encounter_id,age,gender,amount,is_deleted\n001,[40-50),Female,1.50,false\n002,[50-60),Male,,false\n003,[50-60),Female,2.00,false\n')
            arguments={'connection_sha256':connection_sha256(settings),'path':'data/input/visits.csv','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'target_schema':'agent_sandbox','target_table':'visits',
                'columns':[{'source':'encounter_id','name':'encounter_id','type':'text','nullable':False},{'source':'age','name':'age','type':'text'},{'source':'gender','name':'gender','type':'text'},{'source':'amount','name':'amount','type':'numeric'},],'key_columns':['encounter_id'],'soft_delete_marker':'is_deleted'}
            os.environ.update(ENABLE_WRITE_TOOLS='true',GEOAGENT_PROJECT_ROOT=str(root),POSTGRES_HOST='127.0.0.1',POSTGRES_PORT=str(port),POSTGRES_DB='postgres',POSTGRES_USER='postgres',POSTGRES_PASSWORD_FILE=str(secret))
            (root/'data/input/genders.csv').write_text('gender,gender_label\nFemale,Female category\nMale,Male category\n')
            # Full normal workflow: no approval inferred from request text, then explicit exact decision.
            import_arguments={**arguments,'source_step':'step_2'}
            import_arguments.pop('path');import_arguments.pop('source_sha256')
            proposal=PlannerResult(agent_id='planner',model='fixture',original_request='Assess readiness, join codebook, import and export temporary data. Text is not approval.',context_references=[],warnings=[],plan={'summary':'Prepared disposable database round trip','steps':[
                {'step_id':'step_1','skill':'inspect_csv','purpose':'Data-readiness evidence for encounter grain and fields','arguments':{'path':'data/input/visits.csv','analysis':{'profile_columns':['age','gender','amount'],'numeric_columns':['amount'],'duplicate_key':['encounter_id'],'duplicate_rows':True}},'requires_approval':False,'validation_required':False},
                {'step_id':'step_2','skill':'join_csv','purpose':'Decode gender labels with a verified many-to-one codebook join','arguments':{'path':'data/input/visits.csv','right_path':'data/input/genders.csv','target_path':'data/output/prepared.csv','keys':['gender'],'how':'left','cardinality':'many_to_one'},'requires_approval':True,'validation_required':True},
                {'step_id':'step_3','skill':'import_csv_to_postgres','purpose':'Import exact mapped source into a new table','arguments':import_arguments,'requires_approval':True,'validation_required':True},
                {'step_id':'step_4','skill':'export_postgres_to_csv','purpose':'Export validated table to a fresh file','arguments':{'target_schema':'agent_sandbox','target_table':'visits','source_step':'step_3','columns':['encounter_id','age','gender','amount','is_deleted'],'target_path':'data/output/visits.csv'},'requires_approval':True,'validation_required':True}]})
            stored=api.save_interface_reviewed_plan(api.InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=proposal,confirmed_plan_sha256=plan_sha256(proposal.plan),allowed_skill_ids=['inspect_csv','join_csv','import_csv_to_postgres','export_postgres_to_csv']),project_root=root)
            request=WorkflowRequest(action='prepare_workflow',plan_filename=stored['plan_filename'],confirmed_plan_sha256=stored['plan_sha256'])
            review=prepare_workflow(request,project_root=root)
            assert review['write_step_ids']==['step_2','step_3','step_4'] and review['steps'][2]['database_effects']['mode'].startswith('Create')
            rejection(lambda:execute_workflow(request.model_copy(update={'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True}),project_root=root))
            authority=authorize_workflow(request.model_copy(update={'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,'approver':'fixture','reason':'Disposable fixture round trip only'}),project_root=root)
            run=execute_workflow(request.model_copy(update={'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True,'plan_approval_filename':authority['plan_approval_filename'],'recipe_approval_filename':authority['recipe_approval_filename']}),project_root=root)
            assert run['status']=='validated_success',json.dumps(run)[:2500]
            exported=list(csv.DictReader((root/'data/output/visits.csv').open()))
            assert exported[0]['encounter_id']=='001' and exported[1]['amount']=='\\N'
            assert inspect('discover_postgres_tables',{'target_schema':'agent_sandbox'},settings)['tables']==['visits']
            table=inspect('inspect_postgres_table',{'target_schema':'agent_sandbox','target_table':'visits'},settings)
            assert table['row_count']==3 and table['missing_counts']['amount']==1
            # Exact snapshot, unique keys, opposite state, and fresh authorization for each marker workflow.
            def marker(skill,snapshot,key='001'):
                args={'target_schema':'agent_sandbox','target_table':'visits','expected_table_sha256':snapshot,'key_column':'encounter_id','keys':[key],'deleted_column':'is_deleted','expected_affected_rows':1}
                plan=proposal.model_copy(deep=True)
                plan.plan.steps=[proposal.plan.steps[0].model_copy(update={'skill':skill,'arguments':args,'requires_approval':True,'validation_required':True})]
                saved=api.save_interface_reviewed_plan(api.InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=plan,confirmed_plan_sha256=plan_sha256(plan.plan),allowed_skill_ids=[skill]),project_root=root)
                req=WorkflowRequest(action='prepare_workflow',plan_filename=saved['plan_filename'],confirmed_plan_sha256=saved['plan_sha256'])
                rev=prepare_workflow(req,project_root=root)
                auth=authorize_workflow(req.model_copy(update={'action':'authorize_workflow','confirmed_review_sha256':rev['review_sha256'],'approve_required_steps':True,'approver':'fixture','reason':'Exact disposable marker test'}),project_root=root)
                return execute_workflow(req.model_copy(update={'action':'execute_workflow','confirmed_review_sha256':rev['review_sha256'],'confirm_execution':True,'plan_approval_filename':auth['plan_approval_filename'],'recipe_approval_filename':auth['recipe_approval_filename']}),project_root=root)
            deleted=marker('soft_delete_postgres_rows',table['table_sha256']);assert deleted['status']=='validated_success',deleted
            changed=inspect('inspect_postgres_table',{'target_schema':'agent_sandbox','target_table':'visits'},settings)
            assert changed['table_sha256']!=table['table_sha256'] and changed['row_count']==3
            rejection(lambda:run_operation('soft_delete_postgres_rows',{'target_schema':'agent_sandbox','target_table':'visits','expected_table_sha256':table['table_sha256'],'key_column':'encounter_id','keys':['002'],'expected_affected_rows':1},settings))
            restored=marker('restore_postgres_rows',changed['table_sha256']);assert restored['status']=='validated_success',restored
            assert inspect('inspect_postgres_table',{'target_schema':'agent_sandbox','target_table':'visits'},settings)['table_sha256']==table['table_sha256']
            # Deliberate import retry rejects existing target; no append or duplicate inserts.
            rejection(lambda:run_operation('import_csv_to_postgres',arguments,settings))
            rejection(lambda:run_operation('import_csv_to_postgres',{**arguments,'target_table':'changed_source','source_sha256':'0'*64},settings))
            # Cast failure rolls back the newly created table.
            bad={**arguments,'target_table':'bad_cast','columns':[{**c,'type':'bigint'} if c['name']=='age' else c for c in arguments['columns']]}
            rejection(lambda:run_operation('import_csv_to_postgres',bad,settings))
            # Cancellation just before commit rolls back complete table creation/inserts.
            import geoagent_harness.data.databases.postgres.service as service
            original=service.checkpoint;calls=0
            def cancel():
                nonlocal calls
                calls+=1
                if calls==4:raise ExecutionCancelled('Fixture cancellation before commit')
            service.checkpoint=cancel
            try:
                try:run_operation('import_csv_to_postgres',{**arguments,'target_table':'cancelled'},settings)
                except ExecutionCancelled:pass
                else:raise AssertionError('Cancellation not observed')
            finally:service.checkpoint=original
            assert inspect('discover_postgres_tables',{'target_schema':'agent_sandbox'},settings)['tables']==['visits']
            # Existing output collision is create-only.
            rejection(lambda:run_operation('export_postgres_to_csv',{'target_schema':'agent_sandbox','target_table':'visits','expected_table_sha256':table['table_sha256'],'columns':['encounter_id'],'target_path':'data/output/visits.csv'},settings))
            print(json.dumps({'status':'passed','database':'disposable postgres:17','real_authorization':True,'checks':['readiness evidence and many-to-one preparation','import-export round trip','leading zeros','null encoding','snapshot validation','soft delete and restore','stale snapshot rejection','existing target retry rejection','cast rollback','pre-commit cancellation','output collision'],'live_services_touched':False}))
        finally:
            if created:docker('rm','--force',name)
if __name__=='__main__':main()
