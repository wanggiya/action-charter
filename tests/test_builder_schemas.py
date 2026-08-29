import pytest
from pydantic import ValidationError

from geoagent_harness.builder import (
    BuilderArtifactKind,
    BuilderArtifactRequest,
    BuilderFileProposal,
    BuilderProposal,
    BuilderRequest,
    validate_builder_proposal,
    BuilderCandidateTestRecord,
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

def test_builder_candidate_test_record_is_consistent(
) -> None:
    digest = "a" * 64

    record = BuilderCandidateTestRecord(
        task_id="builder-test-record",
        generation_sha256="b" * 64,
        candidate_tree_sha256=digest,
        candidate_tree_sha256_after=digest,
        candidate_unchanged=True,
        pytest_exit_code=0,
        collected=2,
        passed_count=2,
        failed_count=0,
        skipped_count=0,
        error_count=0,
        passed=True,
    )

    assert record.passed is True
    assert record.network_available is False
    assert record.candidate_mount_read_only is True
    assert record.tests_executed is True
    assert record.implementation_executed is True
    assert (
        record.deterministic_validation_performed
        is False
    )
    assert record.implementation_trusted is False
    assert record.promotion_performed is False
    assert record.execution_performed is False


def test_builder_test_record_rejects_false_success(
) -> None:
    digest = "a" * 64

    with pytest.raises(
        ValueError,
        match="test success conflicts",
    ):
        BuilderCandidateTestRecord(
            task_id="builder-test-record",
            generation_sha256="b" * 64,
            candidate_tree_sha256=digest,
            candidate_tree_sha256_after=digest,
            candidate_unchanged=True,
            pytest_exit_code=1,
            collected=1,
            passed_count=0,
            failed_count=1,
            skipped_count=0,
            error_count=0,
            passed=True,
        )


def test_builder_test_record_rejects_changed_candidate(
) -> None:
    with pytest.raises(
        ValueError,
        match="unchanged claim conflicts",
    ):
        BuilderCandidateTestRecord(
            task_id="builder-test-record",
            generation_sha256="b" * 64,
            candidate_tree_sha256="a" * 64,
            candidate_tree_sha256_after="c" * 64,
            candidate_unchanged=True,
            pytest_exit_code=0,
            collected=1,
            passed_count=1,
            failed_count=0,
            skipped_count=0,
            error_count=0,
            passed=True,
        )
