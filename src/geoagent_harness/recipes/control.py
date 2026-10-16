"""Optional in-process execution observer; it supplies no execution authority."""
from contextvars import ContextVar


class ExecutionCancelled(RuntimeError):
    """Cancellation at a safe operation boundary, after any active verification."""


observer: ContextVar[object | None] = ContextVar('recipe_execution_observer', default=None)


def checkpoint():
    active = observer.get()
    if active is not None:
        active.checkpoint()


def progress(step_id, skill_id, status, outcome=None, validation=None):
    active = observer.get()
    if active is not None:
        active.progress(step_id, skill_id, status, outcome, validation)
