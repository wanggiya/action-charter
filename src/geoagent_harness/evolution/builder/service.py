"""Runtime wiring for proposal-only Builder generation."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.agents.runtime.manifest import load_agent_manifest
from geoagent_harness.evolution.builder.agent import BuilderModelClientProtocol, generate_builder_proposal
from geoagent_harness.evolution.builder.schemas import BuilderGenerationResult, BuilderRequest
from geoagent_harness.platform.model_gateway import SharedModelClient
from geoagent_harness.platform.model_gateway import load_model_settings


def propose_builder_candidate(
    *,
    request: BuilderRequest,
    agents_root: Path = Path("agents"),
    model_client: BuilderModelClientProtocol | None = None,
) -> BuilderGenerationResult:
    """Generate without writing or executing candidate files."""

    manifest = load_agent_manifest(
        "builder",
        agents_root,
    )

    active_client = model_client

    if active_client is None:
        active_client = SharedModelClient(
            load_model_settings()
        )

    return generate_builder_proposal(
        request=request,
        manifest=manifest,
        model_client=active_client,
    )
