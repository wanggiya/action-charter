"""Tests for the structured read-only Critic Agent."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.agent_manifest import (
    AgentManifest,
    AgentPermissions,
    load_agent_manifest,
)
from geoagent_harness.critic.agent import (
    CriticAgentError,
    run_critic_agent,
)
from geoagent_harness.critic.schemas import (
    ApprovalEvidence,
    CriticEvidencePack,
    EvidenceReference,
    ValidationEvidence,
)
from geoagent_harness.model.schemas import (
    ModelRequest,
    ModelResult,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeModelClient:
    """Return fixed output without contacting Ollama."""

    def __init__(self, content: str) -> None:
        self.content = content
        self.request: ModelRequest | None = None

    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        self.request = request

        return ModelResult(
            model="qwen-test",
            content=self.content,
            finish_reason="stop",
        )


def make_evidence(
    *,
    status: str = "validated_success",
) -> CriticEvidencePack:
    return CriticEvidencePack(
        task_id="critic-agent-test",
        original_request=(
            "Load and validate the approved sample."
        ),
        deterministic_status=status,
        trace_final_status=(
            "validated_success"
            if status == "validated_success"
            else (
                "validation_failed"
                if status in {
                    "validation_failed",
                    "incomplete_evidence",
                }
                else "execution_failed"
            )
        ),
        validation_passed=(
            True
            if status == "validated_success"
            else False
        ),
        selected_skills=[
            "inspect_vector",
            "load_vector_to_postgis",
            "validate_postgis_layer",
            "generate_report",
        ],
        validation=ValidationEvidence(
            passed=(
                status == "validated_success"
            ),
            table_exists=True,
            geometry_column_exists=True,
            row_count=2,
            srid=4326,
            geometry_type="POINT",
            invalid_geometry_count=0,
            null_geometry_count=0,
            extent={
                "min_x": -77.1,
                "min_y": 38.8,
                "max_x": -77.0,
                "max_y": 38.9,
            },
            failed_checks=[],
        ),
        approval=ApprovalEvidence(
            approval_id="approval-test",
            plan_sha256="a" * 64,
            approved_step_ids=[
                "step_2",
                "step_4",
            ],
            complete=True,
        ),
        artifacts=[
            "reports/critic-agent-test.md",
            "traces/critic-agent-test.json",
        ],
        warnings=[],
        human_corrections=[],
        evidence_gaps=(
            ["report evidence is incomplete"]
            if status == "incomplete_evidence"
            else []
        ),
        timestamps={
            "started_at": "2026-08-09T20:00:00Z",
            "finished_at": "2026-08-09T20:01:00Z",
        },
        versions={
            "python": "3.12.3",
        },
        report_excerpt="# GeoAgent Task Report",
        evidence_references=[
            EvidenceReference(
                path="traces/critic-agent-test.json",
                sha256="b" * 64,
            ),
            EvidenceReference(
                path="reports/critic-agent-test.md",
                sha256="c" * 64,
            ),
        ],
    )


def model_payload(
    *,
    status: str = "validated_success",
) -> str:
    if status == "validated_success":
        conclusion = "supported"
        success_claimed = True
    elif status == "incomplete_evidence":
        conclusion = "incomplete"
        success_claimed = False
    else:
        conclusion = "not_supported"
        success_claimed = False

    return json.dumps(
        {
            "schema_version": "1.0",
            "deterministic_status": status,
            "conclusion": conclusion,
            "success_claimed": success_claimed,
            "summary": (
                "The conclusion is supported by the "
                "deterministic evidence."
            ),
            "validation_basis": [
                "Deterministic validation status was checked."
            ],
            "additional_risks": [],
            "recommendations": [
                "Retain the trace and report."
            ],
            "edits_performed": False,
            "database_actions_performed": False,
        }
    )


@pytest.fixture
def critic_manifest() -> AgentManifest:
    return load_agent_manifest(
        "critic",
        PROJECT_ROOT / "agents",
    )


def test_accepts_valid_critic_assessment(
    critic_manifest: AgentManifest,
) -> None:
    client = FakeModelClient(model_payload())

    result = run_critic_agent(
        evidence=make_evidence(),
        manifest=critic_manifest,
        model_client=client,
    )

    assert result.agent_id == "critic"
    assert result.model == "qwen-test"
    assert (
        result.deterministic_status
        == "validated_success"
    )
    assert result.assessment.conclusion == "supported"
    assert result.assessment.success_claimed is True

    assert client.request is not None
    assert client.request.json_mode is True
    assert client.request.temperature == 0.0


@pytest.mark.parametrize(
    "status",
    [
        "validation_failed",
        "execution_failed",
        "incomplete_evidence",
    ],
)
def test_accepts_matching_non_success_assessment(
    critic_manifest: AgentManifest,
    status: str,
) -> None:
    result = run_critic_agent(
        evidence=make_evidence(status=status),
        manifest=critic_manifest,
        model_client=FakeModelClient(
            model_payload(status=status)
        ),
    )

    assert result.assessment.success_claimed is False


def test_rejects_invalid_json(
    critic_manifest: AgentManifest,
) -> None:
    with pytest.raises(
        CriticAgentError,
        match="invalid JSON",
    ):
        run_critic_agent(
            evidence=make_evidence(),
            manifest=critic_manifest,
            model_client=FakeModelClient(
                "The workflow looks correct."
            ),
        )


def test_rejects_markdown_json_fence(
    critic_manifest: AgentManifest,
) -> None:
    fenced = f"```json\n{model_payload()}\n```"

    with pytest.raises(
        CriticAgentError,
        match="invalid JSON",
    ):
        run_critic_agent(
            evidence=make_evidence(),
            manifest=critic_manifest,
            model_client=FakeModelClient(fenced),
        )


def test_rejects_changed_deterministic_status(
    critic_manifest: AgentManifest,
) -> None:
    with pytest.raises(
        CriticAgentError,
        match="changed the deterministic status",
    ):
        run_critic_agent(
            evidence=make_evidence(
                status="validation_failed"
            ),
            manifest=critic_manifest,
            model_client=FakeModelClient(
                model_payload(
                    status="validated_success"
                )
            ),
        )


def test_rejects_false_success_claim(
    critic_manifest: AgentManifest,
) -> None:
    payload = json.loads(model_payload())
    payload["success_claimed"] = False

    with pytest.raises(
        CriticAgentError,
        match="success claim contradicts",
    ):
        run_critic_agent(
            evidence=make_evidence(),
            manifest=critic_manifest,
            model_client=FakeModelClient(
                json.dumps(payload)
            ),
        )


def test_rejects_contradictory_conclusion(
    critic_manifest: AgentManifest,
) -> None:
    payload = json.loads(model_payload())
    payload["conclusion"] = "not_supported"

    with pytest.raises(
        CriticAgentError,
        match="conclusion contradicts",
    ):
        run_critic_agent(
            evidence=make_evidence(),
            manifest=critic_manifest,
            model_client=FakeModelClient(
                json.dumps(payload)
            ),
        )


def test_redacts_secret_from_model_output(
    critic_manifest: AgentManifest,
) -> None:
    payload = json.loads(model_payload())
    payload["summary"] = (
        "POSTGRES_PASSWORD=do-not-expose"
    )

    result = run_critic_agent(
        evidence=make_evidence(),
        manifest=critic_manifest,
        model_client=FakeModelClient(
            json.dumps(payload)
        ),
    )

    assert "do-not-expose" not in (
        result.assessment.summary
    )
    assert "[REDACTED]" in (
        result.assessment.summary
    )


def test_rejects_tool_enabled_manifest() -> None:
    manifest = AgentManifest(
        id="critic",
        model_ref="shared_ollama_runtime",
        purpose="Unsafe critic.",
        permissions=AgentPermissions(
            tools=["health_check"],
        ),
        instructions=["Review evidence."],
    )

    with pytest.raises(
        CriticAgentError,
        match="cannot have executable tools",
    ):
        run_critic_agent(
            evidence=make_evidence(),
            manifest=manifest,
            model_client=FakeModelClient(
                model_payload()
            ),
        )


@pytest.mark.parametrize(
    ("permission", "message"),
    [
        ("arbitrary_shell", "arbitrary shell"),
        ("unrestricted_sql", "unrestricted SQL"),
        ("filesystem_write", "filesystem write"),
        ("database_write", "database write"),
    ],
)
def test_rejects_unsafe_manifest_permissions(
    permission: str,
    message: str,
) -> None:
    values = {
        "arbitrary_shell": False,
        "unrestricted_sql": False,
        "filesystem_write": False,
        "database_write": False,
    }
    values[permission] = True

    manifest = AgentManifest(
        id="critic",
        model_ref="shared_ollama_runtime",
        purpose="Unsafe critic.",
        permissions=AgentPermissions(**values),
        instructions=["Review evidence."],
    )

    with pytest.raises(
        CriticAgentError,
        match=message,
    ):
        run_critic_agent(
            evidence=make_evidence(),
            manifest=manifest,
            model_client=FakeModelClient(
                model_payload()
            ),
        )