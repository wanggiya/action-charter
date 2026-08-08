"""High-level service for producing a validated plan."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.agent_manifest import (
    load_agent_manifest,
)
from geoagent_harness.context_pack import (
    build_context_pack,
)
from geoagent_harness.model import (
    SharedModelClient,
    load_model_settings,
)
from geoagent_harness.planner.agent import (
    ModelClientProtocol,
    run_planner_agent,
)
from geoagent_harness.planner.schemas import (
    PlannerResult,
)


def plan_task(
    *,
    original_request: str,
    project_root: Path,
    agents_root: Path,
    model_client: ModelClientProtocol | None = None,
) -> PlannerResult:
    """Build context, call the model, and validate its plan."""

    context_pack = build_context_pack(
        original_request,
        project_root,
    )

    manifest = load_agent_manifest(
        "planner",
        agents_root,
    )

    client = model_client

    if client is None:
        client = SharedModelClient(
            load_model_settings()
        )

    return run_planner_agent(
        context_pack=context_pack,
        manifest=manifest,
        model_client=client,
    )