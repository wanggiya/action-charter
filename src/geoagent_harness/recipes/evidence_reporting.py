"""Deterministic Markdown reporting for recipe evidence."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.recipes.evidence_schemas import (
    RecipeRunEvidence,
)
from geoagent_harness.recipes.evidence_storage import (
    recipe_evidence_sha256,
)


class RecipeEvidenceReportError(RuntimeError):
    """Raised when a recipe evidence report is unsafe."""


def render_recipe_evidence_report(
    evidence: RecipeRunEvidence,
) -> str:
    """Render an authoritative deterministic report."""

    evidence_digest = recipe_evidence_sha256(
        evidence
    )

    lines = [
        f"# Recipe Run: {evidence.recipe_id}",
        "",
        "## Outcome",
        "",
        f"- Final status: `{evidence.final_status}`",
        f"- Recipe SHA-256: `{evidence.recipe_sha256}`",
        f"- Approval ID: `{evidence.approval_id}`",
        f"- Evidence SHA-256: `{evidence_digest}`",
        f"- Recorded at: `{evidence.recorded_at.isoformat()}`",
        "",
        "## Steps",
        "",
    ]

    for step in evidence.run_result.step_results:
        lines.extend(
            [
                f"### {step.step_id}: `{step.skill_id}`",
                "",
                f"- Status: `{step.status}`",
                (
                    "- Execution performed: "
                    f"`{str(step.execution_performed).lower()}`"
                ),
                (
                    "- Validation performed: "
                    f"`{str(step.validation_performed).lower()}`"
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Artifacts",
            "",
        ]
    )

    for artifact in evidence.artifacts:
        producer = (
            artifact.producer_step_id
            or "external_input"
        )

        lines.extend(
            [
                f"### `{artifact.artifact_id}`",
                "",
                f"- Role: `{artifact.role.value}`",
                f"- Path: `{artifact.path}`",
                f"- SHA-256: `{artifact.sha256}`",
                f"- Size: `{artifact.size_bytes}` bytes",
                f"- Media type: `{artifact.media_type}`",
                f"- Producer step: `{producer}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Lineage",
            "",
        ]
    )

    if evidence.lineage:
        for edge in evidence.lineage:
            lines.append(
                "- "
                f"`{edge.source_artifact_id}` → "
                f"`{edge.target_artifact_id}` "
                f"through `{edge.step_id}` "
                f"using `{edge.skill_id}`"
            )
    else:
        lines.append(
            "- No lineage edges were recorded."
        )

    lines.extend(
        [
            "",
            "## Skill Versions",
            "",
        ]
    )

    for skill_id in sorted(
        evidence.skill_versions
    ):
        lines.append(
            f"- `{skill_id}`: "
            f"`{evidence.skill_versions[skill_id]}`"
        )

    lines.extend(
        [
            "",
            "## Warnings",
            "",
        ]
    )

    if evidence.warnings:
        lines.extend(
            f"- {warning}"
            for warning in evidence.warnings
        )
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Evidence Policy",
            "",
            (
                "- This report was generated "
                "deterministically."
            ),
            (
                "- No model determined the final "
                "status."
            ),
            (
                "- Artifact digests identify exact "
                "recorded files."
            ),
            "- Secrets redacted: `true`",
            "",
        ]
    )

    return "\n".join(lines)


def recipe_evidence_report_path(
    evidence: RecipeRunEvidence,
    *,
    report_root: Path,
) -> Path:
    """Return the digest-addressed report path."""

    root = report_root.resolve()
    digest = recipe_evidence_sha256(evidence)

    return (
        root
        / f"{evidence.recipe_id}.{digest}.md"
    )


def write_recipe_evidence_report(
    evidence: RecipeRunEvidence,
    *,
    report_root: Path,
) -> Path:
    """Immutably write one deterministic report."""

    root = report_root.resolve()
    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = recipe_evidence_report_path(
        evidence,
        report_root=root,
    )

    try:
        with path.open(
            "x",
            encoding="utf-8",
        ) as stream:
            stream.write(
                render_recipe_evidence_report(
                    evidence
                )
            )
    except FileExistsError as exc:
        raise RecipeEvidenceReportError(
            "recipe evidence report already exists; "
            "overwriting is blocked"
        ) from exc
    except OSError as exc:
        raise RecipeEvidenceReportError(
            "recipe evidence report could not be "
            "written"
        ) from exc

    return path