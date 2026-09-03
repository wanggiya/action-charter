"""Tests for secure spatial-data contract storage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from geoagent_harness.spatial_contracts import (
    SpatialDataContractStorageError,
    canonical_spatial_data_contract_json,
    load_spatial_data_contract,
    spatial_data_contract_sha256,
)


def contract_payload() -> dict:
    """Return one minimal valid vector contract."""

    return {
        "schema_version": "1.0",
        "contract_id": "storage_points",
        "contract_version": "1.0.0",
        "dataset_kind": "vector",
        "description": "Storage test contract.",
        "expected_crs": "EPSG:4326",
        "allowed_geometry_types": ["Point"],
        "required_fields": [
            {
                "name": "feature_id",
                "field_type": "integer",
                "nullable": False,
                "max_null_fraction": 0.0,
            }
        ],
        "unique_keys": [
            {
                "fields": ["feature_id"],
                "allow_nulls": False,
            }
        ],
    }


def test_loads_json_contract_and_hashes_canonically(
    tmp_path: Path,
) -> None:
    path = tmp_path / "points.contract.json"
    path.write_text(
        json.dumps(contract_payload(), indent=2) + "\n",
        encoding="utf-8",
    )

    contract = load_spatial_data_contract(
        path,
        contract_root=tmp_path,
    )

    canonical = canonical_spatial_data_contract_json(
        contract
    )

    assert contract.contract_id == "storage_points"
    assert canonical == canonical.strip()
    assert len(spatial_data_contract_sha256(contract)) == 64


def test_json_and_yaml_have_same_contract_digest(
    tmp_path: Path,
) -> None:
    payload = contract_payload()
    json_path = tmp_path / "points.json"
    yaml_path = tmp_path / "points.yaml"

    json_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    yaml_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )

    json_contract = load_spatial_data_contract(
        json_path,
        contract_root=tmp_path,
    )
    yaml_contract = load_spatial_data_contract(
        yaml_path,
        contract_root=tmp_path,
    )

    assert spatial_data_contract_sha256(
        json_contract
    ) == spatial_data_contract_sha256(yaml_contract)


def test_rejects_contract_path_escape(
    tmp_path: Path,
) -> None:
    root = tmp_path / "contracts"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text(
        json.dumps(contract_payload()),
        encoding="utf-8",
    )

    with pytest.raises(
        SpatialDataContractStorageError,
        match="directly beneath",
    ):
        load_spatial_data_contract(
            outside,
            contract_root=root,
        )


def test_rejects_nested_contract_file(
    tmp_path: Path,
) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    path = nested / "points.yaml"
    path.write_text(
        yaml.safe_dump(contract_payload()),
        encoding="utf-8",
    )

    with pytest.raises(
        SpatialDataContractStorageError,
        match="directly beneath",
    ):
        load_spatial_data_contract(
            path,
            contract_root=tmp_path,
        )


def test_rejects_symlinked_contract_file(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.json"
    target.write_text(
        json.dumps(contract_payload()),
        encoding="utf-8",
    )
    link = tmp_path / "linked.json"
    link.symlink_to(target)

    with pytest.raises(
        SpatialDataContractStorageError,
        match="file cannot be a symlink",
    ):
        load_spatial_data_contract(
            link,
            contract_root=tmp_path,
        )


def test_rejects_unsupported_contract_suffix(
    tmp_path: Path,
) -> None:
    path = tmp_path / "points.txt"
    path.write_text(
        json.dumps(contract_payload()),
        encoding="utf-8",
    )

    with pytest.raises(
        SpatialDataContractStorageError,
        match="must be JSON or YAML",
    ):
        load_spatial_data_contract(
            path,
            contract_root=tmp_path,
        )


def test_rejects_malformed_contract(
    tmp_path: Path,
) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text(
        "contract_id: [broken\n",
        encoding="utf-8",
    )

    with pytest.raises(
        SpatialDataContractStorageError,
        match="invalid JSON or YAML",
    ):
        load_spatial_data_contract(
            path,
            contract_root=tmp_path,
        )


def test_rejects_schema_invalid_contract(
    tmp_path: Path,
) -> None:
    payload = contract_payload()
    payload["filesystem_modified"] = True
    path = tmp_path / "unsafe.json"
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        SpatialDataContractStorageError,
        match="schema validation",
    ):
        load_spatial_data_contract(
            path,
            contract_root=tmp_path,
        )
