"""Lazy typed views of one trusted environment/layout snapshot; no global cache."""
from __future__ import annotations
from collections.abc import Mapping
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
import os
from pathlib import Path
from types import MappingProxyType
from typing import Literal, TYPE_CHECKING

from geoagent_harness.platform.layout import LayoutConfiguration, ROOT_ENVIRONMENT

if TYPE_CHECKING:
    from geoagent_harness.platform.settings import MCPSettings
    from geoagent_harness.platform.model_settings import ModelSettings
    from geoagent_harness.platform.client_settings import MCPClientSettings
    from geoagent_harness.platform.replay_settings import SnakemakeReplaySettings

# Existing request overrides retain one identity through all compatibility imports.
selected_model: ContextVar[str | None] = ContextVar('selected_model', default=None)
selected_reasoning: ContextVar[str | None] = ContextVar('selected_reasoning', default=None)

SETTING_NAMES = frozenset(name for name, _ in ROOT_ENVIRONMENT.values()) | frozenset({
    'GEOAGENT_CONTAINER_IMAGE', 'ENABLE_WRITE_TOOLS', 'ALLOW_OVERWRITE',
    'ALLOWED_SCHEMAS', 'ALLOWED_GEOSERVER_WORKSPACES', 'ALLOWED_GEOSERVER_DATASTORES',
    'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD_FILE',
    'GEOSERVER_BASE_URL', 'GEOSERVER_USER', 'GEOSERVER_PASSWORD_FILE',
    'MODEL_BASE_URL', 'MODEL_NAME', 'MODEL_TIMEOUT_SECONDS', 'MODEL_MAX_TOKENS',
    'MODEL_REASONING_EFFORT', 'MODEL_RESPONSE_FORMAT',
    'GEOAGENT_MCP_URL', 'GEOAGENT_MCP_TIMEOUT_SECONDS',
})


@dataclass(frozen=True)
class PlatformConfiguration:
    layout: LayoutConfiguration
    _values: Mapping[str, str] = field(repr=False)
    _model_override: str | None = field(default=None, repr=False)
    _reasoning_override: str | None = field(default=None, repr=False)
    # A composition seam, not an implemented server profile or a model-selected mode.
    deployment_profile: Literal['personal'] = field(default='personal', init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, '_values', MappingProxyType({
            key: value for key, value in self._values.items() if key in SETTING_NAMES}))

    @property
    def tools(self) -> MCPSettings:
        from geoagent_harness.platform.settings import _parse_settings
        return _parse_settings(self._values, self.layout)

    @property
    def model(self) -> ModelSettings:
        from geoagent_harness.platform.model_settings import _parse_model_settings
        return _parse_model_settings(self._values, model_override=self._model_override,
                                     reasoning_override=self._reasoning_override)

    @property
    def mcp_client(self) -> MCPClientSettings:
        from geoagent_harness.platform.client_settings import _parse_mcp_client_settings
        return _parse_mcp_client_settings(self._values)

    @property
    def replay(self) -> SnakemakeReplaySettings:
        from geoagent_harness.platform.replay_settings import _parse_snakemake_replay_settings
        return _parse_snakemake_replay_settings(self.layout)


def load_configuration(environ: Mapping[str, str] | None = None, *,
                       layout: LayoutConfiguration | None = None,
                       project_root: Path | None = None) -> PlatformConfiguration:
    """Snapshot allowlisted values; never read .env, credentials or provider services.

    Explicit layout/project-root arguments are trusted composition inputs. Existing
    environment aliases and defaults remain valid. Explicit environment mappings
    ignore request overrides, exactly as the historical model loader did.
    """
    source = os.environ if environ is None else environ
    values = MappingProxyType({key: source[key] for key in SETTING_NAMES if key in source})
    active_layout = layout if layout is not None else LayoutConfiguration.from_environment(values)
    if project_root is not None:
        active_layout = replace(active_layout, project_root=Path(project_root))
    return PlatformConfiguration(active_layout, values,
        selected_model.get() if environ is None else None,
        selected_reasoning.get() if environ is None else None)
