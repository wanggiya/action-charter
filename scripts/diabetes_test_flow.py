"""Operator-reviewed real-data acceptance plans; these definitions grant no authority."""
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.postgres.service import connection_sha256
from diabetes_reference import CODES

SELECTED=['encounter_id','patient_nbr','age','gender','race','time_in_hospital','readmitted',*CODES,'weight','payer_code','medical_specialty']
LABELS=[c+'_label' for c in CODES]
EXPORTED=[*SELECTED,*LABELS,'is_deleted']

def make_plan(settings,*,sample='data/input/test/diabetic_sample_5000.csv',codebook='data/input/test/IDS_mapping.csv',table='diabetes_sample_trial_01',output='data/output/diabetes_trial_01'):
    def step(n,skill,purpose,args,write=True,depends=None):
        return {'step_id':f'step_{n}','skill':skill,'purpose':purpose,'arguments':args,'requires_approval':write,'validation_required':write,**({'depends_on':depends} if depends is not None else {})}
    quality={'codebook_path':codebook,'profile_columns':['age','gender','readmitted','time_in_hospital','weight','payer_code','race','medical_specialty'],
        'numeric_columns':['time_in_hospital'],'quality_columns':['encounter_id','patient_nbr','payer_code','weight'],'distinct_columns':['encounter_id','patient_nbr'],
        'duplicate_key':['encounter_id'],'duplicate_rows':True,'missing_values':{k:['?'] for k in ['race','weight','payer_code','medical_specialty']}}
    columns=[{'source':c,'name':c,'type':'bigint' if c=='time_in_hospital' else 'text','nullable':c not in {'encounter_id','patient_nbr'}} for c in [*SELECTED,*LABELS]]
    return PlannerResult(agent_id='planner',model='operator-authored-real-data-acceptance',original_request='Validate the supplied diabetes sample structurally, preserve encounters and raw missing codes, decode supplied labels, compare groups, and round-trip a fresh disposable PostgreSQL table. No clinical exclusions or imputation.',context_references=[],warnings=[],plan={
        'summary':'Diabetes sample readiness, preparation, grouping and verified database round trip','steps':[
            step(1,'inspect_csv','Record source-bound readiness evidence at encounter grain',{'path':sample,'analysis':quality},False),
            step(2,'select_csv_columns','Keep declared fields without removing encounters',{'path':sample,'columns':SELECTED,'target_path':output+'_selected.csv'}),
            step(3,'decode_csv_codes','Decode only the three supplied ID sections; preserve original codes and rows',{'source_step':'step_2','codebook_path':codebook,'columns':CODES,'unknown_policy':'error','target_path':output+'_decoded.csv'}),
            step(4,'aggregate_csv','Compare complete sample age/readmission counts and mean hospital days',{'source_step':'step_3','by':['age','readmitted'],'aggregations':[{'column':'encounter_id','function':'count','output_column':'encounters'},{'column':'time_in_hospital','function':'mean','output_column':'mean_stay'}],'target_path':output+'_groups.csv'}),
            step(5,'import_csv_to_postgres','Create a fresh encounter table from the validated decoded records, not the grouped summary',{'connection_sha256':connection_sha256(settings),'target_schema':'agent_sandbox','target_table':table,'source_step':'step_3','columns':columns,'key_columns':['encounter_id'],'null_values':[''],'soft_delete_marker':'is_deleted'},depends=['step_3','step_4']),
            step(6,'export_postgres_to_csv','Export the validated new table and preserve null semantics',{'target_schema':'agent_sandbox','target_table':table,'source_step':'step_5','columns':EXPORTED,'target_path':output+'_roundtrip.csv','null_token':'\\N'})]})
