"""Secure loading and canonical hashing of spatial-data contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from geoagent_harness.spatial_contracts.schemas import (
    VectorSpatialDataContract,
)


MAX_SPATIAL_CONTRACT_BYTES = 250_000
SUPPORTED_CONTRACT_SUFFIXES = {
    ".json",
    ".yaml",
    ".yml",
}


class SpatialDataContractStorageError(RuntimeError):
    """Raised when a stored spatial contract is unsafe or invalid."""


def canonical_spatial_data_contract_json(
    contract: VectorSpatialDataContract,
) -> str:
    """Return deterministic canonical JSON for one contract."""

    return json.dumps(
        contract.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def spatial_data_contract_sha256(
    contract: VectorSpatialDataContract,
) -> str:
    """Hash the complete validated contract canonically."""

    return hashlib.sha256(
        canonical_spatial_data_contract_json(
            contract
        ).encode("utf-8")
    ).hexdigest()


def _safe_contract_path(
    contract_file: Path,
    *,
    contract_root: Path,
) -> Path:
    """Require one direct non-symlink file beneath its root."""

    if contract_root.is_symlink():
        raise SpatialDataContractStorageError(
            "spatial contract root cannot be a symlink"
        )

    try:
        root = contract_root.resolve(strict=True)
    except OSError as exc:
        raise SpatialDataContractStorageError(
            "spatial contract root is unavailable"
        ) from exc

    if not root.is_dir():
        raise SpatialDataContractStorageError(
            "spatial contract root must be a directory"
        )

    candidate = (
        contract_file
        if contract_file.is_absolute()
        else root / contract_file
    )

    if candidate.is_symlink():
        raise SpatialDataContractStorageError(
            "spatial contract file cannot be a symlink"
        )

    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise SpatialDataContractStorageError(
            "spatial contract file is unavailable"
        ) from exc

    if resolved.parent != root:
        raise SpatialDataContractStorageError(
            "spatial contract file must be directly beneath "
            "the approved root"
        )

    if not resolved.is_file():
        raise SpatialDataContractStorageError(
            "spatial contract path must be a regular file"
        )

    if resolved.suffix.lower() not in SUPPORTED_CONTRACT_SUFFIXES:
        raise SpatialDataContractStorageError(
            "spatial contract file must be JSON or YAML"
        )

    return resolved


def load_spatial_data_contract(
    contract_file: Path,
    *,
    contract_root: Path,
) -> VectorSpatialDataContract:
    """Load one bounded schema-valid contract without mutation."""

    safe_path = _safe_contract_path(
        contract_file,
        contract_root=contract_root,
    )

    try:
        size = safe_path.stat().st_size
    except OSError as exc:
        raise SpatialDataContractStorageError(
            "spatial contract metadata is unavailable"
        ) from exc

    if size < 1:
        raise SpatialDataContractStorageError(
            "spatial contract file is empty"
        )

    if size > MAX_SPATIAL_CONTRACT_BYTES:
        raise SpatialDataContractStorageError(
            "spatial contract file exceeds the size limit"
        )

    try:
        raw = safe_path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise SpatialDataContractStorageError(
            "spatial contract file is not valid UTF-8"
        ) from exc
    except OSError as exc:
        raise SpatialDataContractStorageError(
            "spatial contract file could not be read"
        ) from exc

    try:
        if safe_path.suffix.lower() == ".json":
            payload: Any = json.loads(raw)
        else:
            payload = yaml.safe_load(raw)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise SpatialDataContractStorageError(
            "spatial contract file contains invalid JSON or YAML"
        ) from exc

    if not isinstance(payload, dict):
        raise SpatialDataContractStorageError(
            "spatial contract must contain one object"
        )

    try:
        return VectorSpatialDataContract.model_validate(
            payload
        )
    except ValidationError as exc:
        raise SpatialDataContractStorageError(
            "spatial contract failed schema validation"
        ) from exc
