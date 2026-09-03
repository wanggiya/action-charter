"""Offline CLI tests for immutable Critic-result records."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

import geoagent_harness.critic as critic
from geoagent_harness.cli import app
from geoagent_harness.critic import (
    CriticResultStorageError,
    load_critic_result_record,
)
from tests.test_critic_result_records import critic_result


runner = CliRunner()


def test_cli_records_critic_result_without_changing_status(
    tmp_path: Path,
    monkeypatch,
) -> None:
    active_result = critic_result()

    def critique(**kwargs):
        assert kwargs["trace_path"] == Path("task.json")
        assert kwargs["report_path"] == Path("task.md")
        assert kwargs["trace_root"] == Path("traces")
        assert kwargs["report_root"] == Path("reports")
        return active_result

    monkeypatch.setattr(critic, "critique_task", critique)
    record_root = tmp_path / "critic-results"

    result = runner.invoke(
        app,
        [
            "record-critic-result",
            "task.json",
            "task.md",
            "--record-root",
            str(record_root),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["deterministic_status"] == (
        "validated_success"
    )
    assert payload["critic_result_recorded"] is True
    assert payload["authoritative_status_changed"] is False
    assert payload["release_created"] is False
    assert payload["execution_performed"] is False

    record = load_critic_result_record(
        Path(payload["record_file"]),
        record_root=record_root,
    )
    assert record.critic_result == active_result


def test_cli_reports_critic_record_storage_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        critic,
        "critique_task",
        lambda **kwargs: critic_result(),
    )

    def reject(*args, **kwargs):
        raise CriticResultStorageError(
            "Critic-result package already exists"
        )

    monkeypatch.setattr(
        critic,
        "persist_critic_result_record",
        reject,
    )

    result = runner.invoke(
        app,
        [
            "record-critic-result",
            "task.json",
            "task.md",
            "--record-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 2
    assert "already exists" in result.output
