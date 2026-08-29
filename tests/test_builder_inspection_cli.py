"""Offline CLI tests for Builder candidate inspection."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.builder import (
    BuilderGenerationResult,
    BuilderProposal,
    BuilderRequest,
    materialize_builder_proposal,
)
from geoagent_harness.cli import app


runner = CliRunner()


def generation() -> BuilderGenerationResult:
    request = BuilderRequest(
        task_id="builder-inspection-cli",
        summary="Propose one adapter candidate.",
        artifacts=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "purpose": "Propose the adapter.",
            },
        ],
    )

    proposal = BuilderProposal(
        task_id="builder-inspection-cli",
        summary="Proposed one untrusted adapter.",
        files=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "content": (
                    '"""Untrusted adapter candidate."""\n'
                ),
            },
        ],
    )

    return BuilderGenerationResult(
        model="builder-cli-test-model",
        request=request,
        proposal=proposal,
    )


def prepared_candidate(
    tmp_path: Path,
) -> tuple[Path, Path]:
    generation_root = tmp_path / "generations"
    generation_root.mkdir()

    generation_file = (
        generation_root / "generation.json"
    )
    generation_file.write_text(
        json.dumps(
            generation().model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    candidate_root = tmp_path / "candidates"

    materialized = materialize_builder_proposal(
        generation_file=generation_file,
        generation_root=generation_root,
        candidate_root=candidate_root,
    )

    return (
        candidate_root,
        Path(materialized.candidate_path),
    )


def test_cli_inspects_candidate_read_only(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )

    result = runner.invoke(
        app,
        [
            "inspect-builder-candidate",
            str(candidate),
            "--candidate-root",
            str(candidate_root),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["passed"] is True
    assert payload["candidate_modified"] is False
    assert payload["files_imported"] is False
    assert payload["files_executed"] is False
    assert payload["tests_performed"] is False
    assert payload["validation_performed"] is False
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is False
    assert payload["execution_performed"] is False


def test_cli_rejects_tampered_candidate(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )

    target = (
        candidate
        / "src"
        / "geoagent_harness"
        / "skill_adapters"
        / "example.py"
    )
    target.write_text(
        "raise RuntimeError('tampered')\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "inspect-builder-candidate",
            str(candidate),
            "--candidate-root",
            str(candidate_root),
        ],
    )

    assert result.exit_code == 2
    assert (
        "file digest does not match manifest"
        in result.output
    )


def test_cli_rejects_missing_candidate(
    tmp_path: Path,
) -> None:
    candidate_root = tmp_path / "candidates"
    candidate_root.mkdir()

    result = runner.invoke(
        app,
        [
            "inspect-builder-candidate",
            "missing.candidate",
            "--candidate-root",
            str(candidate_root),
        ],
    )

    assert result.exit_code == 2
    assert "candidate is unavailable" in result.output


def test_cli_rejects_candidate_outside_root(
    tmp_path: Path,
) -> None:
    candidate_root, candidate = prepared_candidate(
        tmp_path
    )
    different_root = tmp_path / "different-root"
    different_root.mkdir()

    result = runner.invoke(
        app,
        [
            "inspect-builder-candidate",
            str(candidate),
            "--candidate-root",
            str(different_root),
        ],
    )

    assert result.exit_code == 2
    assert (
        "directly beneath its root"
        in result.output
    )
