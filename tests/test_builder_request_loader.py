"""Tests for bounded Builder request loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderRequestLoadError,
    load_builder_request,
)
from geoagent_harness.builder.request_loader import (
    MAX_BUILDER_REQUEST_BYTES,
)


def valid_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "task_id": "loader-test",
        "summary": "Propose one adapter.",
        "artifacts": [
            {
                "kind": "adapter",
                "path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "purpose": "Propose the adapter.",
            }
        ],
        "context_references": [],
        "filesystem_write_requested": False,
        "tool_access_requested": False,
        "execution_requested": False,
        "approval_requested": False,
        "promotion_requested": False,
    }


def write_request(root: Path) -> Path:
    path = root / "request.json"
    path.write_text(
        json.dumps(valid_payload()),
        encoding="utf-8",
    )
    return path


def test_loads_valid_request(tmp_path: Path) -> None:
    request_file = write_request(tmp_path)

    request = load_builder_request(
        request_file,
        request_root=tmp_path,
    )

    assert request.task_id == "loader-test"
    assert request.filesystem_write_requested is False
    assert request.execution_requested is False


def test_rejects_path_outside_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "approved"
    root.mkdir()
    outside = write_request(tmp_path)

    with pytest.raises(
        BuilderRequestLoadError,
        match="directly beneath",
    ):
        load_builder_request(
            outside,
            request_root=root,
        )


def test_rejects_symlinked_request(
    tmp_path: Path,
) -> None:
    target = write_request(tmp_path)
    link = tmp_path / "linked.json"
    link.symlink_to(target)

    with pytest.raises(
        BuilderRequestLoadError,
        match="cannot be a symlink",
    ):
        load_builder_request(
            link,
            request_root=tmp_path,
        )


def test_rejects_nested_request(
    tmp_path: Path,
) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    request_file = write_request(nested)

    with pytest.raises(
        BuilderRequestLoadError,
        match="directly beneath",
    ):
        load_builder_request(
            request_file,
            request_root=tmp_path,
        )


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("", "empty"),
        ("not-json", "invalid JSON"),
        ("[]", "one JSON object"),
        ("{}", "required schema"),
    ],
)
def test_rejects_invalid_request_content(
    tmp_path: Path,
    content: str,
    message: str,
) -> None:
    request_file = tmp_path / "request.json"
    request_file.write_text(
        content,
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderRequestLoadError,
        match=message,
    ):
        load_builder_request(
            request_file,
            request_root=tmp_path,
        )


def test_rejects_oversized_request(
    tmp_path: Path,
) -> None:
    request_file = tmp_path / "request.json"
    request_file.write_text(
        "x" * (MAX_BUILDER_REQUEST_BYTES + 1),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderRequestLoadError,
        match="size limit",
    ):
        load_builder_request(
            request_file,
            request_root=tmp_path,
        )

