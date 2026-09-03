"""Regression tests for deterministic Planner context bounds."""

import hashlib
import json
import shutil
from pathlib import Path

from geoagent_harness.agent_manifest import load_agent_manifest
from geoagent_harness.context_pack import build_context_pack
from geoagent_harness.context_pack.builder import (
    CURRENT_STATUS_TRUNCATION_MARKER,
    MAX_CURRENT_STATUS_CHARACTERS,
)
from geoagent_harness.context_pack.redaction import redact_text
from geoagent_harness.planner.prompt import build_planner_request


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_with_large_status(tmp_path: Path) -> tuple[Path, str]:
    shutil.copytree(PROJECT_ROOT / "context", tmp_path / "context")
    source = (
        "# Current Status\n"
        + "head-section\n"
        + ("bounded-context-evidence\n" * 3000)
        + "latest-section\n"
    )
    (tmp_path / "context/CURRENT_STATUS.md").write_text(
        source,
        encoding="utf-8",
    )
    return tmp_path, source


def test_large_current_status_is_bounded_with_full_digest(
    tmp_path: Path,
) -> None:
    project_root, source = project_with_large_status(tmp_path)

    pack = build_context_pack(
        "Inspect the sample vector, load it, validate it, and report.",
        project_root,
    )
    clean_source = redact_text(source)

    assert len(pack.current_status) == MAX_CURRENT_STATUS_CHARACTERS
    assert CURRENT_STATUS_TRUNCATION_MARKER in pack.current_status
    assert pack.current_status.startswith(clean_source[:1000])
    assert pack.current_status.endswith(clean_source[-1000:])
    assert pack.warnings == [
        "context/CURRENT_STATUS.md was truncated to "
        "16000 characters for model context"
    ]

    reference = next(
        item
        for item in pack.context_references
        if item.path == "context/CURRENT_STATUS.md"
    )
    assert reference.sha256 == hashlib.sha256(
        source.encode("utf-8")
    ).hexdigest()


def test_planner_prompt_remains_bounded_as_status_grows(
    tmp_path: Path,
) -> None:
    project_root, _ = project_with_large_status(tmp_path)
    pack = build_context_pack(
        "Inspect the sample vector, load it, validate it, and report.",
        project_root,
    )
    manifest = load_agent_manifest(
        "planner",
        PROJECT_ROOT / "agents",
    )
    request = build_planner_request(pack, manifest)

    total_characters = sum(
        len(message.content) for message in request.messages
    )
    assert total_characters < 60_000
    user_payload = json.loads(request.messages[1].content)
    assert user_payload["context_pack"]["warnings"] == pack.warnings
