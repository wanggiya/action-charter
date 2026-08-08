import json
from pathlib import Path

from geoagent_harness.agent_manifest import (
    load_agent_manifest,
)
from geoagent_harness.context_pack import (
    build_context_pack,
)
from geoagent_harness.planner.prompt import (
    build_planner_request,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_prompt_is_json_mode_and_bounded() -> None:
    context = build_context_pack(
        "Inspect and validate sample_points.",
        PROJECT_ROOT,
    )
    manifest = load_agent_manifest(
        "planner",
        PROJECT_ROOT / "agents",
    )

    request = build_planner_request(
        context,
        manifest,
    )

    assert request.temperature == 0.0
    assert request.json_mode is True
    assert len(request.messages) == 2

    system = json.loads(request.messages[0].content)
    user = json.loads(request.messages[1].content)

    assert system["agent_id"] == "planner"
    assert "required_json_schema" in system
    assert user["task"] == (
        "Create a plan. Do not execute it."
    )


def test_prompt_contains_no_original_secret() -> None:
    context = build_context_pack(
        "Inspect data with password=private-value",
        PROJECT_ROOT,
    )
    manifest = load_agent_manifest(
        "planner",
        PROJECT_ROOT / "agents",
    )

    request = build_planner_request(
        context,
        manifest,
    )

    serialized = "\n".join(
        message.content
        for message in request.messages
    )

    assert "private-value" not in serialized
    assert "[REDACTED]" in serialized