"""Existing resource catalogs coordination, independent of HTTP."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Callable, Literal
from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.platform.project import _trusted_root
from geoagent_harness.contracts.interface_limits import (
    INTERFACE_DATA_EXTENSIONS,
    MAX_INTERFACE_DATA_RESOURCES,
)


def interface_data_resource_inventory(project_root: Path) -> dict[str, Any]:
    """List bounded project inputs and existing output directories read-only."""

    root = _trusted_root(project_root)
    input_root = root / "data" / "input"
    output_root = root / "data" / "output"
    inputs: list[dict[str, Any]] = []
    output_directories = ["data/output"]

    if input_root.is_symlink() or output_root.is_symlink():
        raise InterfaceApiError("data roots cannot be symlinks")
    if input_root.is_dir():
        for path in sorted(input_root.rglob("*")):
            if path.is_symlink():
                continue
            if not path.is_file() or path.suffix.lower() not in INTERFACE_DATA_EXTENSIONS:
                continue
            inputs.append({
                "path": path.relative_to(root).as_posix(),
                "name": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
            })
            if len(inputs) > MAX_INTERFACE_DATA_RESOURCES:
                raise InterfaceApiError("input data inventory exceeds its limit")
    if output_root.is_dir():
        for path in sorted(output_root.rglob("*")):
            if path.is_symlink() or not path.is_dir():
                continue
            output_directories.append(path.relative_to(root).as_posix())
            if len(output_directories) > MAX_INTERFACE_DATA_RESOURCES:
                raise InterfaceApiError("output directory inventory exceeds its limit")

    return {
        "schema_version": "1.0",
        "status": "inspected",
        "inputs": inputs,
        "output_directories": output_directories,
        "input_count": len(inputs),
        "inventory_performed": True,
        "files_modified": False,
        "execution_performed": False,
    }


# Trusted context kwargs stay outside transport/model request schemas.
from geoagent_harness.core.execution.actions import task_entrypoint as _task_entrypoint
interface_data_resource_inventory = _task_entrypoint(interface_data_resource_inventory, audit=False)
