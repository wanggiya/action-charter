"""Integration contracts for the spatial-data assessment skill."""

from __future__ import annotations

import asyncio
from pathlib import Path

from geoagent_harness.mcp_client import READ_ONLY_TOOL_ALLOWLIST
from geoagent_harness.mcp_server.server import mcp
from geoagent_harness.mcp_server.settings import MCPSettings, load_settings
from geoagent_harness.mcp_server.tools import (
    TOOL_ALLOWLIST,
    assess_spatial_data_contract,
)
from geoagent_harness.skill_registry import load_skill_registry


PROJECT_ROOT = Path(__file__).parents[1]
BENCHMARK_ROOT = (
    PROJECT_ROOT / "benchmarks" / "spatial-contracts" / "vector"
)


def test_skill_is_registered_as_read_only_validation() -> None:
    skill = load_skill_registry(PROJECT_ROOT).get_skill(
        "assess_spatial_data_contract"
    )

    assert skill.version == "0.1.0"
    assert skill.status.value == "implemented"
    assert skill.kind.value == "validation"
    assert skill.access.value == "read_only"
    assert skill.approval_required is False
    assert skill.validation_required is False
    assert skill.verifier is None


def test_contract_root_loads_from_trusted_environment() -> None:
    settings = load_settings(
        {
            "GEOAGENT_INPUT_ROOT": "/approved/input",
            "GEOAGENT_OUTPUT_ROOT": "/approved/output",
            "GEOAGENT_SPATIAL_CONTRACT_ROOT": "/approved/contracts",
        }
    )

    assert settings.contract_root == Path("/approved/contracts")


def test_read_only_allowlists_include_contract_assessment() -> None:
    assert "assess_spatial_data_contract" in TOOL_ALLOWLIST
    assert "assess_spatial_data_contract" in READ_ONLY_TOOL_ALLOWLIST

    registered = {
        tool.name
        for tool in asyncio.run(mcp.list_tools())
    }
    assert "assess_spatial_data_contract" in registered


def test_mcp_tool_assesses_clean_benchmark() -> None:
    settings = MCPSettings(
        input_root=BENCHMARK_ROOT / "data",
        output_root=PROJECT_ROOT / "data" / "output",
        contract_root=BENCHMARK_ROOT,
    )

    result = assess_spatial_data_contract(
        path="clean.geojson",
        contract_file="contract.yaml",
        settings=settings,
    )

    assert result.status == "assessed"
    assert result.result.passed is True
    assert result.result.filesystem_modified is False
    assert result.result.database_modified is False
    assert result.result.execution_performed is False
