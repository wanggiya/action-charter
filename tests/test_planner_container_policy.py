"""Verify the planner container's static security boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_compose() -> dict[str, Any]:
    return yaml.safe_load(
        (
            PROJECT_ROOT / "compose.yaml"
        ).read_text(encoding="utf-8")
    )


def test_planner_has_only_model_network() -> None:
    planner = load_compose()["services"]["planner"]

    assert planner["networks"] == ["model"]


def test_planner_has_no_database_configuration() -> None:
    planner = load_compose()["services"]["planner"]
    environment = planner.get("environment", {})

    assert all(
        not str(key).startswith("POSTGRES_")
        for key in environment
    )

    assert "secrets" not in planner


def test_planner_mounts_are_read_only() -> None:
    planner = load_compose()["services"]["planner"]
    volumes = planner.get("volumes", [])

    assert volumes
    assert all(
        str(volume).endswith(":ro")
        for volume in volumes
    )

    serialized = "\n".join(
        str(volume)
        for volume in volumes
    ).lower()

    assert "data/input" not in serialized
    assert "data/output" not in serialized
    assert "reports" not in serialized
    assert "traces" not in serialized
    assert "postgis" not in serialized
    assert "docker.sock" not in serialized


def test_planner_runtime_is_hardened() -> None:
    planner = load_compose()["services"]["planner"]

    assert planner["read_only"] is True
    assert planner["cap_drop"] == ["ALL"]
    assert "no-new-privileges:true" in (
        planner["security_opt"]
    )


def test_planner_runs_plan_command() -> None:
    planner = load_compose()["services"]["planner"]
    command = planner["command"]

    assert command[0] == "plan-task"
    assert "--request" in command
    assert "--project-root" in command
    assert "--agents-root" in command