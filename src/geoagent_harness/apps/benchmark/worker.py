"""One fixed benchmark pipeline in a separate process, not an arbitrary-code sandbox."""
import json
import os
from pathlib import Path
import time
from dataclasses import replace,asdict

from geoagent_harness.platform.storage.files import FileJsonRecords

SAFE_SKILLS = ('inspect_csv','inspect_vector','inspect_raster','select_csv_columns',
    'filter_csv_rows','handle_csv_missing','join_csv','aggregate_csv','export_csv',
    'calculate_csv_columns','vector_attributes_to_csv','convert_vector','convert_raster')
DATABASE_SKILLS=('validate_postgres_import','import_csv_to_postgres','inspect_postgres_table',
    'export_postgres_to_csv','load_vector_to_postgis','validate_postgis_layer')


def bind_profile(root,settings):
    """Prepare a fresh worker or verify an already prepared qualification root."""
    if settings is None or settings.provider_profile_id=='local':return
    from geoagent_harness.platform.model_gateway import profiles
    from geoagent_harness.contracts.model_providers import ProviderProfile,ProviderUpdate,ProviderSelection,ProviderLimits
    state=profiles.read(root)
    if state.profiles:
        if state.selected!=settings.provider_profile_id:
            raise ValueError('Worker profile differs from pinned configuration')
        actual=profiles.capture(root).settings()
        def comparable(value):return {key:v for key,v in asdict(value).items() if key!='credential_root'}
        if comparable(actual)!=comparable(settings):
            raise ValueError('Worker profile differs from pinned configuration')
        return
    profile=ProviderProfile(id=settings.provider_profile_id,base_url=settings.base_url,
        kind=settings.provider_kind,location=settings.provider_location,data_allowed=settings.data_allowed,
        model=settings.model,listing=settings.listing,capabilities=settings.response_format,
        credential_ref=settings.credential_ref,
        limits=ProviderLimits(timeout_s=settings.timeout_seconds,max_tokens=settings.max_tokens))
    profiles.save(root,ProviderUpdate(profile=profile,expected_revision=state.revision))
    profiles.select(root,ProviderSelection(profile_id=profile.id,expected_revision=state.revision+1))


def failure_details(error,observation):
    """Only trusted field descriptions/fixed codes, never exception/model text."""
    from pydantic import ValidationError
    from geoagent_harness.agents.roles.planner.agent import _schema_findings
    from geoagent_harness.platform.model_gateway.telemetry import error_code
    from geoagent_harness.contracts.benchmark import BenchmarkFailureDetails
    reasons={'capability_gap_unresolved','unverified_reuse_claim','request_coverage_incomplete',
             'schema_repair_deferred','output_truncated'}
    rules={'Referenced operation must produce a CSV table':'csv_producer_required',
           'Input format does not match the operation data contract':'input_format_mismatch',
           'file paths must be safe normalized relative paths':'unsafe_input_path',
           'Output paths must remain under data/output':'unsafe_output_path',
           'Calculation references unknown source columns or collides with the source schema':'missing_calculation_columns'}
    current=error;seen=set();findings=[];policy=None
    while current is not None and id(current) not in seen and len(seen)<8:
        seen.add(id(current))
        if isinstance(current,ValidationError) and not findings:findings=[text[:1024] for text in _schema_findings(current)]
        if str(current) in rules:policy=rules[str(current)]
        current=current.__cause__
    stage='planning' if not observation.get('planning_status') else 'advisory_review' if observation.get('observed_outcome')=='completed' else 'execution'
    reason=getattr(error,'reason',None)
    return BenchmarkFailureDetails(stage=stage,category=error_code(error),
        correction_attempted=getattr(error,'correction_attempted',False) is True,
        planner_reason=reason if isinstance(reason,str) and reason in reasons else None,policy_rule=policy,
        schema_findings=findings).model_dump(mode='json')


class BudgetExceeded(RuntimeError):
    pass


class BudgetClient:
    def __init__(self, settings, plan, limit, deadline, root, facts=None, model_socket=None, qualification=False):
        self.settings, self.plan, self.limit, self.deadline, self.root = settings, plan, limit, deadline, root
        self.calls = [];self.exhausted=False;self.facts=facts or {}
        self.model_socket = model_socket  # Trusted qualification runner only; never a model argument.
        self.qualification = qualification

    def complete(self, request):
        if self.facts:
            from geoagent_harness.platform.model_gateway.schemas import ChatMessage
            payload=json.loads(request.messages[0].content)
            payload['benchmark_resources']=self.facts
            request=request.model_copy(update={'messages':[ChatMessage(role='system',content=json.dumps(payload)),*request.messages[1:]]})
        from geoagent_harness.platform.model_gateway import SharedModelClient
        from geoagent_harness.platform.model_gateway.schemas import ModelResult
        from geoagent_harness.platform.model_gateway.telemetry import _phase
        if len(self.calls) >= self.limit or time.monotonic() >= self.deadline:
            self.exhausted=True;self.persist()
            raise BudgetExceeded('Benchmark call/deadline limit')
        role, phase = _phase.get()
        role = role if role in {'planner','critic','executor'} else 'planner'
        call = {'role':role,'phase':phase,'prompt_tokens':None,'completion_tokens':None,'elapsed_seconds':None,
                'correction':False,'timeout':False}
        try:
            latest=json.loads(request.messages[-1].content)
            call['correction']=isinstance(latest,dict) and ('validation_findings' in latest or 'rejected_candidate' in latest or ('failure_kind' in latest and 'deterministic_findings' in latest))
        except (ValueError,TypeError):pass
        self.calls.append(call);self.persist()
        started = time.monotonic()
        try:
            if self.plan is not None:
                if role == 'critic':
                    response = {'deterministic_status':'completed','conclusion':'supported',
                        'summary':'Fixture review of supplied recorded evidence.', 'findings':[],
                        'limitations':['Fixture review; not a real-model assessment.']}
                else:
                    response = {'message':'Synthetic fixture proposal; nothing authorized.', 'plan':self.plan}
                result = ModelResult(model='benchmark-fixture', content=json.dumps(response))
            else:
                remaining = max(.001, self.deadline-time.monotonic())
                import httpx
                transport = httpx.HTTPTransport(uds=self.model_socket) if self.model_socket else None
                result = SharedModelClient(replace(self.settings, timeout_seconds=min(self.settings.timeout_seconds,remaining)), transport=transport).complete(
                    request.model_copy(update={'timeout_seconds':min(request.timeout_seconds or 600,remaining,600)}))
            call.update(prompt_tokens=result.prompt_tokens,completion_tokens=result.completion_tokens)
            if self.qualification and role=='critic':
                from geoagent_harness.contracts.outcome_assessment import OutcomeAssessment, MethodSuggestion
                from pydantic import ValidationError
                try:
                    assessment=OutcomeAssessment.model_validate_json(result.content)
                    call['assessment_schema_valid']=True
                    call['assessment_status']=assessment.deterministic_status
                    call['assessment_operations']=[s if s in (*SAFE_SKILLS,*DATABASE_SKILLS) else '[unknown operation]'
                        for s in assessment.reusable_method.operations] if assessment.reusable_method else []
                except ValidationError as error:
                    fields=set(OutcomeAssessment.model_fields)|set(MethodSuggestion.model_fields)
                    call['assessment_schema_valid']=False
                    call['schema_findings']=[{'field':'.'.join(str(p) if type(p) is int or p in fields else '[unexpected field]' for p in e['loc']),
                        'type':e['type']} for e in error.errors(include_input=False,include_context=False)[:8]]
            return result
        except Exception as error:
            call['timeout']=getattr(error,'code',None)=='model_timeout'
            raise
        finally:
            call['elapsed_seconds'] = time.monotonic()-started
            self.persist()

    def persist(self):
        FileJsonRecords(self.root, max_bytes=512_000).replace('calls.json',json.dumps({'calls':self.calls}))


def work(root):
    from geoagent_harness.platform.model_settings import ModelSettings
    from geoagent_harness.task_actions.conversation import TurnRequest, conversation_turn
    from geoagent_harness.contracts.planning import PlannerResult
    from geoagent_harness.contracts.actions import InterfaceReviewedPlanSaveRequest
    from geoagent_harness.task_actions.artifacts import save_interface_reviewed_plan
    from geoagent_harness.core.policy.approvals import plan_sha256
    from geoagent_harness.task_actions.workflow import WorkflowRequest, prepare_workflow, authorize_workflow
    from geoagent_harness.task_actions.workflow_runs import RunRequest, run_action
    from geoagent_harness.task_actions.run_assessment import assess_run
    from geoagent_harness.core.policy.write_policy import session
    from geoagent_harness.platform.model_gateway.telemetry import error_code
    store = FileJsonRecords(root,max_bytes=2_000_000)
    job = store.read('job.json')
    settings = ModelSettings(**job['settings']) if job.get('settings') else None
    bind_profile(root,settings)
    if 'review_timeout_seconds' in job:
        from geoagent_harness.platform.model_gateway.catalog import select_review_timeout,ReviewTimeoutSelection
        select_review_timeout(root,ReviewTimeoutSelection(seconds=job['review_timeout_seconds'],expected_revision=0))
    plan=job.get('fixture_plan')
    facts={'inputs':job.get('inputs',[]),'execution_authority':False}
    skills=(*SAFE_SKILLS,*DATABASE_SKILLS) if job.get('database') else SAFE_SKILLS
    if 'allowed_skill_ids' in job:
        selected=job['allowed_skill_ids']
        if not isinstance(selected,list) or not selected or any(s not in skills for s in selected):
            raise ValueError('Qualification skills must be a nonempty subset of admitted operations')
        skills=tuple(selected)
    if job.get('database'):
        from geoagent_harness.platform.settings import load_settings
        from geoagent_harness.data.databases.postgres.service import connection_sha256
        facts['database']={'connection_sha256':connection_sha256(load_settings()),'schema':'agent_sandbox'}
    if plan is not None:
        # Fixed fixture reply binds actual resources, never expected answers/credentials.
        plan=json.loads(json.dumps(plan))
        inputs={v['path']:v['sha256'] for v in job.get('inputs',[])}
        for step in plan.get('steps',[]):
            args=step.get('arguments',{})
            if args.get('connection_sha256')=='$connection':args['connection_sha256']=facts['database']['connection_sha256']
            if isinstance(args.get('source_sha256'),str) and args['source_sha256'].startswith('$input:'):
                args['source_sha256']=inputs[args['source_sha256'][7:]]
    client = BudgetClient(settings,plan,job['model_calls'],time.monotonic()+job['wall_clock_s'],root,facts,job.get('model_socket'),job.get('qualification',False))

    identity='1'*32
    observation={'observed_outcome':'unknown','executed_operations':0,'output_files':0,'run':{},'reason_code':'worker_error','approvals_required':0}
    try:
        with session(root,enabled=job['allow_writes']):
            state = conversation_turn(TurnRequest(action='turn',conversation_id=identity,message=job['request'],
                allowed_skill_ids=list(skills),use_history=False),project_root=root,
                model_client=client,helper_client=client,recipe_client=client,critic_client=client)
            candidate=state.get('planner_result')
            if not candidate:
                observation.update(observed_outcome='unknown',reason_code='proposal_missing')
                return
            plan = PlannerResult.model_validate({k:candidate[k] for k in PlannerResult.model_fields if k in candidate})
            if any(s.skill not in skills for s in plan.plan.steps):
                observation.update(observed_outcome='refused',reason_code='operation_not_admitted');return
            saved=save_interface_reviewed_plan(InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=plan,
                confirmed_plan_sha256=plan_sha256(plan.plan),allowed_skill_ids=list(skills)),project_root=root)
            request=WorkflowRequest(action='prepare_workflow',conversation_id=identity,plan_filename=saved['plan_filename'],confirmed_plan_sha256=saved['plan_sha256'])
            review=prepare_workflow(request,project_root=root)
            observation['planning_status']='validated'
            observation['approvals_required']=len(review['approval_required_step_ids'])
            if review['write_step_ids'] and not job['allow_writes']:
                observation.update(observed_outcome='refused',reason_code='write_not_authorized');return
            auth={}
            if review['approval_required_step_ids']:
                auth=authorize_workflow(request.model_copy(update={'action':'authorize_workflow',
                    'confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,
                    'approver':'benchmark-fixture-operator','reason':'Explicit benchmark option; temporary synthetic file outputs only.'}),project_root=root)
            execute=request.model_copy(update={'action':'execute_workflow','confirm_execution':True,
                'confirmed_review_sha256':review['review_sha256'],
                'plan_approval_filename':auth.get('plan_approval_filename'),'recipe_approval_filename':auth.get('recipe_approval_filename')})
            observation.update(observed_outcome='unknown',executed_operations=None,reason_code='execution_started')
            store.replace('observation.json',json.dumps(observation))
            run=run_action(RunRequest(action='start',workflow=execute,conversation_id=identity),project_root=root,background=False)
            observation.update(run=run,executed_operations=sum('started_at' in s for s in run['steps']),
                observed_outcome='completed' if run['status']=='completed' else 'error',reason_code='workflow_'+run['status'])
            store.replace('observation.json',json.dumps(observation))  # persist execution before advisory review
            if run['status']=='completed' and len(client.calls)<client.limit:
                reviewed=assess_run(root,run['run_id'],model_client=client)
                observation['critic_status']=reviewed.get('critic_review',{}).get('status')
                observation['critic_reason_code']=reviewed.get('critic_review',{}).get('error_code')
    except Exception as error:
        from geoagent_harness.core.policy.plan import PlannerPolicyError
        code='planner_policy_rejected' if isinstance(error,PlannerPolicyError) else error_code(error)
        observation['failure_type']=type(error).__name__
        observation['failure_details']=failure_details(error,observation)
        observation['reason_code']='call_budget_exhausted' if client.exhausted or isinstance(error,BudgetExceeded) else code
        observation['observed_outcome']='refused' if code=='planner_policy_rejected' and observation['executed_operations']==0 else 'error'
    finally:
        observation['output_files']=sum(p.is_file() for p in (root/'data/output').rglob('*'))
        store.replace('observation.json',json.dumps(observation))


if __name__=='__main__':
    import sys
    work(Path(sys.argv[1]))
