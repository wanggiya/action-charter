from pathlib import Path

import pytest

from geoagent_harness.agent_manifest import load_agent_manifest

AGENTS_ROOT = Path(__file__).resolve().parents[1] / "agents"


@pytest.mark.parametrize("role", ["planner", "executor", "critic"])
def test_agent_manifest_is_valid(role: str) -> None:
    manifest = load_agent_manifest(role, AGENTS_ROOT)

    assert manifest.id == role
    assert manifest.permissions.arbitrary_shell is False


def test_unknown_agent_role_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown agent role"):
        load_agent_manifest("../../untrusted", AGENTS_ROOT)


def test_only_executor_has_tool_access() -> None:
    planner = load_agent_manifest("planner", AGENTS_ROOT)
    executor = load_agent_manifest("executor", AGENTS_ROOT)
    critic = load_agent_manifest("critic", AGENTS_ROOT)

    assert planner.permissions.tools == []
    assert executor.permissions.tools == [
        "health_check",
        "run_approved_vector_postgis_workflow",
    ]
    assert (
        "load_vector_to_postgis"
        not in executor.permissions.tools
    )
    assert (
        "inspect_vector_dataset"
        not in executor.permissions.tools
    )
    assert (
        "plan_load_vector_to_postgis"
        not in executor.permissions.tools
    )
    assert critic.permissions.tools == []
