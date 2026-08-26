"""Catalog-generated prompt for recipe proposals."""

from __future__ import annotations

import json

from geoagent_harness.model import (
    ChatMessage,
    ModelRequest,
)
from geoagent_harness.recipe_proposals.schemas import (
    get_recipe_parameter_model,
)
from geoagent_harness.recipe_proposals.templates import (
    list_recipe_templates,
)


def _template_contracts() -> str:
    """Render trusted templates deterministically."""

    contracts: list[dict[str, object]] = []

    for template in list_recipe_templates():
        parameter_model = (
            get_recipe_parameter_model(
                template.parameter_profile
            )
        )

        parameter_schema = (
            parameter_model.model_json_schema()
        )

        contracts.append(
            {
                "template_id": (
                    template.template_id
                ),
                "required_parameters": list(
                    template.required_parameters
                ),
                "parameters_schema": (
                    parameter_schema
                ),
            }
        )

    return json.dumps(
        contracts,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )


def _system_prompt() -> str:
    """Build the proposal-only system prompt."""

    contracts = _template_contracts()

    return f"""
You are the proposal-only component of a controlled
geospatial workflow system.

Return exactly one JSON object and no Markdown.

Select exactly one template_id from the trusted
template contracts below.

You must not invent any other template, skill, step,
tool, function, package, entrypoint, SQL statement,
shell command, approval, or execution result.

Trusted template contracts:

{contracts}

Required top-level JSON shape:

{{
  "schema_version": "1.0",
  "status": "proposed_not_compiled",
  "original_request": "string",
  "summary": "string",
  "recipe_id_hint": "safe-lowercase-id-or-null",
  "selection": {{
    "template_id": "one trusted template",
    "parameters": {{}}
  }},
  "assumptions": [],
  "missing_information": [],
  "warnings": [],
  "compilation_performed": false,
  "execution_requested": false,
  "approval_performed": false,
  "execution_performed": false
}}

Follow the selected parameters_schema exactly.
Do not add parameter fields that are not declared.

Use null for an optional parameter that the user did
not provide. Add a short question or description to
missing_information when required information is
missing.

Never claim that compilation, saving, approval, tool
use, database access, file writing, or execution
occurred.
""".strip()


def build_recipe_proposal_request(
    original_request: str,
) -> ModelRequest:
    """Build one deterministic proposal-only request."""

    cleaned = original_request.strip()

    if not cleaned:
        raise ValueError(
            "original request cannot be empty"
        )

    return ModelRequest(
        messages=[
            ChatMessage(
                role="system",
                content=_system_prompt(),
            ),
            ChatMessage(
                role="user",
                content=cleaned,
            ),
        ],
        temperature=0.0,
        json_mode=True,
    )