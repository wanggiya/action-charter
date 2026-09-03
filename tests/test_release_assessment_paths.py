"""Regression tests for release evidence path conventions."""

from pathlib import Path

import pytest

from geoagent_harness.releases.assessment import (
    ReleaseAssessmentError,
    _safe_file,
)


def test_accepts_project_relative_path_including_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "plans"
    root.mkdir()
    plan = root / "workflow.json"
    plan.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert _safe_file(
        Path("plans/workflow.json"),
        root=Path("plans"),
    ) == plan


def test_accepts_filename_relative_to_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "traces"
    root.mkdir()
    trace = root / "workflow.json"
    trace.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert _safe_file(
        Path("workflow.json"),
        root=Path("traces"),
    ) == trace


def test_rejects_symlinked_parent_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "evidence"
    real = root / "real"
    real.mkdir(parents=True)
    (real / "record.json").write_text("{}", encoding="utf-8")
    (root / "linked").symlink_to(real, target_is_directory=True)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(
        ReleaseAssessmentError,
        match="symlink",
    ):
        _safe_file(
            Path("evidence/linked/record.json"),
            root=Path("evidence"),
        )
