"""Non-executing structured Planner Agent."""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import ValidationError

from geoagent_harness.agent_manifest import AgentManifest
from geoagent_harness.context_pack.schemas import TaskContextPack
from geoagent_harness.model.schemas import (
    ModelRequest,
    ChatMessage,
    ModelResult,
)
from geoagent_harness.planner.policy import (
    PlannerPolicyError,
    validate_plan_policy,
    normalize_plan_input_filenames,
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
    """Raised when the planner cannot produce a validated non-executing proposal."""

    def __init__(self, message: str, *, findings: list[str] | None = None,
                 correction_attempted: bool = False):
        super().__init__(message)
        self.findings = (findings or [])[:6]
        self.correction_attempted = correction_attempted


def _schema_findings(error: ValidationError) -> list[str]:
    """Describe trusted field locations/types, never model values or context."""
    safe_fields = {'schema_version', 'status', 'summary', 'steps', 'assumptions',
                   'risks', 'execution_performed', 'validation_performed',
                   'step_id', 'skill', 'purpose', 'arguments', 'requires_approval',
                   'expected_artifacts', 'validation_required', 'agent_id', 'plan',
                   'depends_on', 'skill_id', 'tool', 'name', 'id'}
    descriptions = {'missing': 'required field is missing', 'extra_forbidden': 'unexpected field is not allowed',
                    'list_type': 'must be a list', 'dict_type': 'must be an object',
                    'string_type': 'must be a string', 'bool_type': 'must be a boolean',
                    'literal_error': 'must match the declared schema value',
                    'too_short': 'contains too few items or characters',
                    'too_long': 'contains too many items or characters',
                    'string_pattern_mismatch': 'must match the required naming pattern',
                    'value_error': 'does not satisfy the declared field rules'}
    findings = []
    for item in error.errors(include_input=False, include_context=False, include_url=False)[:6]:
        path = '.'.join(str(part) if isinstance(part, int) or part in safe_fields else '[unexpected field]'
                        for part in item['loc']) or 'plan'
        findings.append(path + ': ' + descriptions.get(item['type'], 'does not match the required schema type'))
    return findings



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

    available_skills = {skill.id for skill in context_pack.available_skills}
    correction_used = False
    correction_kind = ""
    first_policy_error = None
    for attempt in range(2):
        model_result = model_client.complete(request)
        problem = None
        try:
            payload = json.loads(model_result.content)
        except json.JSONDecodeError:
            problem = PlannerAgentError("Planner model returned invalid JSON",
                findings=["response: must be exactly one complete JSON object without Markdown"],
                correction_attempted=bool(attempt))
            kind = "JSON"
        else:
            try:
                plan = WorkflowPlan.model_validate(payload)
            except ValidationError as error:
                problem = PlannerAgentError("Planner model returned an invalid plan schema",
                    findings=_schema_findings(error), correction_attempted=bool(attempt))
                kind = "schema"
            else:
                try:
                    normalize_plan_input_filenames(plan)
                    validate_plan_policy(plan, available_skills=available_skills)
                except PlannerPolicyError as error:
                    from geoagent_harness.context_pack.redaction import redact_text
                    finding = redact_text(str(error))[:1000]
                    if first_policy_error is None:
                        first_policy_error = finding
                    problem = PlannerAgentError(
                        "Planner plan failed deterministic policy after one correction attempt: " + first_policy_error,
                        findings=[finding], correction_attempted=bool(attempt))
                    kind = "policy"
        if problem is None:
            break
        if attempt:
            raise problem
        correction_used = True
        correction_kind = kind
        request = request.model_copy(update={"messages": [*request.messages,
            ChatMessage(role="user", content=json.dumps({
                "task": "Correct the proposal once. Return a complete fresh JSON WorkflowPlan for the original request only.",
                "failure_kind": kind,
                "deterministic_finding": '; '.join(problem.findings),
                "allowed_skill_ids": sorted(available_skills),
                "instruction": "Match required_json_schema. Return the plan itself, not an agent envelope. Use step_1, step_2 in order; expected_artifacts, assumptions and risks must be lists of strings. Keep execution_performed=false and validation_performed=false. Do not add unrelated steps or broaden the reviewed scope. Writes require approval and validation. Nothing may execute.",
            }))]})

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
        warnings=[*context_pack.warnings, *([f"Planner proposal required one {correction_kind} correction; the fresh plan passed schema and deterministic policy validation."] if correction_used else [])],
    )