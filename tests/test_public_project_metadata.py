"""Public ActionCharter project metadata contracts."""

from __future__ import annotations

from pathlib import Path

import yaml


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
