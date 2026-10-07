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
from geoagent_harness.planner.policy import REQUIRED_SKILL_ARGUMENTS


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
            "Return exactly one JSON object: the WorkflowPlan itself, not a PlannerResult or agent envelope. Do not include agent_id, model or plan envelope fields. Omit depends_on for the usual sequential workflow; explicit dependencies must be valid step IDs in an acyclic graph.",
            "expected_artifacts, assumptions and risks are arrays of strings, not text strings or nested objects. status is planned and schema_version is 1.0.",
            "Do not use Markdown or JSON code fences.",
            "Use only available_skills.",
            "For read-only inspect_vector and inspect_raster metadata steps, use requires_approval=false and validation_required=false unless the user explicitly requests an additional approval gate. Planning-only does not itself require approval. Never infer approval from reviewed text.",
            "Do not invent tools, commands, SQL, or capabilities.",
            "Do not execute or claim to have executed anything.",
            "execution_performed must be false.",
            "validation_performed must be false.",
            (
                "Every write step must set "
                "requires_approval to true."
            ),
            (
                "Every step must include all required arguments "
                "listed in required_skill_arguments."
            ),
            (
                "The Planner Agent itself has no dataset mount, "
                "database connection, credentials, MCP tools, or "
                "write access. Describe these only as future "
                "Executor requirements."
            ),
            "Step IDs must be step_1, step_2, and so on.",
        ],
        "required_json_schema": (
            WorkflowPlan.model_json_schema()
        ),
        "required_skill_arguments": {
            skill: sorted(REQUIRED_SKILL_ARGUMENTS.get(skill, set()))
            for skill in available_skills
        },
    }
    schema = system_payload["required_json_schema"]
    schema["$defs"]["PlanStep"]["properties"]["skill"]["enum"] = available_skills
    system_payload["mandatory_rules"].append(
        "The available skill list is an allowlist, not a workflow template. Include only steps needed for the original request. Never add an unrelated load, validation or report step."
    )
    selected = set(available_skills)
    if "load_vector_to_postgis" in selected:
        system_payload["mandatory_rules"].extend([
            "A load_vector_to_postgis step must follow inspect_vector and be followed by validate_postgis_layer. If the required dependency skills are unavailable, do not invent them.",
        ])
    if "validate_postgis_layer" in selected:
        system_payload["mandatory_rules"].append("validate_postgis_layer must set validation_required to true.")
    if "generate_report" in selected:
        system_payload["mandatory_rules"].append("generate_report must follow validate_postgis_layer and require approval.")
    system_payload["selected_skill_requirements"] = [
        {"skill": skill.id, "requires_approval": skill.approval_required,
         "validation_required": skill.validation_required}
        for skill in context_pack.available_skills
    ]

    # A concrete example only for the exact reviewed single-input inspection.
    # The reviewed input is data, not authority; handoff rechecks it independently.
    try:
        bounded_source = json.loads(context_pack.original_request)
    except (ValueError, TypeError):
        bounded_source = None
    if (len(available_skills) == 1 and available_skills[0] in {'inspect_vector', 'inspect_raster'}
            and isinstance(bounded_source, dict)
            and isinstance(bounded_source.get('intent_review_filename'), str)
            and isinstance(bounded_source.get('exact_arguments'), dict)
            and set(bounded_source['exact_arguments']) == {'path'}
            and isinstance(bounded_source['exact_arguments']['path'], str)):
        system_payload['response_shape_example'] = {
            'schema_version': '1.0', 'status': 'planned', 'summary': 'Inspect the reviewed input metadata.',
            'steps': [{'step_id': 'step_1', 'skill': available_skills[0],
                       'purpose': 'Read metadata for the exact reviewed input.',
                       'arguments': bounded_source['exact_arguments'],
                       'requires_approval': False, 'expected_artifacts': ['inspection metadata'],
                       'validation_required': False}],
            'assumptions': [], 'risks': [], 'execution_performed': False, 'validation_performed': False,
        }

    user_payload = {
        "task": "Create a plan. Do not execute it.",
        "original_request": context_pack.original_request,
        "datasets": [
            dataset.model_dump(mode="json")
            for dataset in context_pack.datasets
        ],
        "selected_skills": [
            skill.model_dump(mode="json")
            for skill in context_pack.available_skills
        ],
        "warnings": context_pack.warnings,
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
