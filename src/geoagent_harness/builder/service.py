"""Runtime wiring for proposal-only Builder generation."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.agent_manifest import (
    load_agent_manifest,
)
from geoagent_harness.builder.agent import (
    BuilderModelClientProtocol,
    generate_builder_proposal,
)
from geoagent_harness.builder.schemas import (
    BuilderGenerationResult,
    BuilderRequest,
)
from geoagent_harness.model import (
    SharedModelClient,
    load_model_settings,
)


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
