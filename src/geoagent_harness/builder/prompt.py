"""Construct the bounded Builder Agent prompt."""

from __future__ import annotations

import json

from geoagent_harness.agent_manifest import AgentManifest
from geoagent_harness.builder.schemas import (
    BuilderProposal,
    BuilderRequest,
)
from geoagent_harness.model import (
    ChatMessage,
    ModelRequest,
)
from geoagent_harness.redaction import redact_value


def build_builder_request(
    request: BuilderRequest,
    manifest: AgentManifest,
) -> ModelRequest:
    """Build one deterministic, JSON-only Builder request."""

    system_payload = {
        "agent_id": manifest.id,
        "purpose": manifest.purpose,
        "instructions": manifest.instructions,
        "mandatory_rules": [
            "Return exactly one JSON object.",
            "Do not return Markdown or JSON fences.",
            "Return only the required proposal schema.",
            (
                "Propose exactly the artifact paths and kinds "
                "listed in the request."
            ),
            "Do not invent additional files.",
            (
                "Do not request or claim tools, shell, SQL, "
                "credentials, permissions, or write access."
            ),
            "filesystem_modified must be false.",
            "tools_called must be false.",
            "tests_performed must be false.",
            "validation_performed must be false.",
            "approval_granted must be false.",
            "implementation_trusted must be false.",
            "promotion_performed must be false.",
            "execution_performed must be false.",
            (
                "Describe intended tests only in "
                "test_intentions."
            ),
            (
                "All generated content remains an untrusted "
                "in-memory proposal."
            ),
        ],
        "required_json_schema": (
            BuilderProposal.model_json_schema()
        ),
    }

    user_payload = {
        "task": (
            "Propose the requested candidate artifacts. "
            "Do not write, test, validate, trust, promote, "
            "or execute them."
        ),
        "builder_request": redact_value(
            request.model_dump(mode="json")
        ),
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
