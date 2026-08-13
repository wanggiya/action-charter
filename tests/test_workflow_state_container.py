"""Tests for workflow-state container boundaries."""

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_compose() -> dict:
    return yaml.safe_load(
        (
            PROJECT_ROOT / "compose.yaml"
        ).read_text(encoding="utf-8")
    )


def test_executor_receives_state_read_only() -> None:
    compose = load_compose()
    executor = compose["services"]["executor"]

    environment = executor["environment"]

    assert environment["GEOAGENT_STATE_ROOT"] == (
        "/workspace/workflow-state"
    )

    volumes = executor["volumes"]

    assert (
        "./workflow-state:"
        "/workspace/workflow-state:ro"
    ) in volumes


def test_planner_and_critic_do_not_receive_state() -> None:
    compose = load_compose()

    for service_name in ("planner", "critic"):
        service = compose["services"][service_name]
        volumes = service.get("volumes", [])

        assert all(
            "workflow-state" not in volume
            for volume in volumes
        )