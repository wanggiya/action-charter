"""Construct the bounded Planner Agent prompt."""

from __future__ import annotations

import json

from geoagent_harness.agent_manifest import AgentManifest
from geoagent_harness.context_pack.schemas import TaskContextPack
from geoagent_harness.model.schemas import (
    ChatMessage,
    ModelRequest,
)
from geoagent_harness.planner.schemas import WorkflowPlan


def build_planner_request(
    context_pack: TaskContextPack,
    manifest: AgentManifest,
) -> ModelRequest:
    """Build a JSON-only planning request."""

    available_skills = [
        skill.id
        for skill in context_pack.available_skills
    ]

    system_payload = {
        "agent_id": manifest.id,
        "purpose": manifest.purpose,
        "instructions": manifest.instructions,
        "available_skills": available_skills,
        "mandatory_rules": [
            "Return exactly one JSON object.",
            "Do not use Markdown or JSON code fences.",
            "Use only available_skills.",
            "Do not invent tools, commands, SQL, or capabilities.",
            "Do not execute or claim to have executed anything.",
            "execution_performed must be false.",
            "validation_performed must be false.",
            "A load_vector_to_postgis step must follow inspect_vector.",
            (
                "A load_vector_to_postgis step must be followed "
                "by validate_postgis_layer."
            ),
            (
                "A generate_report step must follow "
                "validate_postgis_layer."
            ),
            (
                "Every write step must set "
                "requires_approval to true."
            ),
            (
                "validate_postgis_layer must set "
                "validation_required to true."
            ),
            "Step IDs must be step_1, step_2, and so on.",
        ],
        "required_json_schema": (
            WorkflowPlan.model_json_schema()
        ),
    }

    user_payload = {
        "task": "Create a plan. Do not execute it.",
        "context_pack": context_pack.as_prompt_payload(),
    }

    return ModelRequest(
        messages=[
            ChatMessage(
                role="system",
                content=json.dumps(
                    system_payload,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            ),
            ChatMessage(
                role="user",
                content=json.dumps(
                    user_payload,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            ),
        ],
        temperature=0.0,
        json_mode=True,
    )