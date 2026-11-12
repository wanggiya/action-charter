"""Task admission, context propagation and audit; exact domain authority stays mandatory."""
from datetime import datetime
from enum import Enum
from functools import wraps
import hashlib
import inspect
import json
from pathlib import Path
import re
from typing import get_type_hints
from uuid import uuid4

from geoagent_harness.contracts.task_context import Actor, RunContext, ActionContextError
from geoagent_harness.platform.action_context import ActionFrame, RunState, current_action, using_action_frame
from geoagent_harness.platform.execution_services import execution_services
from geoagent_harness.platform.project_identity import resolve_identity


def _encoded(value):
    if hasattr(value,'model_dump'): return value.model_dump(mode='json')
    if isinstance(value,Path): return str(value)
    if isinstance(value,datetime): return value.isoformat()
    if isinstance(value,Enum): return value.value
    if isinstance(value,(set,frozenset)): return sorted(value)
    return {'internal_type':type(value).__module__+'.'+type(value).__qualname__}


def task_entrypoint(function=None, *, trigger='direct', name=None, audit=True):
    def decorate(function):
        signature=inspect.signature(function)
        action=name or function.__module__+'.'+function.__name__
        @wraps(function)
        def wrapped(*args, actor=None, run_context=None, **kwargs):
            bound=signature.bind(*args,**kwargs)
            active=current_action()
            location=bound.arguments.get('project_root',bound.arguments.get('root'))
            settings=bound.arguments.get('settings')
            if location is None and settings is not None: location=settings.project_root
            route=bound.arguments.get('context')
            if location is None and route is not None and hasattr(route,'project_root'):location=route.project_root
            if location is None: location=active.run.project_root if active else Path.cwd()
            project=Path(location).resolve()
            resolve_identity(project)
            chosen_actor=actor if actor is not None else active.actor if active else Actor()
            run=run_context if run_context is not None else active.run if active else RunContext(str(project),trigger=trigger)
            if not isinstance(chosen_actor,Actor) or not isinstance(run,RunContext):
                raise ActionContextError('Context must come from trusted application contracts')
            if Path(run.project_root).resolve()!=project:
                raise ActionContextError('Run context belongs to a different project')
            if active and (chosen_actor!=active.actor or run!=active.run):
                raise ActionContextError('Nested actions cannot replace actor or run context')
            services=execution_services()
            state=active.state if active else RunState(services.clock.monotonic() if run.budget.wall_seconds is not None else 0.0)
            with state.lock:
                if run.budget.max_actions is not None and state.actions>=run.budget.max_actions:
                    raise ActionContextError('Run action budget exhausted; nothing dispatched')
                if run.budget.wall_seconds is not None and services.clock.monotonic()-state.started>=run.budget.wall_seconds:
                    raise ActionContextError('Run wall-clock budget exhausted; nothing dispatched')
                state.actions+=1
            identity=uuid4().hex
            decision=services.policy.decide(chosen_actor,run,action)
            arguments={key:value for key,value in bound.arguments.items() if key not in {'handler','context'} and not callable(value)}
            handler=bound.arguments.get('handler')
            if handler is not None: arguments['route']=handler.path
            fingerprint=hashlib.sha256(json.dumps(arguments,sort_keys=True,default=_encoded,separators=(',',':')).encode()).hexdigest()
            durable=bool(audit(bound.arguments) if callable(audit) else audit) or run.idempotency_key is not None or bool(active and active.durable)
            ledger=services.ledger(project,namespace=services.audit_namespace) if durable else services.queries(project)
            ledger.claim(identity=identity,run=run,actor=chosen_actor,action=action,fingerprint=fingerprint,
                parent=active.action_id if active and (not durable or active.durable) else None,
                key=run.idempotency_key if active is None or active.action_id is None else None,
                at=services.clock.now().isoformat(),decision=decision)
            if decision.outcome!='allow':
                ledger.finish(identity,phase='blocked',at=services.clock.now().isoformat())
                raise ActionContextError(f'Action admission {decision.outcome}: {decision.reason}; exact authorization is still required')
            frame=ActionFrame(chosen_actor,run,state,identity,durable)
            with using_action_frame(frame):
                try: result=function(*args,**kwargs)
                except BaseException:
                    try:ledger.finish(identity,phase='failed',at=services.clock.now().isoformat())
                    except Exception:pass  # preserve original failure; consumed claim still blocks replay
                    raise
                if isinstance(result,dict):
                    for key in ('run_id','conversation_id','plan_filename','plan_sha256','recipe_filename','approval_id'):
                        value=result.get(key)
                        if isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,200}',value):
                            ledger.link(identity,kind=key,reference=value,at=services.clock.now().isoformat())
                ledger.finish(identity,phase='completed',at=services.clock.now().isoformat())
                return result
        # Preserve external CLI/MCP schemas; actor/context are trusted Python-only kwargs.
        hints=get_type_hints(function,include_extras=True)
        wrapped.__signature__=signature.replace(parameters=[p.replace(annotation=hints.get(key,p.annotation)) for key,p in signature.parameters.items()],return_annotation=hints.get('return',signature.return_annotation))
        wrapped.__task_entrypoint__=True
        return wrapped
    return decorate(function) if function is not None else decorate


def credential_request(resource):
    """Called only inside the existing verified write-operation boundary."""
    active=current_action()
    if active is not None:
        return execution_services().credentials.issue(active.actor,active.run,resource)
    return None


def record_reference(kind, reference):
    active=current_action()
    if active is None or active.action_id is None:return
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',kind) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,240}',reference):
        raise ActionContextError('Invalid action evidence reference')
    services=execution_services()
    ledger=(services.ledger(Path(active.run.project_root),namespace=services.audit_namespace)
            if active.durable else services.queries(Path(active.run.project_root)))
    ledger.link(active.action_id,kind=kind,reference=reference,at=services.clock.now().isoformat())
