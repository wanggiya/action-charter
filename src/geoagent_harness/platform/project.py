"""Trusted local project-root validation shared by application services."""
from pathlib import Path
from geoagent_harness.contracts.errors import InterfaceApiError


def _trusted_root(project_root: Path) -> Path:
    try:
        resolved = project_root.resolve(strict=True)
    except OSError as exc:
        raise InterfaceApiError("trusted project root is unavailable") from exc
    if not resolved.is_dir():
        raise InterfaceApiError("trusted project root must be a directory")
    return resolved

