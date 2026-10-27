"""Real-data acceptance in a temporary project; never changes original inputs/live services."""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import shutil
import tempfile
import time

from geoagent_harness.interface_api import server as api
from geoagent_harness.interface_api.workflow import EditRequest, WorkflowRequest, validate_edit, prepare_workflow, authorize_workflow, execute_workflow
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.tabular.analytical_service import profile_table
from geoagent_harness.write_policy import session


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv',type=Path,default=Path('data/input/diabetic_data.csv'))
    parser.add_argument('--codebook',type=Path,default=Path('data/input/IDS_mapping.csv'))
    args=parser.parse_args()
    repo=Path(__file__).resolve().parents[1]
    started=time.monotonic()
    # Independent oracle uses CSV counters/sums, not internal analysis services.
    counts=Counter();sums=defaultdict(int);patients=set();readmissions=Counter()
    row_frequencies=Counter();patient_frequencies=Counter();encounter_frequencies=Counter();group_patients=defaultdict(set);raw_missing=Counter();source_groups=Counter();source_patients=defaultdict(set)
    with args.csv.open(newline='',encoding='utf-8-sig') as stream:
        for row in csv.DictReader(stream):
            key=(row['age'],row['readmitted']);counts[key]+=1;sums[key]+=int(row['time_in_hospital'])
            patients.add(row['patient_nbr']);readmissions[row['readmitted']]+=1
            row_frequencies[tuple(row.values())]+=1;patient_frequencies[row['patient_nbr']]+=1;encounter_frequencies[row['encounter_id']]+=1
            group_patients[key].add(row['patient_nbr'])
            source_key=(row['admission_source_id'],row['readmitted']);source_groups[source_key]+=1;source_patients[source_key].add(row['patient_nbr'])
            for name,value in row.items():
                if value=='?':raw_missing[name]+=1
    with tempfile.TemporaryDirectory(prefix='actioncharter-diabetes-acceptance-') as name:
        root=Path(name)
        for directory in ['context','agents']:shutil.copytree(repo/directory,root/directory)
        (root/'data/input').mkdir(parents=True);(root/'data/output').mkdir()
        shutil.copyfile(args.csv,root/'data/input/diabetic_data.csv')
        shutil.copyfile(args.codebook,root/'data/input/IDS_mapping.csv')
        profile=profile_table(root,'diabetic_data.csv',{'codebook_path':'IDS_mapping.csv','group_by':['age','readmitted'],
                    'numeric_columns':['time_in_hospital'],'distinct_columns':['patient_nbr','encounter_id']})
        assert profile['row_count']==sum(counts.values())
        assert profile['table_analysis']['distinct_counts']['patient_nbr']==len(patients)
        assert {(g['age'],g['readmitted']):g['row_count'] for g in profile['table_analysis']['groups']}==dict(counts)
        assert {(g['age'],g['readmitted']):g['patient_nbr_distinct'] for g in profile['table_analysis']['groups']}=={k:len(v) for k,v in group_patients.items()}
        by_source=profile_table(root,'diabetic_data.csv',{'codebook_path':'IDS_mapping.csv',
            'group_by':['admission_source_id','readmitted'],'distinct_columns':['patient_nbr']})['table_analysis']
        assert {(g['admission_source_id'],g['readmitted']):g['row_count'] for g in by_source['groups']}==dict(source_groups)
        assert {(g['admission_source_id'],g['readmitted']):g['patient_nbr_distinct'] for g in by_source['groups']}=={k:len(v) for k,v in source_patients.items()}
        quality=profile_table(root,'diabetic_data.csv',{'quality_columns':['patient_nbr','weight','race','payer_code'],
            'duplicate_rows':True,'duplicate_key':['encounter_id'],
            'missing_values':{'weight':['?'],'race':['?'],'payer_code':['?']}})['table_analysis']
        assert quality['quality']['duplicate_rows']['excess_occurrences']==sum(n-1 for n in row_frequencies.values())
        assert quality['quality']['duplicate_key']['excess_occurrences']==sum(n-1 for n in encounter_frequencies.values())
        assert quality['quality']['duplicate_key']['candidate_key']
        frequency=quality['quality']['columns']['patient_nbr']
        assert frequency['once_only_values']==sum(n==1 for n in patient_frequencies.values())
        assert frequency['repeated_values']==sum(n>1 for n in patient_frequencies.values())
        for name in ['weight','race','payer_code']:
            assert next(p for p in quality['profiles'] if p['name']==name)['declared_missing_count']==raw_missing[name]

        plan=PlannerResult(model='operator-authored-acceptance',original_request='Full-source raw encounter grouping for a temporary correctness test',context_references=[],
            plan={'summary':'Full-file readmission grouping and export','steps':[{
                'step_id':'step_1','skill':'aggregate_csv','purpose':'Count complete source by age and recorded readmission category',
                'arguments':{'path':'data/input/diabetic_data.csv','streaming':True,'by':['age','readmitted'],
                    'aggregations':[{'column':'encounter_id','function':'count','output_column':'encounters'},
                                    {'column':'time_in_hospital','function':'mean','output_column':'mean_stay'}],
                    'target_path':'data/output/raw_readmission_groups.csv'},'requires_approval':True,'validation_required':True}]})
        with session(root,enabled=True):
            checked=validate_edit(EditRequest(action='validate_plan_edit',planner_result=plan),project_root=root)
            saved=api.save_interface_reviewed_plan(api.InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=plan,
                confirmed_plan_sha256=checked['plan_sha256'],allowed_skill_ids=checked['allowed_skill_ids']),project_root=root)
            request=WorkflowRequest(action='prepare_workflow',plan_filename=saved['plan_filename'],confirmed_plan_sha256=saved['plan_sha256'])
            review=prepare_workflow(request,project_root=root)
            approved=authorize_workflow(request.model_copy(update={'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],
                'approve_required_steps':True,'approver':'temporary-fixture-operator','reason':'Verify exact temporary CSV output only'}),project_root=root)
            assert not list((root/'data/output').iterdir())
            executed=execute_workflow(request.model_copy(update={'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],
                'confirm_execution':True,'plan_approval_filename':approved['plan_approval_filename'],'recipe_approval_filename':approved['recipe_approval_filename']}),project_root=root)
        with (root/'data/output/raw_readmission_groups.csv').open() as stream:
            output=list(csv.DictReader(stream))
        assert len(output)==len(counts)
        for row in output:
            key=(row['age'],row['readmitted'])
            assert int(row['encounters'])==counts[key]
            assert abs(float(row['mean_stay'])-sums[key]/counts[key])<1e-10
        print(json.dumps({'status':'passed','source_rows':sum(counts.values()),'distinct_patients':len(patients),
            'readmission_categories':dict(readmissions),'groups':len(output),'worker':profile['resource_usage'],
            'admission_source_groups':len(source_groups),
            'quality':{'duplicate_rows':quality['quality']['duplicate_rows']['excess_occurrences'],
                       'encounter_key_unique':quality['quality']['duplicate_key']['candidate_key'],
                       'patients_once':frequency['once_only_values'],'patients_repeated':frequency['repeated_values'],
                       'question_mark_counts':{n:raw_missing[n] for n in ['weight','race','payer_code']}},
            'workflow_status':executed.get('status'), 'elapsed_seconds':round(time.monotonic()-started,3),
            'planner_model_called':False,'outputs_only_in_temporary_project':True,
            'scope':'raw encounter analysis, not a clinical cohort or trained predictor'},indent=2))


if __name__=='__main__':main()
