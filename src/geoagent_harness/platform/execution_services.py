"""Replaceable local services. Admission never replaces exact operation approval."""
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
import time
from typing import Callable, Protocol, Literal

from geoagent_harness.contracts.task_context import Actor, RunContext, PolicyDecision


class Clock(Protocol):
    def now(self) -> datetime: ...
    def monotonic(self) -> float: ...


class Policy(Protocol):
    def decide(self, actor: Actor, run: RunContext, action: str) -> PolicyDecision: ...


class CredentialBroker(Protocol):
    def issue(self, actor: Actor, run: RunContext, resource: str) -> None: ...


class JobQueue(Protocol):
    def submit(self, callback: Callable, *args, **kwargs) -> object: ...


class ActionLedger(Protocol):
    def claim(self, *, identity: str, run: RunContext, actor: Actor, action: str,
              fingerprint: str, parent: str | None, key: str | None, at: str, decision: PolicyDecision) -> None: ...
    def finish(self, identity: str, *, phase: str, at: str) -> None: ...
    def link(self, identity: str, *, kind: str, reference: str, at: str) -> None: ...
    def events(self, run_id: str, *, limit: int = 1000) -> list[dict]: ...


class LedgerFactory(Protocol):
    def __call__(self, project_root: Path, *, namespace: Literal['local','mcp'] = 'local') -> ActionLedger: ...


class SystemClock:
    def now(self): return datetime.now(timezone.utc)
    def monotonic(self): return time.monotonic()


class LocalPolicy:
    def decide(self, actor, run, action):
        if actor != Actor():
            return PolicyDecision('deny', 'local_owner_required')
        return PolicyDecision('allow', 'local_owner_admission_only')


class LocalCredentialBroker:
    def issue(self, actor, run, resource):
        # Existing typed workers retain their approved password-file boundary.
        # This seam issues no credential, role, token or extra permission locally.
        return None


class InProcessQueue:
    def submit(self, callback, *args, **kwargs):
        context = copy_context()
        thread = Thread(target=context.run, args=(callback, *args), kwargs=kwargs, daemon=True)
        thread.start()
        return thread


def _ledger(project, *, namespace='local'):
    from geoagent_harness.platform.storage.action_ledger import LocalActionLedger
    return LocalActionLedger(project, namespace=namespace)


def _queries(project):
    from geoagent_harness.platform.storage.action_ledger import TransientActionLedger
    return TransientActionLedger(project)


@dataclass(frozen=True)
class ExecutionServices:
    clock: Clock = field(default_factory=SystemClock)
    policy: Policy = field(default_factory=LocalPolicy)
    credentials: CredentialBroker = field(default_factory=LocalCredentialBroker)
    queue: JobQueue = field(default_factory=InProcessQueue)
    ledger: LedgerFactory = _ledger
    queries: Callable[[Path], ActionLedger] = _queries
    audit_namespace: Literal['local','mcp'] = 'local'


_services: ContextVar[ExecutionServices] = ContextVar('execution_services', default=ExecutionServices())


def execution_services() -> ExecutionServices:
    return _services.get()


@contextmanager
def using_execution_services(services: ExecutionServices):
    """Trusted first-party composition/test hook; never selectable by request/model."""
    token = _services.set(services)
    try: yield services
    finally: _services.reset(token)
