"""CLI tests for trusted Builder materialization."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.builder import (
    BuilderGenerationResult,
    BuilderProposal,
    BuilderRequest,
)
from geoagent_harness.cli import app
from geoagent_harness.skill_definitions import (
    candidate_tree_sha256,
)

runner = CliRunner()


def generation() -> BuilderGenerationResult:
    request = BuilderRequest(
        task_id="builder-cli-materialization",
        summary="Propose one adapter.",
        artifacts=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "purpose": "Propose the adapter.",
            }
        ],
    )

    proposal = BuilderProposal(
        task_id="builder-cli-materialization",
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
            }
        ],
    )

    return BuilderGenerationResult(
        model="builder-cli-test-model",
        request=request,
        proposal=proposal,
    )


def write_generation(root: Path) -> Path:
    path = root / "generation.json"
    path.write_text(
        json.dumps(
            generation().model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_cli_materializes_candidate(
    tmp_path: Path,
) -> None:
    generation_root = tmp_path / "generations"
    generation_root.mkdir()
    generation_file = write_generation(
        generation_root
    )
    candidate_root = tmp_path / "candidates"

    result = runner.invoke(
        app,
        [
            "materialize-builder-proposal",
            "--generation-file",
            str(generation_file),
            "--generation-root",
            str(generation_root),
            "--candidate-root",
            str(candidate_root),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)
    candidate = Path(payload["candidate_path"])

    assert candidate.is_dir()
    assert payload["candidate_materialized"] is True
    assert payload["source_generation_modified"] is False
    assert payload["tests_performed"] is False
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is False
    assert payload["execution_performed"] is False
    assert payload["candidate_tree_sha256"] == (
        candidate_tree_sha256(candidate)
    )


def test_cli_rejects_missing_generation(
    tmp_path: Path,
) -> None:
    generation_root = tmp_path / "generations"
    generation_root.mkdir()

    result = runner.invoke(
        app,
        [
            "materialize-builder-proposal",
            "--generation-file",
            str(generation_root / "missing.json"),
            "--generation-root",
            str(generation_root),
            "--candidate-root",
            str(tmp_path / "candidates"),
        ],
    )

    assert result.exit_code == 2
    assert "could not be loaded" in result.output


def test_cli_refuses_existing_candidate(
    tmp_path: Path,
) -> None:
    generation_root = tmp_path / "generations"
    generation_root.mkdir()
    generation_file = write_generation(
        generation_root
    )
    candidate_root = tmp_path / "candidates"

    arguments = [
        "materialize-builder-proposal",
        "--generation-file",
        str(generation_file),
        "--generation-root",
        str(generation_root),
        "--candidate-root",
        str(candidate_root),
    ]

    first = runner.invoke(app, arguments)
    second = runner.invoke(app, arguments)

    assert first.exit_code == 0, first.output
    assert second.exit_code == 2
    assert "already exists" in second.output
