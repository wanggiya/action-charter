import json
from pathlib import Path

import pytest

from geoagent_harness.agent_manifest import (
    AgentManifest,
    AgentPermissions,
    load_agent_manifest,
)
from geoagent_harness.builder import (
    BuilderAgentError,
    BuilderArtifactKind,
    BuilderArtifactRequest,
    BuilderProposal,
    BuilderRequest,
    generate_builder_proposal,
)
from geoagent_harness.model import (
    ModelRequest,
    ModelResult,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeModelClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.request: ModelRequest | None = None

    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        self.request = request

        return ModelResult(
            model="qwen-builder-test",
            content=self.content,
            finish_reason="stop",
        )


def builder_request() -> BuilderRequest:
    return BuilderRequest(
        task_id="builder-agent-test",
        summary="Propose one adapter.",
        artifacts=[
            BuilderArtifactRequest(
                kind=BuilderArtifactKind.ADAPTER,
                path=(
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                purpose="Propose the adapter.",
            )
        ],
    )


def proposal_payload() -> dict[str, object]:
    return BuilderProposal(
        task_id="builder-agent-test",
        summary="Proposed one untrusted adapter.",
        files=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "content": (
                    '"""Untrusted adapter candidate."""\n'
                ),
            }
        ],
        test_intentions=[
            "Run isolated static tests later.",
        ],
    ).model_dump(mode="json")


def builder_manifest() -> AgentManifest:
    return load_agent_manifest(
        "builder",
        PROJECT_ROOT / "agents",
    )


def test_builder_accepts_valid_proposal() -> None:
    client = FakeModelClient(
        json.dumps(proposal_payload())
    )

    result = generate_builder_proposal(
        request=builder_request(),
        manifest=builder_manifest(),
        model_client=client,
    )

    assert result.agent_id == "builder"
    assert result.model == "qwen-builder-test"
    assert result.proposal.task_id == "builder-agent-test"
    assert result.filesystem_modified is False
    assert result.implementation_trusted is False
    assert result.execution_performed is False
    assert client.request is not None
    assert client.request.json_mode is True


@pytest.mark.parametrize(
    "content",
    [
        "not JSON",
        "```json\n{}\n```",
        "[]",
    ],
)
def test_builder_rejects_non_object_output(
    content: str,
) -> None:
    with pytest.raises(BuilderAgentError):
        generate_builder_proposal(
            request=builder_request(),
            manifest=builder_manifest(),
            model_client=FakeModelClient(content),
        )


def test_builder_rejects_authority_claim() -> None:
    payload = proposal_payload()
    payload["execution_performed"] = True

    with pytest.raises(
        BuilderAgentError,
        match="invalid proposal schema",
    ):
        generate_builder_proposal(
            request=builder_request(),
            manifest=builder_manifest(),
            model_client=FakeModelClient(
                json.dumps(payload)
            ),
        )


def test_builder_rejects_unrequested_file() -> None:
    payload = proposal_payload()
    files = payload["files"]
    assert isinstance(files, list)
    files[0]["path"] = (
        "src/geoagent_harness/"
        "skill_adapters/different.py"
    )

    with pytest.raises(
        BuilderAgentError,
        match="deterministic policy",
    ):
        generate_builder_proposal(
            request=builder_request(),
            manifest=builder_manifest(),
            model_client=FakeModelClient(
                json.dumps(payload)
            ),
        )


def test_builder_requires_builder_manifest() -> None:
    manifest = AgentManifest(
        id="planner",
        model_ref="shared_ollama_runtime",
        purpose="Wrong logical role.",
        permissions=AgentPermissions(),
        instructions=["Plan only."],
    )

    with pytest.raises(
        BuilderAgentError,
        match="requires the builder manifest",
    ):
        generate_builder_proposal(
            request=builder_request(),
            manifest=manifest,
            model_client=FakeModelClient(
                json.dumps(proposal_payload())
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
def test_builder_rejects_unsafe_permissions(
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
        id="builder",
        model_ref="shared_ollama_runtime",
        purpose="Unsafe Builder.",
        permissions=AgentPermissions(**values),
        instructions=["Propose only."],
    )

    with pytest.raises(
        BuilderAgentError,
        match=message,
    ):
        generate_builder_proposal(
            request=builder_request(),
            manifest=manifest,
            model_client=FakeModelClient(
                json.dumps(proposal_payload())
            ),
        )
