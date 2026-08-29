"""Run candidate tests and emit bounded JSON evidence."""

from __future__ import annotations

import hashlib
import importlib
import io
import json
import sys
from contextlib import (
    redirect_stderr,
    redirect_stdout,
)
from pathlib import Path
from typing import Any

import pytest

import geoagent_harness


from geoagent_harness.builder.schemas import (
    BuilderCandidateManifest,
)

CANDIDATE_ROOT = Path("/candidate")
CANDIDATE_SOURCE = (
    CANDIDATE_ROOT
    / "src"
    / "geoagent_harness"
)
CANDIDATE_SKILLS = (
    CANDIDATE_SOURCE / "skills"
)
CANDIDATE_SKILL_ADAPTERS = (
    CANDIDATE_SOURCE / "skill_adapters"
)
CANDIDATE_TESTS = (
    CANDIDATE_ROOT / "tests"
)
SKILL_CANDIDATE_MANIFEST = (
    CANDIDATE_ROOT / "scaffold-manifest.json"
)
BUILDER_CANDIDATE_MANIFEST = (
    CANDIDATE_ROOT / "BUILDER_CANDIDATE.json"
)


class CandidateTestPlugin:
    """Collect deterministic pytest outcome counts."""

    def __init__(self) -> None:
        self.collected = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = 0

    def pytest_collection_finish(
        self,
        session: Any,
    ) -> None:
        self.collected = len(
            session.items
        )

    def pytest_collectreport(
        self,
        report: Any,
    ) -> None:
        if report.failed:
            self.errors += 1

    def pytest_runtest_logreport(
        self,
        report: Any,
    ) -> None:
        if report.when == "call":
            if report.passed:
                self.passed += 1
            elif report.failed:
                self.failed += 1
            elif report.skipped:
                self.skipped += 1
        elif (
            report.when in {"setup", "teardown"}
            and report.failed
        ):
            self.errors += 1


def candidate_tree_sha256(
    root: Path,
) -> str:
    """Hash every candidate file in stable path order."""

    digest = hashlib.sha256()

    paths = sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file()
        ),
        key=lambda path: (
            path.relative_to(root).as_posix()
        ),
    )

    for path in paths:
        if path.is_symlink():
            raise RuntimeError(
                "candidate evidence cannot hash symlinks"
            )

        relative = path.relative_to(
            root
        ).as_posix()

        digest.update(
            relative.encode("utf-8")
        )
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")

    return digest.hexdigest()


def _validate_candidate_layout(
) -> tuple[str, dict[str, str]]:
    """Validate one exact supported candidate layout."""

    if not CANDIDATE_SOURCE.is_dir():
        raise RuntimeError(
            "candidate source package is missing"
        )

    if not CANDIDATE_TESTS.is_dir():
        raise RuntimeError(
            "candidate tests are missing"
        )

    skill_manifest_exists = (
        SKILL_CANDIDATE_MANIFEST.is_file()
    )
    builder_manifest_exists = (
        BUILDER_CANDIDATE_MANIFEST.is_file()
    )

    if (
        skill_manifest_exists
        == builder_manifest_exists
    ):
        raise RuntimeError(
            "candidate must contain exactly one "
            "supported manifest"
        )

    if skill_manifest_exists:
        if not CANDIDATE_SKILLS.is_dir():
            raise RuntimeError(
                "candidate skills package is missing"
            )

        manifest = json.loads(
            SKILL_CANDIDATE_MANIFEST.read_text(
                encoding="utf-8"
            )
        )
        skill_id = manifest.get("skill_id")

        if not isinstance(skill_id, str):
            raise RuntimeError(
                "candidate manifest has no skill ID"
            )

        return "skill", {
            "skill_id": skill_id,
        }

    builder_payload = json.loads(
        BUILDER_CANDIDATE_MANIFEST.read_text(
            encoding="utf-8"
        )
    )
    builder_manifest = (
        BuilderCandidateManifest.model_validate(
            builder_payload
        )
    )

    return "builder", {
        "task_id": builder_manifest.task_id,
        "generation_sha256": (
            builder_manifest.generation_sha256
        ),
    }


def main() -> int:
    """Run tests and emit evidence bound to candidate files."""

    try:
        candidate_type, identity = (
            _validate_candidate_layout()
        )
            
        before_sha256 = candidate_tree_sha256(
            CANDIDATE_ROOT
        )

        geoagent_harness.__path__.insert(
            0,
            CANDIDATE_SOURCE.resolve().as_posix(),
        )

        if candidate_type == "skill":
            skills_package = importlib.import_module(
                "geoagent_harness.skills"
            )

            skills_package.__path__.insert(
                0,
                CANDIDATE_SKILLS.resolve().as_posix(),
            )

        if (
            candidate_type == "builder"
            and CANDIDATE_SKILL_ADAPTERS.is_dir()
        ):
            adapters_package = (
                importlib.import_module(
                    "geoagent_harness.skill_adapters"
                )
            )

            adapters_package.__path__.insert(
                0,
                CANDIDATE_SKILL_ADAPTERS
                .resolve()
                .as_posix(),
            )

        arguments = sys.argv[1:]

        if not arguments:
            arguments = [
                CANDIDATE_TESTS.as_posix(),
                "-q",
                "--disable-warnings",
                "-p",
                "no:cacheprovider",
            ]

        plugin = CandidateTestPlugin()
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()

        with (
            redirect_stdout(captured_stdout),
            redirect_stderr(captured_stderr),
        ):
            exit_code = int(
                pytest.main(
                    arguments,
                    plugins=[plugin],
                )
            )

        after_sha256 = candidate_tree_sha256(
            CANDIDATE_ROOT
        )

        output = captured_stdout.getvalue()
        errors = captured_stderr.getvalue()

        if output:
            print(
                output,
                file=sys.stderr,
                end=(
                    ""
                    if output.endswith("\n")
                    else "\n"
                ),
            )

        if errors:
            print(
                errors,
                file=sys.stderr,
                end=(
                    ""
                    if errors.endswith("\n")
                    else "\n"
                ),
            )

        candidate_unchanged = (
            before_sha256 == after_sha256
        )

        passed = (
            exit_code == 0
            and plugin.collected > 0
            and plugin.failed == 0
            and plugin.errors == 0
            and candidate_unchanged
        )

        record: dict[str, Any] = {
            "schema_version": "1.0",
            "candidate_tree_sha256": (
                before_sha256
            ),
            "candidate_tree_sha256_after": (
                after_sha256
            ),
            "candidate_unchanged": (
                candidate_unchanged
            ),
            "pytest_exit_code": exit_code,
            "collected": plugin.collected,
            "passed_count": plugin.passed,
            "failed_count": plugin.failed,
            "skipped_count": plugin.skipped,
            "error_count": plugin.errors,
            "passed": passed,
            "network_available": False,
            "candidate_mount_read_only": True,
            "tests_executed": True,
            "implementation_executed": True,
            "registry_modified": False,
            "promotion_performed": False,
        }

        if candidate_type == "skill":
            record["skill_id"] = identity[
                "skill_id"
            ]
        else:
            record.update(
                {
                    "record_type": (
                        "builder_candidate_test"
                    ),
                    "task_id": identity["task_id"],
                    "generation_sha256": identity[
                        "generation_sha256"
                    ],
                    (
                        "deterministic_validation_"
                        "performed"
                    ): False,
                    "implementation_trusted": False,
                    "execution_performed": False,
                }
            )

        print(
            json.dumps(
                record,
                sort_keys=True,
                separators=(",", ":"),
            )
        )

        return 0 if passed else 1

    except (
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())