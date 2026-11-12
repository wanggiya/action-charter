"""Typed advisory analysis goals over recorded inspection evidence; never execution."""
import re
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field

METHODS={
 'data_quality':('supported',['missingness','key/duplicate checks','field-role review']),
 'describe':('supported',['count','mean','percentiles','variance','standard deviation']),
 'group_counts':('supported',['group counts','row/column/overall percentages']),
 'pearson':('supported',['correlation coefficient','conditional unadjusted P-value']),
 'spearman':('supported',['rank correlation coefficient','conditional unadjusted P-value']),
 'linear_regression':('supported',['coefficient','standard error','confidence interval','conditional P-value','R-squared','residual standard error']),
 'categorical_association':('not_available',['contingency association test','effect size','assumption checks']),
 'classification_evaluation':('not_available',['held-out precision','recall','F1','confusion matrix','calibration']),
 'causal_analysis':('not_available',['design-specific causal estimand','identification assumptions'])}

class AnalysisGoal(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title:str=Field(min_length=1,max_length=120)
    question:str=Field(min_length=1,max_length=240)
    method:Literal['data_quality','describe','group_counts','pearson','spearman','linear_regression','categorical_association','classification_evaluation','causal_analysis']
    fields:list[str]=Field(min_length=1,max_length=12)
    rationale:str=Field(min_length=1,max_length=200)
    prerequisites:list[str]=Field(default_factory=list,max_length=2)
    target_candidate:str|None=Field(default=None,max_length=200)


def requested(message):
    return bool(re.match(r'^\s*(?:please\s+)?(?:propose|suggest|recommend|which|what|let)\b',message,re.I)
        and re.search(r'\banalys(?:is|es)\s+goals?\b|\bgoals?\b.{0,30}\binspection\b',message,re.I)
        and not re.search(r'\b(?:execute|compute|calculate|fit|write|export|install|train)\b',message,re.I))


def capabilities():
    return {method:{'availability':status,'metrics_when_calculated':metrics} for method,(status,metrics) in METHODS.items()}


def validate(goals,source_sha256,context):
    if not context:
        if goals:raise ValueError('Inspect a dataset before proposing source-bound analysis goals')
        return None
    matches=[r for r in context['results'] if (r.get('field_guidance') or {}).get('source_sha256')==source_sha256]
    if len(matches)!=1:raise ValueError('Choose one exact recorded inspection source; do not substitute a source or hash')
    if not goals:raise ValueError('Propose at least one source-bound analysis goal, rather than only a generic explanation')
    result=matches[0];g=result['field_guidance'];fields={f['name']:f for f in g['field_evidence']}
    output=[]
    for index,goal in enumerate(goals):
        if len(set(goal.fields))!=len(goal.fields) or set(goal.fields)-set(fields):raise ValueError('Goal fields must be distinct observed fields in the selected source')
        if any(len(p)>200 for p in goal.prerequisites):raise ValueError('Keep prerequisites bounded')
        if goal.target_candidate and goal.target_candidate not in goal.fields:raise ValueError('A target candidate must be one of the goal fields')
        status,metrics=METHODS[goal.method];requirements=list(goal.prerequisites)
        if goal.method in {'describe','pearson','spearman','linear_regression'} and g['matching_rows']>200000:
            status='needs_scope';requirements+=['Recorded matching rows exceed the registered 200,000-row statistical limit. Choose a justified filter or an explicitly approved sample; never silently substitute data.']
        numeric={'numerical','count'}
        if goal.method in {'describe','pearson','spearman','linear_regression'}:
            if any(fields[n]['role'] not in numeric for n in goal.fields):raise ValueError('Numeric methods require observed numerical/count candidates; do not use identifiers, codes or categories as measurements')
            if goal.method in {'pearson','spearman','linear_regression'} and len(goal.fields)<2:raise ValueError('Association/regression goals need at least two observed measurement candidates')
            requirements+=['Confirm measurement meaning, units and analysis unit. Declare missing-value policy before calculation.']
        if goal.method in {'pearson','spearman','linear_regression','categorical_association'}:
            requirements+=['Check repeated entities and independence; define the comparison/hypothesis. P-values are conditional and do not establish causality.']
        if goal.method=='linear_regression':
            if not goal.target_candidate:raise ValueError('Propose an observed numeric target candidate for regression; its meaning still requires confirmation')
            requirements+=['Confirm the proposed outcome and predictors; choose justified covariance and review residual/model diagnostics.']
        if goal.method=='group_counts':
            if len(goal.fields)>2:raise ValueError('Category grouping goals support at most two fields')
            requirements+=['State the denominator and distinguish observations from distinct entities.']
        if goal.method=='classification_evaluation':requirements+=['Define labels, prediction horizon and allowed predictors. Use a held-out or cross-validated split respecting entities/time; prevent target leakage. No registered training/evaluation operation is available yet.']
        if status=='not_available':requirements+=['This method needs an implemented and validated operation before workflow preparation; do not substitute an unrelated method.']
        output.append({**goal.model_dump(mode='json'),'id':f'goal_{index+1}','availability':status,
            'metrics':metrics,'prerequisites':list(dict.fromkeys(requirements)),
            'status':'proposal_not_calculated','execution_authority':False})
    return {'schema_version':'analysis-goals-v1','run_id':context['run_id'],'plan_sha256':context['plan_sha256'],'step_id':result['step_id'],
        'source':g['source'],'source_sha256':g['source_sha256'],'source_rows':g['source_rows'],'matching_rows':g['matching_rows'],'source_options':g.get('source_options'),'goals':output,'computed':False,'execution_performed':False,'authority_granted':False}
