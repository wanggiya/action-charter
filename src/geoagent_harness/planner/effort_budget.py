"""Cumulative accounting for one conversational Planner turn, not execution authority."""
from __future__ import annotations

import math
import os
from time import monotonic

from geoagent_harness.failures import FailureCategory
from geoagent_harness.model import ModelClientError
from geoagent_harness.model.settings import ModelSettingsError


class EffortBudget:
    MAX_CALLS = 4
    MAX_DISCOVERY = 2

    def __init__(self):
        raw = os.environ.get('PLANNER_TURN_TIMEOUT_SECONDS', '').strip()
        try:
            self.deadline_seconds = float(raw) if raw else None
        except ValueError as error:
            raise ModelSettingsError('PLANNER_TURN_TIMEOUT_SECONDS must be numeric') from error
        if self.deadline_seconds is not None and (not math.isfinite(self.deadline_seconds) or not 0 < self.deadline_seconds <= 2400):
            raise ModelSettingsError('PLANNER_TURN_TIMEOUT_SECONDS must be between 0 and 2400')
        self.started = monotonic()
        self.model_calls = 0
        self.tool_calls = 0
        self.discovery_calls = 0
        self.fixture_batches = 0
        self.prompt_bytes = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.usage_complete = True
        self.stopping_reason = None

    def remaining(self):
        if self.deadline_seconds is None:
            return None
        return self.deadline_seconds - (monotonic() - self.started)

    def reject(self, reason):
        self.stopping_reason = reason
        raise ModelClientError(
            'Planner effort budget exhausted; current workflow preserved. Nothing executed.',
            code='planner_budget_exhausted', category=FailureCategory.POLICY_DENIED,
        )

    def check_time(self):
        remaining = self.remaining()
        if remaining is not None and remaining <= 0:
            self.reject('deadline')
        return remaining

    def complete(self, client, request, check_prompt):
        remaining = self.check_time()
        if self.model_calls >= self.MAX_CALLS:
            self.reject('model_call_limit')
        size = check_prompt(request)
        self.model_calls += 1  # Failed/time-out attempts consume the allowance.
        self.prompt_bytes += size
        bounded = request.model_copy(update={'timeout_seconds': min(600, remaining, request.timeout_seconds or 600)}) if remaining is not None else request
        try:
            result = client.complete(bounded)
        except ModelClientError as error:
            self.usage_complete = False
            self.stopping_reason = error.code
            raise
        self.prompt_tokens += result.prompt_tokens or 0
        self.completion_tokens += result.completion_tokens or 0
        self.usage_complete &= result.prompt_tokens is not None and result.completion_tokens is not None
        self.check_time()  # Discard late replies; never commit them after expiration.
        return result

    def client(self, client, check_prompt):
        from types import SimpleNamespace
        return SimpleNamespace(complete=lambda request: self.complete(client, request, check_prompt))

    def tool(self):
        self.check_time()
        if self.discovery_calls >= self.MAX_DISCOVERY:
            self.reject('discovery_call_limit')
        self.tool_calls += 1
        self.discovery_calls += 1

    def fixture_batch(self):
        self.check_time()
        if self.fixture_batches >= 1:self.reject('fixture_batch_limit')
        self.fixture_batches += 1
        self.tool_calls += 1

    def receipt(self):
        return {
            'model_calls': self.model_calls, 'model_call_limit': self.MAX_CALLS,
            'tool_calls': self.tool_calls, 'tool_call_limit': self.MAX_DISCOVERY + (1 if self.fixture_batches else 0),
            'fixture_batches':self.fixture_batches,'fixture_batch_limit':1,
            'prompt_bytes_total': self.prompt_bytes,
            'prompt_tokens': self.prompt_tokens if self.usage_complete else None,
            'completion_tokens': self.completion_tokens if self.usage_complete else None,
            'token_usage_complete': self.usage_complete,
            'elapsed_seconds': round(monotonic() - self.started, 3),
            'deadline_seconds': self.deadline_seconds, 'stopping_reason': self.stopping_reason,
            'scope': 'conversation_planner_and_requested_recipe_or_critic_work',
        }
