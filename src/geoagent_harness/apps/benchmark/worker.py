"""One fixed benchmark pipeline in a separate process, not an arbitrary-code sandbox."""
import json
import os
from pathlib import Path
import time
from dataclasses import replace

from geoagent_harness.platform.storage.files import FileJsonRecords

SAFE_SKILLS = ('inspect_csv','inspect_vector','inspect_raster','select_csv_columns',
    'filter_csv_rows','handle_csv_missing','join_csv','aggregate_csv','export_csv',
    'calculate_csv_columns','vector_attributes_to_csv','convert_vector','convert_raster')
DATABASE_SKILLS=('validate_postgres_import','import_csv_to_postgres','inspect_postgres_table',
    'export_postgres_to_csv','load_vector_to_postgis','validate_postgis_layer')


class BudgetExceeded(RuntimeError):
    pass


class BudgetClient:
    def __init__(self, settings, plan, limit, deadline, root, facts=None):
        self.settings, self.plan, self.limit, self.deadline, self.root = settings, plan, limit, deadline, root
        self.calls = [];self.exhausted=False;self.facts=facts or {}

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
                result = SharedModelClient(replace(self.settings, timeout_seconds=min(self.settings.timeout_seconds,remaining))).complete(
                    request.model_copy(update={'timeout_seconds':min(request.timeout_seconds or 600,remaining,600)}))
            call.update(prompt_tokens=result.prompt_tokens,completion_tokens=result.completion_tokens)
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
    plan=job.get('fixture_plan')
    facts={'inputs':job.get('inputs',[]),'execution_authority':False}
    skills=(*SAFE_SKILLS,*DATABASE_SKILLS) if job.get('database') else SAFE_SKILLS
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
    client = BudgetClient(settings,plan,job['model_calls'],time.monotonic()+job['wall_clock_s'],root,facts)

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
    except Exception as error:
        from geoagent_harness.core.policy.plan import PlannerPolicyError
        code='planner_policy_rejected' if isinstance(error,PlannerPolicyError) else error_code(error)
        observation['failure_type']=type(error).__name__
        observation['reason_code']='call_budget_exhausted' if client.exhausted or isinstance(error,BudgetExceeded) else code
        observation['observed_outcome']='refused' if code=='planner_policy_rejected' and observation['executed_operations']==0 else 'error'
    finally:
        observation['output_files']=sum(p.is_file() for p in (root/'data/output').rglob('*'))
        store.replace('observation.json',json.dumps(observation))


if __name__=='__main__':
    import sys
    work(Path(sys.argv[1]))
