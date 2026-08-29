from pathlib import Path

import pytest

from geoagent_harness.agent_manifest import load_agent_manifest

AGENTS_ROOT = Path(__file__).resolve().parents[1] / "agents"


@pytest.mark.parametrize(
    "role",
    ["planner", "executor", "critic", "builder"],
)
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
    assert all(
        tool not in executor.permissions.tools
        for tool in {
            "inspect_vector_dataset",
            "plan_load_vector_to_postgis",
            "load_vector_to_postgis",
            "convert_vector",
            "validate_postgis_layer",
        }
    )
    assert executor.permissions.tools == [
        "health_check",
        "run_approved_vector_postgis_workflow",
        "run_approved_recipe",
    ]
    assert (
        "convert_vector"
        not in executor.permissions.tools
    )
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
    builder = load_agent_manifest("builder", AGENTS_ROOT)

    assert builder.permissions.tools == []
    assert builder.permissions.arbitrary_shell is False
    assert builder.permissions.unrestricted_sql is False
    assert builder.permissions.filesystem_write is False
    assert builder.permissions.database_write is False
    assert builder.permissions.model_extra == {}

def test_builder_manifest_cannot_grant_tool_access(
    tmp_path: Path,
) -> None:
    builder_root = tmp_path / "builder"
    builder_root.mkdir(parents=True)

    (builder_root / "manifest.yaml").write_text(
        """
id: builder
model_ref: shared_ollama_runtime
purpose: Unsafe builder manifest.
permissions:
  tools:
    - run_approved_recipe
  arbitrary_shell: false
  unrestricted_sql: false
  filesystem_write: false
  database_write: false
instructions:
  - Return candidate proposals.
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="cannot grant execution authority",
    ):
        load_agent_manifest("builder", tmp_path)


def test_builder_manifest_cannot_add_permissions(
    tmp_path: Path,
) -> None:
    builder_root = tmp_path / "builder"
    builder_root.mkdir(parents=True)

    (builder_root / "manifest.yaml").write_text(
        """
id: builder
model_ref: shared_ollama_runtime
purpose: Unsafe builder manifest.
permissions:
  tools: []
  arbitrary_shell: false
  unrestricted_sql: false
  filesystem_write: false
  database_write: false
  trusted_source_write: true
instructions:
  - Return candidate proposals.
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="cannot declare additional permissions",
    ):
        load_agent_manifest("builder", tmp_path)
