"""High-level service for running the Critic Agent."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.agent_manifest import (
    load_agent_manifest,
)
from geoagent_harness.critic.agent import (
    ModelClientProtocol,
    run_critic_agent,
)
from geoagent_harness.critic.evidence import (
    build_critic_evidence,
)
from geoagent_harness.critic.schemas import (
    CriticResult,
)
from geoagent_harness.model import (
    SharedModelClient,
    load_model_settings,
)


def critique_task(
    *,
    trace_path: Path,
    report_path: Path,
    trace_root: Path,
    report_root: Path,
    agents_root: Path,
    model_client: ModelClientProtocol | None = None,
) -> CriticResult:
    """Build evidence and request one in-memory assessment."""

    evidence = build_critic_evidence(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=trace_root,
        report_root=report_root,
    )

    manifest = load_agent_manifest(
        "critic",
        agents_root,
    )

    client = model_client

    if client is None:
        client = SharedModelClient(
            load_model_settings()
        )

    return run_critic_agent(
        evidence=evidence,
        manifest=manifest,
        model_client=client,
    )