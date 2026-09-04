"""Public ActionCharter project metadata contracts."""

from __future__ import annotations

from pathlib import Path
import tomllib

import yaml

from geoagent_harness import __version__


ROOT = Path(__file__).resolve().parents[1]


def test_required_public_project_files_exist() -> None:
    for filename in (
        "LICENSE",
        "NOTICE",
        "README.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "CHANGELOG.md",
        "CITATION.cff",
    ):
        assert (ROOT / filename).is_file(), filename


def test_citation_identifies_project_author_and_license() -> None:
    payload = yaml.safe_load((ROOT / "CITATION.cff").read_text())

    assert payload["title"] == "ActionCharter"
    assert payload["license"] == "Apache-2.0"
    assert payload["authors"] == [
        {"family-names": "Qi", "given-names": "Jay"}
    ]


def test_notice_identifies_project_author() -> None:
    notice = (ROOT / "NOTICE").read_text()

    assert "ActionCharter" in notice
    assert "Copyright 2026 Jay Qi" in notice


def test_readme_documents_legacy_compatibility_names() -> None:
    readme = (ROOT / "README.md").read_text()

    assert readme.startswith("# ActionCharter\n")
    assert "`geoagent_harness`" in readme
    assert "`geoagent`" in readme
    assert "GIS" in readme


def test_container_builds_include_declared_license_file() -> None:
    for relative_path in (
        "docker/agent/Dockerfile",
        "docker/gis-tools/Dockerfile",
        "docker/skill-test-runner/Dockerfile",
        "docker/workflow-runner/Dockerfile",
    ):
        dockerfile = (ROOT / relative_path).read_text()

        assert "COPY pyproject.toml README.md LICENSE ./" in dockerfile


def test_public_contribution_templates_exist() -> None:
    for relative_path in (
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
    ):
        assert (ROOT / relative_path).is_file(), relative_path


def test_public_release_version_is_consistent() -> None:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        project_version = tomllib.load(stream)["project"]["version"]

    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text())

    assert project_version == "0.9.0"
    assert citation["version"] == project_version
    assert __version__ == project_version
