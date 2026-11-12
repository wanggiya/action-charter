"""Regression tests for package import boundaries."""

from __future__ import annotations

import subprocess
import sys


def test_mcp_client_imports_in_clean_process() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                'from geoagent_harness.platform.internal_mcp.client import MCPReadOnlyClient\nfrom geoagent_harness.platform.internal_mcp.executor import MCPExecutorClient'
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr


def test_executor_service_imports_in_clean_process() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                'from geoagent_harness.agents.roles.executor.service import execute_approved_plan'
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    
def test_executor_schema_import_does_not_load_gis_stack() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; from geoagent_harness.agents.roles.executor.schemas import ExecutorRecipeRunResult; assert 'geopandas' not in sys.modules; assert 'pyogrio' not in sys.modules"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr

def test_executor_schema_import_does_not_load_raster_stack(
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; from geoagent_harness.agents.roles.executor.schemas import ExecutorRecipeRunResult; assert 'rasterio' not in sys.modules"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr

def test_skill_adapter_package_does_not_load_rasterio(
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import geoagent_harness.data.spatial.adapters; assert 'rasterio' not in sys.modules"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
