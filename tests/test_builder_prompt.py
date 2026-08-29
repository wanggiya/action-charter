import json
from pathlib import Path

from geoagent_harness.agent_manifest import (
    load_agent_manifest,
)
from geoagent_harness.builder import (
    BuilderArtifactKind,
    BuilderArtifactRequest,
    BuilderRequest,
    build_builder_request,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def builder_request(
    summary: str = "Propose one adapter.",
) -> BuilderRequest:
    return BuilderRequest(
        task_id="builder-prompt-test",
        summary=summary,
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
        context_references=[
            "context/SKILLS_INDEX.yaml",
        ],
    )


def test_builder_prompt_is_json_mode_and_bounded() -> None:
    manifest = load_agent_manifest(
        "builder",
        PROJECT_ROOT / "agents",
    )

    request = build_builder_request(
        builder_request(),
        manifest,
    )

    assert request.temperature == 0.0
    assert request.json_mode is True
    assert len(request.messages) == 2

    system = json.loads(request.messages[0].content)
    user = json.loads(request.messages[1].content)

    assert system["agent_id"] == "builder"
    assert "required_json_schema" in system
    assert user["builder_request"]["task_id"] == (
        "builder-prompt-test"
    )
    assert user["task"].startswith(
        "Propose the requested"
    )


def test_builder_prompt_redacts_secrets() -> None:
    manifest = load_agent_manifest(
        "builder",
        PROJECT_ROOT / "agents",
    )

    request = build_builder_request(
        builder_request(
            "Create adapter with password=private-value"
        ),
        manifest,
    )

    serialized = "\n".join(
        message.content
        for message in request.messages
    )

    assert "private-value" not in serialized
    assert "[REDACTED]" in serialized
