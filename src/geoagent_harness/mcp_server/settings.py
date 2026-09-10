"""Fail-closed configuration for the MCP and skill boundaries."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off", ""})


def parse_flag(value: str | None, *, default: bool = False) -> bool:
    """Parse a Boolean without enabling access for an unknown value."""
    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in _TRUE_VALUES:
        return True

    if normalized in _FALSE_VALUES:
        return False

    return False


def validate_identifier(value: str, *, label: str) -> str:
    """Validate a conservative PostgreSQL identifier."""
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(
            f"{label} must match {_IDENTIFIER.pattern!r}; "
            f"received {value!r}"
        )

    return value


class MCPSettings(BaseModel):
    """Non-secret configuration available to controlled tools."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input_root: Path
    output_root: Path
    contract_root: Path = Path("spatial-contracts")
    trace_root: Path = Path("traces")
    report_root: Path = Path("reports")
    plan_root: Path = Path("plans")
    approval_root: Path = Path("approvals")
    state_root: Path = Path("workflow-state")
    container_image: str = "geoagent-gis-tools:local"

    enable_write_tools: bool = False
    allow_overwrite: bool = False

    allowed_schemas: frozenset[str] = Field(
        default_factory=lambda: frozenset({"agent_sandbox"})
    )
    allowed_geoserver_workspaces: frozenset[str] = Field(
        default_factory=lambda: frozenset({"agent_sandbox"})
    )
    allowed_geoserver_datastores: frozenset[str] = Field(
        default_factory=lambda: frozenset({"postgis"})
    )
    

    postgres_host: str = "postgis"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_database: str = "postgres"
    postgres_user: str = "geoagent"

    # The password itself is never stored in settings.
    postgres_password_file: Path = Path(
        "/run/secrets/postgis_password"
    )
    geoserver_base_url: str = "http://geoserver:8080/geoserver"
    geoserver_user: str = "geoagent"
    geoserver_password_file: Path = Path(
        "/run/secrets/geoserver_password"
    )
    
    project_root: Path = Path(".")
    recipe_root: Path = Path("workflow-recipes")
    recipe_run_root: Path = Path(
        "recipe-runs"
    )
    recipe_evidence_root: Path = Path(
        "recipe-evidence"
    )

    @field_validator("allowed_schemas")
    @classmethod
    def schemas_are_safe(
        cls,
        value: frozenset[str],
    ) -> frozenset[str]:
        if not value:
            raise ValueError("at least one allowed schema is required")

        for schema in value:
            validate_identifier(schema, label="schema")

        return value

    @field_validator("allowed_geoserver_workspaces", "allowed_geoserver_datastores")
    @classmethod
    def geoserver_names_are_safe(cls, value: frozenset[str]) -> frozenset[str]:
        if not value:
            raise ValueError("at least one allowed GeoServer name is required")
        for name in value:
            validate_identifier(name, label="GeoServer name")
        return value

    @field_validator("geoserver_base_url")
    @classmethod
    def geoserver_url_is_bounded(cls, value: str) -> str:
        from urllib.parse import urlsplit
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("geoserver_base_url must be an HTTP(S) URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("geoserver_base_url cannot contain credentials, query, or fragment")
        if parsed.path.rstrip("/") not in {"", "/geoserver"}:
            raise ValueError("geoserver_base_url path must be empty or /geoserver")
        return value.rstrip("/")

    @field_validator("postgres_database")
    @classmethod
    def database_name_is_safe(cls, value: str) -> str:
        return validate_identifier(
            value,
            label="postgres_database",
        )

    @field_validator("postgres_user")
    @classmethod
    def database_user_is_safe(cls, value: str) -> str:
        return validate_identifier(
            value,
            label="postgres_user",
        )


def load_settings(
    environ: Mapping[str, str] | None = None,
) -> MCPSettings:
    """Load non-secret settings from a trusted environment."""
    source = os.environ if environ is None else environ

    raw_schemas = source.get(
        "ALLOWED_SCHEMAS",
        "agent_sandbox",
    )

    schemas = frozenset(
        item.strip()
        for item in raw_schemas.split(",")
        if item.strip()
    )
    geoserver_workspaces = frozenset(item.strip() for item in source.get(
        "ALLOWED_GEOSERVER_WORKSPACES", "agent_sandbox"
    ).split(",") if item.strip())
    geoserver_datastores = frozenset(item.strip() for item in source.get(
        "ALLOWED_GEOSERVER_DATASTORES", "postgis"
    ).split(",") if item.strip())
    

    return MCPSettings(
        input_root=Path(
            source.get(
                "GEOAGENT_INPUT_ROOT",
                "data/input",
            )
        ),
        output_root=Path(
            source.get(
                "GEOAGENT_OUTPUT_ROOT",
                "data/output",
            )
        ),
        contract_root=Path(
            source.get(
                "GEOAGENT_SPATIAL_CONTRACT_ROOT",
                "spatial-contracts",
            )
        ),
        trace_root=Path(
            source.get(
                "GEOAGENT_TRACE_ROOT",
                "traces",
            )
        ),
        report_root=Path(
            source.get(
                "GEOAGENT_REPORT_ROOT",
                "reports",
            )
        ),
        plan_root=Path(
            source.get(
                "GEOAGENT_PLAN_ROOT",
                "plans",
            )
        ),
        approval_root=Path(
            source.get(
                "GEOAGENT_APPROVAL_ROOT",
                "approvals",
            )
        ),
        state_root=Path(
            source.get(
                "GEOAGENT_STATE_ROOT",
                "workflow-state",
            )
        ),
        container_image=source.get(
            "GEOAGENT_CONTAINER_IMAGE",
            "geoagent-gis-tools:local",
        ),
        enable_write_tools=parse_flag(
            source.get("ENABLE_WRITE_TOOLS"),
            default=False,
        ),
        allow_overwrite=parse_flag(
            source.get("ALLOW_OVERWRITE"),
            default=False,
        ),
        allowed_schemas=schemas,
        allowed_geoserver_workspaces=geoserver_workspaces,
        allowed_geoserver_datastores=geoserver_datastores,
        postgres_host=source.get(
            "POSTGRES_HOST",
            "postgis",
        ),
        postgres_port=int(
            source.get(
                "POSTGRES_PORT",
                "5432",
            )
        ),
        postgres_database=source.get(
            "POSTGRES_DB",
            "postgres",
        ),
        postgres_user=source.get(
            "POSTGRES_USER",
            "geoagent",
        ),
        postgres_password_file=Path(
            source.get(
                "POSTGRES_PASSWORD_FILE",
                "/run/secrets/postgis_password",
            )
        ),
        geoserver_base_url=source.get(
            "GEOSERVER_BASE_URL", "http://geoserver:8080/geoserver"
        ),
        geoserver_user=source.get("GEOSERVER_USER", "geoagent"),
        geoserver_password_file=Path(source.get(
            "GEOSERVER_PASSWORD_FILE", "/run/secrets/geoserver_password"
        )),
        project_root=Path(
            source.get(
                "GEOAGENT_PROJECT_ROOT",
                ".",
            )
        ),
        recipe_root=Path(
            source.get(
                "GEOAGENT_RECIPE_ROOT",
                "workflow-recipes",
            )
        ),
        recipe_run_root=Path(
            source.get(
                "GEOAGENT_RECIPE_RUN_ROOT",
                "recipe-runs",
            )
        ),
        recipe_evidence_root=Path(
            source.get(
                "GEOAGENT_RECIPE_EVIDENCE_ROOT",
                "recipe-evidence",
            )
        ),
    )
