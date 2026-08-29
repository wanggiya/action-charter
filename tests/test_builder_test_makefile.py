"""Static tests for Builder candidate-test Make targets."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]


def makefile_source() -> str:
    return (
        PROJECT_ROOT / "Makefile"
    ).read_text(encoding="utf-8")


def test_builder_test_target_uses_existing_runner(
) -> None:
    source = makefile_source()

    assert "builder-candidate-test:" in source
    assert (
        "BUILDER_CANDIDATE_DIR is required"
        in source
    )
    assert (
        'SKILL_CANDIDATE_DIR="$(abspath '
        '$(BUILDER_CANDIDATE_DIR))"'
        in source
    )
    assert (
        "run --rm skill-test-runner"
        in source
    )


def test_builder_record_target_writes_on_host(
) -> None:
    source = makefile_source()

    assert (
        "builder-candidate-test-record:"
        in source
    )
    assert (
        "BUILDER_TEST_RECORD_FILE is required"
        in source
    )
    assert (
        '> "$(BUILDER_TEST_RECORD_FILE)"'
        in source
    )
    assert (
        "Builder candidate test record:"
        in source
    )
