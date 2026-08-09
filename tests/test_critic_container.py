"""Static security checks for the independent Critic container."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_compose() -> dict[str, Any]:
    """Load the repository Compose configuration."""

    path = PROJECT_ROOT / "compose.yaml"

    return yaml.safe_load(
        path.read_text(encoding="utf-8")
    )


def test_critic_is_an_independent_service() -> None:
    compose = load_compose()
    critic = compose["services"]["critic"]

    assert critic["image"]
    assert critic["command"] == [
        "agent-info",
        "critic",
    ]
    assert "agents" in critic["profiles"]


def test_critic_has_only_model_network() -> None:
    compose = load_compose()
    critic = compose["services"]["critic"]

    networks = critic["networks"]

    assert networks == ["model"]
    assert "backend" not in networks
    assert "control" not in networks


def test_critic_filesystem_is_read_only() -> None:
    compose = load_compose()
    critic = compose["services"]["critic"]

    assert critic["read_only"] is True
    assert critic["working_dir"] == "/workspace"

    volumes = critic["volumes"]

    assert (
        "./agents/critic:/app/agents/critic:ro"
        in volumes
    )
    assert (
        "./context:/workspace/context:ro"
        in volumes
    )
    assert (
        "./traces:/workspace/traces:ro"
        in volumes
    )
    assert (
        "./reports:/workspace/reports:ro"
        in volumes
    )

    assert all(
        volume.endswith(":ro")
        for volume in volumes
    )


def test_critic_has_no_database_secret() -> None:
    compose = load_compose()
    critic = compose["services"]["critic"]

    assert "secrets" not in critic

    environment = critic.get(
        "environment",
        {},
    )

    forbidden = {
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_PASSWORD_FILE",
        "DATABASE_URL",
        "ENABLE_WRITE_TOOLS",
        "ALLOW_OVERWRITE",
    }

    assert forbidden.isdisjoint(environment)


def test_critic_drops_linux_capabilities() -> None:
    compose = load_compose()
    critic = compose["services"]["critic"]

    assert critic["cap_drop"] == ["ALL"]
    assert (
        "no-new-privileges:true"
        in critic["security_opt"]
    )


def test_agent_image_uses_non_root_user() -> None:
    dockerfile = (
        PROJECT_ROOT
        / "docker"
        / "agent"
        / "Dockerfile"
    ).read_text(encoding="utf-8")

    assert "USER geoagent" in dockerfile
    assert (
        'ENTRYPOINT ["geoagent"]'
        in dockerfile
    )