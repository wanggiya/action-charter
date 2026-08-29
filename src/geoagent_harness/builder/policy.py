"""Deterministic policy checks for Builder proposals."""

from geoagent_harness.builder.schemas import (
    BuilderProposal,
    BuilderRequest,
)


def validate_builder_proposal(
    request: BuilderRequest,
    proposal: BuilderProposal,
) -> BuilderProposal:
    """Require the proposal to match the exact request."""

    if proposal.task_id != request.task_id:
        raise ValueError(
            "builder proposal task ID does not match request"
        )

    requested = {
        artifact.path: artifact.kind
        for artifact in request.artifacts
    }
    proposed = {
        artifact.path: artifact.kind
        for artifact in proposal.files
    }

    if proposed != requested:
        raise ValueError(
            "builder proposal files do not exactly match request"
        )

    return proposal
