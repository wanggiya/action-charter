import pytest
from pydantic import ValidationError

from geoagent_harness.builder import (
    BuilderArtifactKind,
    BuilderArtifactRequest,
    BuilderFileProposal,
    BuilderProposal,
    BuilderRequest,
    validate_builder_proposal,
)


def valid_request() -> BuilderRequest:
    return BuilderRequest(
        task_id="builder-test-1",
        summary="Propose one trusted adapter candidate.",
        artifacts=[
            BuilderArtifactRequest(
                kind=BuilderArtifactKind.ADAPTER,
                path=(
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                purpose="Implement the bounded adapter.",
            )
        ],
        context_references=[
            "context/SKILLS_INDEX.yaml",
        ],
    )


def valid_proposal() -> BuilderProposal:
    return BuilderProposal(
        task_id="builder-test-1",
        summary="Proposed one untrusted adapter.",
        files=[
            BuilderFileProposal(
                kind=BuilderArtifactKind.ADAPTER,
                path=(
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                content=(
                    '"""Untrusted adapter candidate."""\n'
                ),
            )
        ],
        test_intentions=[
            "Run static contract tests.",
        ],
    )


def test_valid_builder_proposal_matches_request() -> None:
    proposal = validate_builder_proposal(
        valid_request(),
        valid_proposal(),
    )

    assert proposal.agent_id == "builder"
    assert proposal.filesystem_modified is False
    assert proposal.tests_performed is False
    assert proposal.implementation_trusted is False
    assert proposal.promotion_performed is False
    assert proposal.execution_performed is False


@pytest.mark.parametrize(
    "path",
    [
        "/tmp/adapter.py",
        "../adapter.py",
        "tests/../adapter.py",
        ".hidden/adapter.py",
        "tests\\test_adapter.py",
    ],
)
def test_unsafe_candidate_paths_are_rejected(
    path: str,
) -> None:
    with pytest.raises(ValidationError):
        BuilderArtifactRequest(
            kind=BuilderArtifactKind.TEST,
            path=path,
            purpose="Unsafe test path.",
        )


def test_wrong_path_for_artifact_kind_is_rejected() -> None:
    with pytest.raises(
        ValidationError,
        match="outside the allowed prefix",
    ):
        BuilderArtifactRequest(
            kind=BuilderArtifactKind.ADAPTER,
            path="tests/test_adapter.py",
            purpose="Wrong artifact location.",
        )


def test_duplicate_requested_paths_are_rejected() -> None:
    artifact = BuilderArtifactRequest(
        kind=BuilderArtifactKind.TEST,
        path="tests/test_example.py",
        purpose="Test the candidate.",
    )

    with pytest.raises(
        ValidationError,
        match="must be unique",
    ):
        BuilderRequest(
            task_id="duplicate-test",
            summary="Duplicate paths.",
            artifacts=[artifact, artifact],
        )


def test_builder_cannot_claim_test_execution() -> None:
    payload = valid_proposal().model_dump()
    payload["tests_performed"] = True

    with pytest.raises(ValidationError):
        BuilderProposal.model_validate(payload)


def test_builder_cannot_claim_trusted_status() -> None:
    payload = valid_proposal().model_dump()
    payload["implementation_trusted"] = True

    with pytest.raises(ValidationError):
        BuilderProposal.model_validate(payload)


def test_builder_cannot_claim_promotion() -> None:
    payload = valid_proposal().model_dump()
    payload["promotion_performed"] = True

    with pytest.raises(ValidationError):
        BuilderProposal.model_validate(payload)


def test_builder_cannot_add_permission_fields() -> None:
    payload = valid_proposal().model_dump()
    payload["permissions"] = {
        "filesystem_write": True,
    }

    with pytest.raises(ValidationError):
        BuilderProposal.model_validate(payload)


def test_proposal_must_match_exact_requested_files() -> None:
    proposal = valid_proposal().model_copy(
        update={"task_id": "different-task"}
    )

    with pytest.raises(
        ValueError,
        match="task ID does not match",
    ):
        validate_builder_proposal(
            valid_request(),
            proposal,
        )


def test_candidate_file_byte_limit_is_enforced() -> None:
    with pytest.raises(
        ValidationError,
        match="byte limit",
    ):
        BuilderFileProposal(
            kind=BuilderArtifactKind.ADAPTER,
            path=(
                "src/geoagent_harness/"
                "skill_adapters/oversized.py"
            ),
            content="界" * 20_000,
        )
