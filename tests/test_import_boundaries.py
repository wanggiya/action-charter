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
                "from geoagent_harness.mcp_client "
                "import MCPReadOnlyClient, "
                "MCPExecutorClient"
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
                "from geoagent_harness.executor.service "
                "import execute_approved_plan"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr