"""Verify the Builder container's static security boundary."""

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


def builder_service() -> dict[str, Any]:
    return load_compose()["services"]["builder"]


def test_builder_uses_only_model_network() -> None:
    builder = builder_service()

    assert builder["networks"] == ["model"]
    assert builder["extra_hosts"] == [
        "host.docker.internal:host-gateway"
    ]


def test_builder_has_only_model_environment() -> None:
    builder = builder_service()
    environment = builder.get("environment", {})

    assert set(environment) == {
        "MODEL_PROVIDER",
        "MODEL_BASE_URL",
        "MODEL_NAME",
        "MODEL_TIMEOUT_SECONDS",
        "MODEL_MAX_TOKENS",
    }

    prohibited_prefixes = (
        "POSTGRES_",
        "GEOAGENT_MCP_",
        "GEOAGENT_OUTPUT_",
        "GEOAGENT_APPROVAL_",
        "GEOAGENT_TRACE_",
        "GEOAGENT_REPORT_",
    )

    assert all(
        not str(key).startswith(prohibited_prefixes)
        for key in environment
    )

    assert "secrets" not in builder


def test_builder_mounts_only_its_manifest() -> None:
    builder = builder_service()
    volumes = builder.get("volumes", [])

    assert volumes == [
        "./agents/builder:/app/agents/builder:ro",
        (
            "./builder-requests/example-adapter.json:"
            "/workspace/request/example-adapter.json:ro"
        ),
    ]

    serialized = "\n".join(volumes).lower()

    for prohibited in (
        "context",
        "src",
        "candidate",
        "data/input",
        "data/output",
        "reports",
        "traces",
        "plans",
        "approvals",
        "recipe",
        "postgis",
        "docker.sock",
        "/run/secrets",
    ):
        assert prohibited not in serialized


def test_builder_runtime_is_hardened() -> None:
    builder = builder_service()

    assert builder["read_only"] is True
    assert builder["cap_drop"] == ["ALL"]
    assert "no-new-privileges:true" in (
        builder["security_opt"]
    )
    assert builder["tmpfs"] == [
        "/tmp:size=64m,mode=1777"
    ]


def test_builder_runs_bounded_proposal_command() -> None:
    builder = builder_service()
    command = builder["command"]

    assert command[0] == "builder-propose"
    assert command == [
        "builder-propose",
        "--request-file",
        "/workspace/request/example-adapter.json",
        "--request-root",
        "/workspace/request",
        "--agents-root",
        "/app/agents",
        "--pretty",
    ]


def test_builder_has_no_candidate_workspace() -> None:
    builder = builder_service()

    serialized = str(builder).lower()

    assert "/candidate" not in serialized
    assert "skill-candidates" not in serialized
    assert "filesystem_write" not in serialized


