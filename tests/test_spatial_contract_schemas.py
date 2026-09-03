"""Tests for versioned vector spatial-data contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from geoagent_harness.spatial_contracts import VectorSpatialDataContract


def valid_contract_payload() -> dict:
    """Return one complete valid contract payload."""

    return {
        "schema_version": "1.0",
        "contract_id": "sample_points",
        "contract_version": "1.0.0",
        "dataset_kind": "vector",
        "description": "Contract for the presentation sample-point layer.",
        "expected_crs": "EPSG:4326",
        "allowed_geometry_types": ["Point"],
        "mixed_geometry_allowed": False,
        "required_fields": [
            {
                "name": "feature_id",
                "field_type": "integer",
                "nullable": False,
                "max_null_fraction": 0.0,
            },
            {
                "name": "name",
                "field_type": "string",
                "nullable": True,
                "max_null_fraction": 0.1,
            },
        ],
        "unique_keys": [
            {
                "fields": ["feature_id"],
                "allow_nulls": False,
            }
        ],
        "feature_count": {"minimum": 1, "maximum": 1000},
        "geometry_quality": {
            "max_invalid_count": 0,
            "max_empty_count": 0,
            "max_null_count": 0,
            "max_duplicate_count": 0,
        },
        "permitted_extent": {
            "min_x": -180.0,
            "min_y": -90.0,
            "max_x": 180.0,
            "max_y": 90.0,
        },
    }


def test_accepts_complete_vector_contract() -> None:
    contract = VectorSpatialDataContract.model_validate(valid_contract_payload())

    assert contract.contract_id == "sample_points"
    assert contract.contract_version == "1.0.0"
    assert contract.expected_crs == "EPSG:4326"
    assert contract.dataset_kind == "vector"
    assert contract.filesystem_modified is False
    assert contract.database_modified is False
    assert contract.execution_performed is False


def test_normalizes_epsg_identifier() -> None:
    payload = valid_contract_payload()
    payload["expected_crs"] = "epsg:04326"

    contract = VectorSpatialDataContract.model_validate(payload)

    assert contract.expected_crs == "EPSG:4326"


def test_rejects_duplicate_required_fields() -> None:
    payload = valid_contract_payload()
    payload["required_fields"].append(dict(payload["required_fields"][0]))

    with pytest.raises(
        ValidationError,
        match="required field names must be unique",
    ):
        VectorSpatialDataContract.model_validate(payload)


def test_rejects_undeclared_unique_key() -> None:
    payload = valid_contract_payload()
    payload["unique_keys"] = [
        {"fields": ["missing_id"], "allow_nulls": False}
    ]

    with pytest.raises(
        ValidationError,
        match="unique-key fields must be declared",
    ):
        VectorSpatialDataContract.model_validate(payload)


def test_rejects_inconsistent_nullability() -> None:
    payload = valid_contract_payload()
    payload["required_fields"][0]["max_null_fraction"] = 0.25

    with pytest.raises(
        ValidationError,
        match=(
            "non-nullable fields must have "
            "max_null_fraction equal to zero"
        ),
    ):
        VectorSpatialDataContract.model_validate(payload)


def test_rejects_reversed_feature_bounds() -> None:
    payload = valid_contract_payload()
    payload["feature_count"] = {"minimum": 10, "maximum": 5}

    with pytest.raises(
        ValidationError,
        match="feature-count minimum cannot exceed maximum",
    ):
        VectorSpatialDataContract.model_validate(payload)


def test_rejects_reversed_extent() -> None:
    payload = valid_contract_payload()
    payload["permitted_extent"]["min_x"] = 200.0

    with pytest.raises(
        ValidationError,
        match="min_x cannot exceed max_x",
    ):
        VectorSpatialDataContract.model_validate(payload)


def test_rejects_unknown_contract_fields() -> None:
    payload = valid_contract_payload()
    payload["approval_granted"] = True

    with pytest.raises(
        ValidationError,
        match="Extra inputs are not permitted",
    ):
        VectorSpatialDataContract.model_validate(payload)
