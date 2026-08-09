"""Non-executing structured Planner Agent."""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import ValidationError

from geoagent_harness.agent_manifest import AgentManifest
from geoagent_harness.context_pack.schemas import TaskContextPack
from geoagent_harness.model.schemas import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.planner.policy import (
    PlannerPolicyError,
    validate_plan_policy,
)
from geoagent_harness.planner.prompt import (
    build_planner_request,
)
from geoagent_harness.planner.schemas import (
    PlannerResult,
    WorkflowPlan,
)


class ModelClientProtocol(Protocol):
    """Narrow model capability available to the planner."""

    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        ...


class PlannerAgentError(RuntimeError):
    """Raised when the planner cannot produce an approved plan."""


def _validate_planner_manifest(
    manifest: AgentManifest,
) -> None:
    permissions = manifest.permissions

    if manifest.id != "planner":
        raise PlannerAgentError(
            "Planner Agent requires the planner manifest"
        )

    if permissions.tools:
        raise PlannerAgentError(
            "Planner Agent cannot have executable tools"
        )

    if permissions.arbitrary_shell:
        raise PlannerAgentError(
            "Planner Agent cannot have arbitrary shell access"
        )

    if permissions.unrestricted_sql:
        raise PlannerAgentError(
            "Planner Agent cannot have unrestricted SQL access"
        )

    if permissions.filesystem_write:
        raise PlannerAgentError(
            "Planner Agent cannot have filesystem write access"
        )

    if permissions.database_write:
        raise PlannerAgentError(
            "Planner Agent cannot have database write access"
        )


def run_planner_agent(
    *,
    context_pack: TaskContextPack,
    manifest: AgentManifest,
    model_client: ModelClientProtocol,
) -> PlannerResult:
    """Generate and validate one non-executed workflow plan."""

    _validate_planner_manifest(manifest)

    request = build_planner_request(
        context_pack,
        manifest,
    )

    model_result = model_client.complete(request)

    try:
        payload = json.loads(model_result.content)
    except json.JSONDecodeError as exc:
        raise PlannerAgentError(
            "Planner model returned invalid JSON"
        ) from exc

    try:
        plan = WorkflowPlan.model_validate(payload)
    except ValidationError as exc:
        raise PlannerAgentError(
            "Planner model returned an invalid plan schema"
        ) from exc

    available_skills = {
        skill.id
        for skill in context_pack.available_skills
    }

    try:
        validate_plan_policy(
            plan,
            available_skills=available_skills,
        )
    except PlannerPolicyError as exc:
        raise PlannerAgentError(
            f"Planner plan failed deterministic policy: {exc}"
        ) from exc

    return PlannerResult(
        model=model_result.model,
        original_request=(
            context_pack.original_request
        ),
        context_references=[
            reference.path
            for reference in context_pack.context_references
        ],
        plan=plan,
        warnings=context_pack.warnings,
    )