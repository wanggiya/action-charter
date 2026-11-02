"""Closed, model-free inspection proposals. No execution or inferred authority."""
import re
from time import monotonic

from geoagent_harness.planner.schemas import WorkflowPlan,PlanStep,PlannerResult
from geoagent_harness.discovery.source import relative_path
from .inspection_policy import source_skill

# Separate from the older inspection contract so an already-running process
# cannot advertise analytical routing that was added after it started.
ANALYTICAL_PLANNING_REVISION = 'table-profile-routing-v2'

FIELDS={
    'inspect_csv':{'metadata','row count','column names','columns','preview','a preview'},
    'inspect_vector':{'metadata','feature count','fields','crs','bounds','geometry type','layer names','driver'},
    'inspect_raster':{'metadata','crs','width','height','dimensions','band count','bands','bounds','resolution','driver','nodata'},
}
FILENAME=r'[^\s,;]+\.(?:csv|tsv|xlsx|jsonl|ndjson|json|geojson|gpkg|shp|tiff|tif)'
FIELD='|'.join(sorted(set.union(*FIELDS.values()),key=len,reverse=True))
PATTERN=re.compile(r'\s*inspect\s+(?P<files>'+FILENAME+r'(?:\s*,\s*'+FILENAME+r'|\s+and\s+'+FILENAME+r'){0,3})\.?\s*'
    r'(?:return\s+(?P<fields>(?:'+FIELD+r')(?:\s*(?:,|and)\s*(?:'+FIELD+r'))*)\.\s*)?(?:no writes\.?\s*)?',re.I)


def plan_for_request(message,available):
    aggregate = re.fullmatch(
        r'\s*aggregate (?P<path>[^\s;]+\.(?:csv|tsv))\.\s*'
        r'group by (?P<groups>[a-zA-Z0-9_, ]+)\.\s*'
        r'count (?P<count>[a-zA-Z0-9_]+) as (?P<count_out>[a-zA-Z0-9_]+)\.\s*'
        r'(?:mean (?P<mean>[a-zA-Z0-9_]+) as (?P<mean_out>[a-zA-Z0-9_]+)\.\s*)?'
        r'save to (?P<target>[^\s;]+\.csv)\.?\s*', message, re.I)
    if aggregate and 'aggregate_csv' in available:
        try:
            from geoagent_harness.tabular.schemas import Aggregate
            metrics = [{'column':aggregate['count'],'function':'count','output_column':aggregate['count_out']}]
            if aggregate['mean']:
                metrics.append({'column':aggregate['mean'],'function':'mean','output_column':aggregate['mean_out']})
            arguments = Aggregate(path=relative_path(aggregate['path'],'input'), streaming=True,
                by=[s.strip() for s in aggregate['groups'].split(',')], aggregations=metrics,
                target_path=relative_path(aggregate['target'],'output'),
                delimiter='\t' if aggregate['path'].endswith('.tsv') else ',').model_dump(mode='json',exclude_none=True)
        except ValueError:
            return None
        return WorkflowPlan(summary='Full-file grouped CSV export', steps=[PlanStep(step_id='step_1',skill='aggregate_csv',
            purpose='Aggregate the complete source into a fresh CSV; explicit authorization required',arguments=arguments,depends_on=[])])
    profile = re.fullmatch(
        r'\s*profile\s+(?P<path>[^\s;]+\.(?:csv|tsv))'
        r'(?:\s+using\s+(?P<codebook>[^\s;]+\.csv))?\.\s*'
        r'(?:group by (?P<groups>[a-zA-Z0-9_, ]+)\.\s*)?'
        r'(?:summarize (?P<numeric>[a-zA-Z0-9_, ]+)\.\s*)?'
        r'(?:count distinct (?P<distinct>[a-zA-Z0-9_, ]+)\.\s*)?'
        r'(?:no writes\.?\s*)?', message, re.I)
    if profile and 'inspect_csv' in available:
        try:
            from geoagent_harness.tabular.analysis_contracts import AnalysisOptions
            analysis = {'codebook_path': relative_path(profile['codebook'], 'input') if profile['codebook'] else None}
            for field, group in [('group_by', 'groups'), ('numeric_columns', 'numeric'), ('distinct_columns', 'distinct')]:
                analysis[field] = [s.strip() for s in profile[group].split(',')] if profile[group] else []
            options = AnalysisOptions.model_validate(analysis)
            path = relative_path(profile['path'], 'input')
        except ValueError:
            return None
        return WorkflowPlan(summary='Full-file analytical profile of ' + path.rsplit('/',1)[-1], steps=[
            PlanStep(step_id='step_1', skill='inspect_csv', purpose='Profile the full table with source-linked code definitions',
                arguments={'path':path, 'delimiter':'\t' if path.endswith('.tsv') else ',',
                           'analysis': options.model_dump(mode='json', exclude_none=True)}, depends_on=[])])
    match=PATTERN.fullmatch(message)
    if not match:return None
    try:
        paths=[relative_path(item,'input') for item in re.split(r'\s*,\s*|\s+and\s+',match['files'])]
    except ValueError:return None
    if len(set(paths))!=len(paths) or any(len(path)>960 for path in paths):return None
    requested=set(re.split(r'\s*,\s*|\s+and\s+',match['fields'].casefold())) if match['fields'] else {'metadata'}
    steps=[]
    for index,path in enumerate(paths):
        skill=source_skill(path)
        if skill not in available or not requested.issubset(FIELDS[skill]):return None
        arguments={'path':path}
        if path.lower().endswith('.tsv'):arguments['delimiter']='\t'
        steps.append(PlanStep(step_id=f'step_{index+1}',skill=skill,purpose='Inspect local dataset metadata',arguments=arguments,depends_on=[]))
    return WorkflowPlan(summary=('Inspect '+', '.join(path.rsplit('/',1)[-1] for path in paths))[:2000],steps=steps)


def save_turn(root,path,state,request,base,selected,available,models,plan):
    # Use the existing revision lease, policy and persistence. Called only inside
    # conversation_turn's active-turn guard; never from a model reply.
    from . import conversation as c
    from .planning_tasks import write_turn
    started=monotonic()
    from geoagent_harness.planner.bindings import bind_required_gates
    from geoagent_harness.skill_registry import load_skill_registry
    bind_required_gates(plan,load_skill_registry(root))
    if base:
        for step in plan.steps:
            for previous in base.plan.steps:
                if step.skill==previous.skill and step.arguments==previous.arguments:
                    step.requires_approval |= previous.requires_approval
                    step.validation_required |= previous.validation_required
    read_only = all(s.skill.startswith('inspect_') for s in plan.steps)
    result=PlannerResult(model='deterministic-inspection-v1' if read_only else 'deterministic-table-v1',original_request=request.message,
        context_references=[],plan=plan)
    c._check(result,root)
    from geoagent_harness.planner.policy import validate_plan_policy
    validate_plan_policy(plan,available_skills=set(available))
    changed=base is None or c.plan_sha256(base.plan)!=c.plan_sha256(plan)
    with c._LOCK:
        latest=c._read(path,request.conversation_id)
        if latest.revision!=request.expected_revision:
            from .server import InterfaceApiError
            raise InterfaceApiError('Conversation changed; reload before sending')
        provenance={'task_id':state.active_task_id,'conversation_id':request.conversation_id if state.active_task_id else None}
        read_only = all(s.skill.startswith('inspect_') for s in plan.steps)
        reply = ('Exact inspection workflow prepared without a model call. Execution status is recorded separately in Outcome.' if read_only
                 else 'Exact table workflow prepared without a model call. Review the output, enable writes, Authorize and Execute.')
        state.messages.extend([c.Entry(role='user',content=request.message,selected_skill_ids=selected,**provenance),
            c.Entry(role='assistant',content=reply,plan_skill_ids=list(dict.fromkeys(step.skill for step in plan.steps)),**provenance)])
        state.planner_result=result;state.selected_skill_ids=selected;state.allowed_skill_ids=available
        state.capability_candidate=None
        if changed:state.recipe_candidate=None
        state.context_usage={'history_enabled':request.use_history,'included_messages':0,'omitted_messages':len(state.messages)-2,
            'excerpts_truncated':False,'prompt_bytes':0,'prompt_limit_bytes':c.MAX_PROMPT_BYTES,
            'current_workflow_included':False,'opening_message_included':False,
            'model_request':{'planner_contract':c.PLANNER_CONTRACT_REVISION,'stage':'deterministic_inspection' if read_only else 'deterministic_table',
                'prompt_bytes':0,'supplied_schema_count':0,'available_operation_count':len(available),
                'retrieved_method_count':0,'elapsed_seconds':monotonic()-started,'model_calls':0}}
        state.revision+=1;state.task_title=state.messages[0].content[:160]
        if state.active_task_id:
            value=state.model_dump(mode='json')
            write_turn(root,value,expected_revision=request.expected_revision,expected_task_revision=request.expected_task_revision if request.expected_task_revision is not None else request.expected_revision)
            state.task_revision=value['task_revision']
        else:c._write(path,state)
    return c._response(state,changed,models,root)
