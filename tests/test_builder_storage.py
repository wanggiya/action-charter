"""Tests for bounded Builder generation storage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderGenerationResult,
    BuilderGenerationStorageError,
    BuilderProposal,
    BuilderRequest,
    builder_generation_sha256,
    canonical_builder_generation_json,
    load_builder_generation,
)
from geoagent_harness.builder.storage import (
    MAX_BUILDER_GENERATION_BYTES,
)


def generation() -> BuilderGenerationResult:
    request = BuilderRequest(
        task_id="builder-storage-test",
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
        task_id="builder-storage-test",
        summary="Proposed one untrusted adapter.",
        files=[
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "content": (
                    '"""Untrusted candidate."""\n'
                ),
            }
        ],
    )

    return BuilderGenerationResult(
        model="builder-test-model",
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


def test_loads_valid_generation(
    tmp_path: Path,
) -> None:
    path = write_generation(tmp_path)

    loaded = load_builder_generation(
        path,
        generation_root=tmp_path,
    )

    assert loaded.agent_id == "builder"
    assert loaded.proposal.task_id == (
        loaded.request.task_id
    )
    assert loaded.filesystem_modified is False
    assert loaded.implementation_trusted is False
    assert loaded.execution_performed is False


def test_generation_digest_is_canonical() -> None:
    first = generation()
    second = BuilderGenerationResult.model_validate_json(
        canonical_builder_generation_json(first)
    )

    assert builder_generation_sha256(first) == (
        builder_generation_sha256(second)
    )
    assert len(builder_generation_sha256(first)) == 64


def test_generation_digest_changes_with_content() -> None:
    original = generation()
    payload = original.model_dump(mode="json")
    payload["proposal"]["files"][0]["content"] = (
        '"""Changed candidate."""\n'
    )
    changed = BuilderGenerationResult.model_validate(
        payload
    )

    assert builder_generation_sha256(original) != (
        builder_generation_sha256(changed)
    )


def test_rejects_generation_outside_root(
    tmp_path: Path,
) -> None:
    approved = tmp_path / "approved"
    approved.mkdir()
    outside = write_generation(tmp_path)

    with pytest.raises(
        BuilderGenerationStorageError,
        match="directly beneath",
    ):
        load_builder_generation(
            outside,
            generation_root=approved,
        )


def test_rejects_symlinked_generation(
    tmp_path: Path,
) -> None:
    target = write_generation(tmp_path)
    link = tmp_path / "linked.json"
    link.symlink_to(target)

    with pytest.raises(
        BuilderGenerationStorageError,
        match="cannot be a symlink",
    ):
        load_builder_generation(
            link,
            generation_root=tmp_path,
        )


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("", "empty"),
        ("not-json", "invalid JSON"),
        ("[]", "one JSON object"),
        ("{}", "schema validation"),
    ],
)
def test_rejects_invalid_generation(
    tmp_path: Path,
    content: str,
    message: str,
) -> None:
    path = tmp_path / "generation.json"
    path.write_text(
        content,
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderGenerationStorageError,
        match=message,
    ):
        load_builder_generation(
            path,
            generation_root=tmp_path,
        )


def test_rejects_oversized_generation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "generation.json"
    path.write_text(
        "x" * (MAX_BUILDER_GENERATION_BYTES + 1),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderGenerationStorageError,
        match="size limit",
    ):
        load_builder_generation(
            path,
            generation_root=tmp_path,
        )


def test_rejects_changed_artifact_path(
    tmp_path: Path,
) -> None:
    payload = generation().model_dump(mode="json")
    payload["proposal"]["files"][0]["path"] = (
        "src/geoagent_harness/"
        "skill_adapters/different.py"
    )

    path = tmp_path / "generation.json"
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderGenerationStorageError,
        match="artifacts do not match",
    ):
        load_builder_generation(
            path,
            generation_root=tmp_path,
        )
