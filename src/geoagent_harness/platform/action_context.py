"""Scoped action lineage and shared admission budget across copied worker contexts."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

from geoagent_harness.contracts.task_context import Actor, RunContext, ActionContextError
from geoagent_harness.platform.execution_services import execution_services
from geoagent_harness.platform.project_identity import resolve_identity


@dataclass
class RunState:
    started: float
    actions: int = 0
    lock: Lock = field(default_factory=Lock)


@dataclass(frozen=True)
class ActionFrame:
    actor: Actor
    run: RunContext
    state: RunState
    action_id: str | None = None
    durable: bool = False


_active: ContextVar[ActionFrame | None] = ContextVar('active_task_action', default=None)


def current_action() -> ActionFrame | None:
    return _active.get()


@contextmanager
def using_action_frame(frame):
    token = _active.set(frame)
    try: yield frame
    finally: _active.reset(token)


@contextmanager
def request_context(project_root, *, trigger, actor=None, run_context=None):
    actor = actor if actor is not None else Actor()
    run = run_context if run_context is not None else RunContext(str(Path(project_root).resolve()), trigger=trigger)
    if not isinstance(actor, Actor) or not isinstance(run, RunContext):
        raise ActionContextError('Context must come from trusted application contracts')
    if Path(run.project_root).resolve() != Path(project_root).resolve():
        raise ActionContextError('Run context belongs to a different project')
    resolve_identity(project_root)
    started=execution_services().clock.monotonic() if run.budget.wall_seconds is not None else 0.0
    with using_action_frame(ActionFrame(actor, run, RunState(started))) as frame:
        yield frame
