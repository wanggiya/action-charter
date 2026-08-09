"""Schema-constrained, read-only Critic Agent."""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import ValidationError

from geoagent_harness.agent_manifest import AgentManifest
from geoagent_harness.critic.prompt import (
    build_critic_request,
)
from geoagent_harness.critic.schemas import (
    CriticAssessment,
    CriticEvidencePack,
    CriticResult,
)
from geoagent_harness.model.schemas import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.trace import redact_value


class ModelClientProtocol(Protocol):
    """Narrow model capability available to the Critic."""

    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        ...


class CriticAgentError(RuntimeError):
    """Raised when the Critic cannot return a safe assessment."""


def _validate_critic_manifest(
    manifest: AgentManifest,
) -> None:
    permissions = manifest.permissions

    if manifest.id != "critic":
        raise CriticAgentError(
            "Critic Agent requires the critic manifest"
        )

    if permissions.tools:
        raise CriticAgentError(
            "Critic Agent cannot have executable tools"
        )

    if permissions.arbitrary_shell:
        raise CriticAgentError(
            "Critic Agent cannot have arbitrary shell access"
        )

    if permissions.unrestricted_sql:
        raise CriticAgentError(
            "Critic Agent cannot have unrestricted SQL access"
        )

    if permissions.filesystem_write:
        raise CriticAgentError(
            "Critic Agent cannot have filesystem write access"
        )

    if permissions.database_write:
        raise CriticAgentError(
            "Critic Agent cannot have database write access"
        )


def _validate_assessment_policy(
    assessment: CriticAssessment,
    evidence: CriticEvidencePack,
) -> None:
    status = evidence.deterministic_status

    if assessment.deterministic_status != status:
        raise CriticAgentError(
            "Critic model changed the deterministic status"
        )

    expected = {
        "validated_success": ("supported", True),
        "validation_failed": ("not_supported", False),
        "execution_failed": ("not_supported", False),
        "incomplete_evidence": ("incomplete", False),
    }

    expected_conclusion, expected_success = expected[
        status
    ]

    if assessment.conclusion != expected_conclusion:
        raise CriticAgentError(
            "Critic conclusion contradicts deterministic evidence"
        )

    if assessment.success_claimed is not expected_success:
        raise CriticAgentError(
            "Critic success claim contradicts deterministic evidence"
        )


def run_critic_agent(
    *,
    evidence: CriticEvidencePack,
    manifest: AgentManifest,
    model_client: ModelClientProtocol,
) -> CriticResult:
    """Generate and validate one read-only critic assessment."""

    _validate_critic_manifest(manifest)

    request = build_critic_request(
        evidence,
        manifest,
    )
    model_result = model_client.complete(request)

    try:
        decoded = json.loads(model_result.content)
    except json.JSONDecodeError as exc:
        raise CriticAgentError(
            "Critic model returned invalid JSON"
        ) from exc

    if not isinstance(decoded, dict):
        raise CriticAgentError(
            "Critic model response must be a JSON object"
        )

    redacted = redact_value(decoded)

    try:
        assessment = CriticAssessment.model_validate(
            redacted
        )
    except ValidationError as exc:
        raise CriticAgentError(
            "Critic model returned an invalid assessment schema"
        ) from exc

    _validate_assessment_policy(
        assessment,
        evidence,
    )

    return CriticResult(
        model=model_result.model,
        task_id=evidence.task_id,
        deterministic_status=(
            evidence.deterministic_status
        ),
        evidence_references=(
            evidence.evidence_references
        ),
        evidence_gaps=list(
            evidence.evidence_gaps
        ),
        workflow_warnings=list(
            evidence.warnings
        ),
        human_corrections=list(
            evidence.human_corrections
        ),
        assessment=assessment,
    )