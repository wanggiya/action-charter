"""Trusted application context, not model/request authorization fields."""
from dataclasses import dataclass, field
import math
import re
from typing import Literal
from uuid import uuid4

from geoagent_harness.contracts.errors import TaskActionError


class ActionContextError(TaskActionError):
    pass


class DuplicateAction(ActionContextError):
    """An existing claim is never permission to repeat dispatch."""
    def __init__(self, run_id, identity, status):
        self.run_id, self.identity, self.status = run_id, identity, status
        super().__init__(f'Action already claimed in run {run_id} ({status}); inspect that run. Nothing was repeated.')


class ActionStorageError(ActionContextError):
    pass


@dataclass(frozen=True)
class Actor:
    actor_id: str = 'owner'
    kind: Literal['owner', 'user', 'service', 'automation'] = 'owner'

    def __post_init__(self):
        if (not isinstance(self.actor_id, str) or not re.fullmatch(r'[A-Za-z0-9_.:@-]{1,80}', self.actor_id)
                or self.kind not in {'owner', 'user', 'service', 'automation'}):
            raise ActionContextError('Invalid trusted actor identity')


@dataclass(frozen=True)
class RunBudget:
    max_actions: int | None = None
    wall_seconds: float | None = None

    def __post_init__(self):
        if self.max_actions is not None and (type(self.max_actions) is not int or not 1 <= self.max_actions <= 100000):
            raise ActionContextError('Invalid action budget')
        if self.wall_seconds is not None and (type(self.wall_seconds) not in {int, float}
                or not math.isfinite(self.wall_seconds) or not 0 < self.wall_seconds <= 86400):
            raise ActionContextError('Invalid wall-clock budget')


@dataclass(frozen=True)
class RunContext:
    project_root: str
    run_id: str = field(default_factory=lambda: uuid4().hex)
    trigger: Literal['direct', 'http', 'cli', 'mcp', 'terminal', 'background'] = 'direct'
    budget: RunBudget = field(default_factory=RunBudget)
    idempotency_key: str | None = None

    def __post_init__(self):
        if (not isinstance(self.project_root, str) or not self.project_root
                or not isinstance(self.run_id, str) or not re.fullmatch(r'[a-f0-9]{32}', self.run_id)
                or self.trigger not in {'direct', 'http', 'cli', 'mcp', 'terminal', 'background'}
                or not isinstance(self.budget, RunBudget)):
            raise ActionContextError('Invalid trusted run context')
        if self.idempotency_key is not None and (not isinstance(self.idempotency_key, str)
                or not re.fullmatch(r'[A-Za-z0-9_.:@-]{1,160}', self.idempotency_key)):
            raise ActionContextError('Invalid idempotency key')


@dataclass(frozen=True)
class PolicyDecision:
    outcome: Literal['allow', 'deny', 'escalate']
    reason: str

    def __post_init__(self):
        if self.outcome not in {'allow', 'deny', 'escalate'} or not re.fullmatch(r'[a-z0-9_-]{1,80}', self.reason):
            raise ActionContextError('Invalid policy decision')
