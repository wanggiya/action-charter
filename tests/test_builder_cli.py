"""Offline CLI tests for Builder proposals."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

import geoagent_harness.builder.service as builder_service
from geoagent_harness.builder import BuilderProposal
from geoagent_harness.cli import app
from geoagent_harness.model import (
    ModelClientError,
    ModelResult,
)

runner = CliRunner()
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeSharedModelClient:
    fail_with_timeout = False

    def __init__(self, _settings) -> None:
        pass

    def complete(self, _request) -> ModelResult:
        if self.fail_with_timeout:
            raise ModelClientError.timeout()

        proposal = BuilderProposal(
            task_id="cli-builder-test",
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
            test_intentions=[
                "Run isolated tests later.",
            ],
        )

        return ModelResult(
            model="fake-builder-model",
            content=json.dumps(
                proposal.model_dump(mode="json")
            ),
        )


def write_request(root: Path) -> Path:
    request_file = root / "request.json"
    request_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "task_id": "cli-builder-test",
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
        ),
        encoding="utf-8",
    )
    return request_file


def configure_fake_model(monkeypatch) -> None:
    monkeypatch.setattr(
        builder_service,
        "SharedModelClient",
        FakeSharedModelClient,
    )
    monkeypatch.setattr(
        builder_service,
        "load_model_settings",
        lambda: object(),
    )


def test_cli_generates_proposal_without_writing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    configure_fake_model(monkeypatch)
    request_file = write_request(tmp_path)

    result = runner.invoke(
        app,
        [
            "builder-propose",
            "--request-file",
            str(request_file),
            "--request-root",
            str(tmp_path),
            "--agents-root",
            str(PROJECT_ROOT / "agents"),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["agent_id"] == "builder"
    assert payload["model"] == "fake-builder-model"
    assert payload["filesystem_modified"] is False
    assert payload["tools_called"] is False
    assert payload["tests_performed"] is False
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is False
    assert payload["execution_performed"] is False


def test_cli_rejects_invalid_request(
    tmp_path: Path,
) -> None:
    request_file = tmp_path / "request.json"
    request_file.write_text(
        "{}",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "builder-propose",
            "--request-file",
            str(request_file),
            "--request-root",
            str(tmp_path),
            "--agents-root",
            str(PROJECT_ROOT / "agents"),
        ],
    )

    assert result.exit_code == 2
    assert "required schema" in result.output


def test_cli_model_timeout_uses_typed_exit_code(
    tmp_path: Path,
    monkeypatch,
) -> None:
    configure_fake_model(monkeypatch)
    FakeSharedModelClient.fail_with_timeout = True
    request_file = write_request(tmp_path)

    try:
        result = runner.invoke(
            app,
            [
                "builder-propose",
                "--request-file",
                str(request_file),
                "--request-root",
                str(tmp_path),
                "--agents-root",
                str(PROJECT_ROOT / "agents"),
            ],
        )
    finally:
        FakeSharedModelClient.fail_with_timeout = False

    assert result.exit_code == 3
    assert "model_timeout" in result.output
