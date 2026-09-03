"""Versioned deterministic spatial-data contracts."""

from geoagent_harness.spatial_contracts.schemas import (
    SpatialDataContractAssessment,
    SpatialDataContractCheck,
    SpatialExtentRule,
    VectorFeatureCountRule,
    VectorFieldContract,
    VectorFieldType,
    VectorGeometryQualityRule,
    VectorGeometryType,
    VectorSpatialDataContract,
    VectorUniqueKeyRule,
)
from geoagent_harness.spatial_contracts.service import (
    SpatialDataContractAssessmentError,
    assess_spatial_data_contract,
)
from geoagent_harness.spatial_contracts.storage import (
    MAX_SPATIAL_CONTRACT_BYTES,
    SpatialDataContractStorageError,
    canonical_spatial_data_contract_json,
    load_spatial_data_contract,
    spatial_data_contract_sha256,
)

__all__ = [
    "SpatialExtentRule",
    "SpatialDataContractAssessment",
    "SpatialDataContractAssessmentError",
    "SpatialDataContractCheck",
    "MAX_SPATIAL_CONTRACT_BYTES",
    "SpatialDataContractStorageError",
    "VectorFeatureCountRule",
    "VectorFieldContract",
    "VectorFieldType",
    "VectorGeometryQualityRule",
    "VectorGeometryType",
    "VectorSpatialDataContract",
    "VectorUniqueKeyRule",
    "assess_spatial_data_contract",
    "canonical_spatial_data_contract_json",
    "load_spatial_data_contract",
    "spatial_data_contract_sha256",
]
