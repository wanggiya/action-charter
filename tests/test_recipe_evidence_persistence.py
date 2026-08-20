"""Tests for durable recipe evidence persistence."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.recipes import (
    evidence_persistence as persistence,
)
from geoagent_harness.recipes.evidence import (
    RecipeEvidenceError,
)
from geoagent_harness.recipes.evidence_persistence import (
    RecipeEvidencePersistenceError,
    persist_recipe_run,
)
from geoagent_harness.recipes.evidence_storage import (
    recipe_evidence_sha256,
    recipe_run_result_sha256,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
)
from tests.test_recipe_evidence_schemas import (
    evidence as example_evidence,
)


RECORDED_AT = datetime(
    2026,
    8,
    19,
    12,
    0,
    tzinfo=timezone.utc,
)


def settings(
    tmp_path: Path,
) -> MCPSettings:
    return MCPSettings(
        project_root=tmp_path,
        input_root=tmp_path / "data/input",
        output_root=tmp_path / "data/output",
        recipe_run_root=tmp_path / "recipe-runs",
        recipe_evidence_root=(
            tmp_path / "recipe-evidence"
        ),
        report_root=tmp_path / "reports",
    )


def test_completed_run_is_persisted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = example_evidence()
    run_result = evidence.run_result
    active_settings = settings(tmp_path)

    run_path = (
        active_settings.recipe_run_root
        / "run.json"
    )
    evidence_path = (
        active_settings.recipe_evidence_root
        / "evidence.json"
    )
    report_path = (
        active_settings.report_root
        / "report.md"
    )

    monkeypatch.setattr(
        persistence,
        "build_recipe_run_evidence",
        lambda **_kwargs: evidence,
    )
    monkeypatch.setattr(
        persistence,
        "render_recipe_evidence_report",
        lambda _evidence: "# report\n",
    )
    monkeypatch.setattr(
        persistence,
        "write_recipe_run_result",
        lambda *_args, **_kwargs: run_path,
    )
    monkeypatch.setattr(
        persistence,
        "write_recipe_evidence",
        lambda *_args, **_kwargs: evidence_path,
    )
    monkeypatch.setattr(
        persistence,
        "write_recipe_evidence_report",
        lambda *_args, **_kwargs: report_path,
    )

    record = persist_recipe_run(
        run_result=run_result,
        registry=SkillRegistry(
            schema_version="1.0",
            skills=[],
        ),
        settings=active_settings,
        recorded_at=RECORDED_AT,
    )

    assert record.recipe_id == (
        run_result.recipe_id
    )
    assert record.recipe_sha256 == (
        run_result.recipe_sha256
    )
    assert record.approval_id == (
        run_result.approval_id
    )
    assert record.final_status == (
        run_result.final_status
    )

    assert record.run_result_sha256 == (
        recipe_run_result_sha256(
            run_result
        )
    )
    assert record.evidence_sha256 == (
        recipe_evidence_sha256(
            evidence
        )
    )

    assert record.run_result_path == (
        "recipe-runs/run.json"
    )
    assert record.evidence_path == (
        "recipe-evidence/evidence.json"
    )
    assert record.report_path == (
        "reports/report.md"
    )

    assert record.execution_performed is True
    assert record.evidence_recorded is True
    assert record.report_written is True


def test_evidence_is_built_before_any_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = example_evidence()
    writes: list[str] = []

    def fail_build(**_kwargs):
        raise RecipeEvidenceError(
            "evidence construction failed"
        )

    monkeypatch.setattr(
        persistence,
        "build_recipe_run_evidence",
        fail_build,
    )
    monkeypatch.setattr(
        persistence,
        "write_recipe_run_result",
        lambda *_args, **_kwargs: writes.append(
            "run"
        ),
    )
    monkeypatch.setattr(
        persistence,
        "write_recipe_evidence",
        lambda *_args, **_kwargs: writes.append(
            "evidence"
        ),
    )
    monkeypatch.setattr(
        persistence,
        "write_recipe_evidence_report",
        lambda *_args, **_kwargs: writes.append(
            "report"
        ),
    )

    with pytest.raises(
        RecipeEvidencePersistenceError,
        match="manual review is required",
    ):
        persist_recipe_run(
            run_result=evidence.run_result,
            registry=SkillRegistry(
                schema_version="1.0",
                skills=[],
            ),
            settings=settings(tmp_path),
            recorded_at=RECORDED_AT,
        )

    assert writes == []


def test_persistence_failure_requires_manual_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = example_evidence()
    active_settings = settings(tmp_path)

    monkeypatch.setattr(
        persistence,
        "build_recipe_run_evidence",
        lambda **_kwargs: evidence,
    )
    monkeypatch.setattr(
        persistence,
        "render_recipe_evidence_report",
        lambda _evidence: "# report\n",
    )

    def fail_write(*_args, **_kwargs):
        raise OSError(
            "simulated storage failure"
        )

    monkeypatch.setattr(
        persistence,
        "write_recipe_run_result",
        fail_write,
    )

    with pytest.raises(
        RecipeEvidencePersistenceError,
        match="manual review is required",
    ):
        persist_recipe_run(
            run_result=evidence.run_result,
            registry=SkillRegistry(
                schema_version="1.0",
                skills=[],
            ),
            settings=active_settings,
            recorded_at=RECORDED_AT,
        )

