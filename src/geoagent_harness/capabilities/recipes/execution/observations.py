"""Bounded recorded-run facts for advisory assessment and method indexing."""
import hashlib, json


def evidence(record):
    steps=[]
    for step in record['steps']:
        outcome=step.get('outcome') or {}
        validation=step.get('validation_outcome') or {}
        metadata={key:outcome[key] for key in ('row_count','column_count','columns','missing_counts') if key in outcome} if isinstance(outcome,dict) else {}
        from geoagent_harness.data.tabular.statistics import statistical_evidence
        statistical=statistical_evidence(outcome) if isinstance(outcome,dict) else None
        if statistical:metadata['statistics']=statistical
        if isinstance(outcome,dict) and outcome.get('readiness_assessment'):
            from geoagent_harness.data.tabular.readiness import compact_assessment
            metadata['readiness']=compact_assessment(outcome['readiness_assessment'])
        steps.append({'step_id':step['step_id'],'skill':step['skill_id'],'status':step['status'],
                      'validation_passed':validation.get('passed') if isinstance(validation,dict) else None,'metadata':metadata})
    value={'evidence_kind':'recorded_run_observations','run_id':record['run_id'],'plan_sha256':record['plan_sha256'],
           'deterministic_status':record['status'],'failed_step_id':record['failed_step_id'],'steps':steps,
           'limitations':['Historical observations are not current target verification, general recipe validation or execution authority.']}
    if len(json.dumps(value).encode())>12_000:
        for step in value['steps']:
            statistical=step['metadata'].get('statistics')
            step['metadata']={'statistics':statistical} if statistical else {}
        value['limitations'].append('Other metadata exceeded the review budget and was omitted.')
    if len(json.dumps(value).encode())>12_000:
        for step in value['steps']:
            step['metadata']={}
        value['limitations'].append('Detailed statistics exceeded the combined review budget; consult recorded reports before analytical conclusions.')
    return value

def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
