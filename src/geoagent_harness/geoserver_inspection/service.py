"""Bounded, read-only inspection of one exact GeoServer publication target."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

import httpx

from geoagent_harness.geoserver_inspection.schemas import (
    GeoServerFeatureTypeFacts,
    GeoServerInspectionRequest,
    GeoServerInspectionResult,
    GeoServerLayerFacts,
)
from geoagent_harness.mcp_server.settings import MCPSettings, validate_identifier

MAX_RESPONSE_BYTES = 262_144


class GeoServerInspectionError(RuntimeError):
    """Raised when bounded inspection cannot complete safely."""


class GeoServerInspectionReader(Protocol):
    def read(self, path: str) -> dict[str, Any] | None: ...
    def close(self) -> None: ...


def _read_password(path: Path) -> str:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        raise GeoServerInspectionError(
            "GeoServer inspection authentication failed; credentials were redacted"
        ) from None
    if not value or len(value) > 4096:
        raise GeoServerInspectionError("GeoServer password file is empty or invalid")
    return value


class HttpGeoServerInspectionReader:
    """GET-only client for fixed GeoServer REST resources."""

    def __init__(self, settings: MCPSettings) -> None:
        self._client = httpx.Client(
            base_url=f"{settings.geoserver_base_url}/rest/",
            auth=(settings.geoserver_user, _read_password(settings.geoserver_password_file)),
            timeout=5.0,
            follow_redirects=False,
            headers={"Accept": "application/json"},
        )

    def read(self, path: str) -> dict[str, Any] | None:
        try:
            response = self._client.get(path)
        except httpx.HTTPError:
            raise GeoServerInspectionError(
                "GeoServer inspection request failed; endpoint details were redacted"
            ) from None
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise GeoServerInspectionError(
                f"GeoServer inspection failed with HTTP status {response.status_code}"
            )
        if len(response.content) > MAX_RESPONSE_BYTES:
            raise GeoServerInspectionError("GeoServer response exceeds the inspection bound")
        try:
            payload = response.json()
        except ValueError:
            raise GeoServerInspectionError("GeoServer returned invalid JSON") from None
        if not isinstance(payload, dict):
            raise GeoServerInspectionError("GeoServer returned an invalid response object")
        return payload

    def close(self) -> None:
        self._client.close()


def _object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise GeoServerInspectionError(f"GeoServer response is missing bounded {key} facts")
    return value


def inspect_geoserver_layer(
    *, request: GeoServerInspectionRequest, settings: MCPSettings,
    reader: GeoServerInspectionReader | None = None,
) -> GeoServerInspectionResult:
    """Inspect exact allowlisted workspace/datastore/layer resources using GET only."""
    for label, value in (("workspace", request.workspace), ("datastore", request.datastore), ("layer", request.layer)):
        validate_identifier(value, label=label)
    if request.workspace not in settings.allowed_geoserver_workspaces:
        raise GeoServerInspectionError(f"GeoServer workspace {request.workspace!r} is not allowed")
    if request.datastore not in settings.allowed_geoserver_datastores:
        raise GeoServerInspectionError(f"GeoServer datastore {request.datastore!r} is not allowed")

    active = reader or HttpGeoServerInspectionReader(settings)
    owns_reader = reader is None
    prefix = f"workspaces/{request.workspace}"
    try:
        workspace = active.read(f"{prefix}.json")
        if workspace is None:
            return GeoServerInspectionResult(status="not_found", workspace=request.workspace, datastore=request.datastore, layer=request.layer, workspace_exists=False, datastore_exists=False, warnings=["Workspace does not exist."])
        if str(_object(workspace, "workspace").get("name", "")) != request.workspace:
            raise GeoServerInspectionError("GeoServer workspace identity does not match the request")
        datastore = active.read(f"{prefix}/datastores/{request.datastore}.json")
        if datastore is None:
            return GeoServerInspectionResult(status="not_found", workspace=request.workspace, datastore=request.datastore, layer=request.layer, workspace_exists=True, datastore_exists=False, warnings=["Datastore does not exist."])
        if str(_object(datastore, "dataStore").get("name", "")) != request.datastore:
            raise GeoServerInspectionError("GeoServer datastore identity does not match the request")
        feature_payload = active.read(f"{prefix}/datastores/{request.datastore}/featuretypes/{request.layer}.json")
        layer_payload = active.read(f"{prefix}/layers/{request.layer}.json")
        feature = None
        if feature_payload is not None:
            raw = _object(feature_payload, "featureType")
            if str(raw.get("name", "")) != request.layer:
                raise GeoServerInspectionError("GeoServer feature-type identity does not match the request")
            feature = GeoServerFeatureTypeFacts(name=str(raw.get("name", "")), native_name=str(raw.get("nativeName", "")), enabled=bool(raw.get("enabled", False)), advertised=bool(raw.get("advertised", False)), srs=str(raw["srs"]) if raw.get("srs") else None)
        published = None
        if layer_payload is not None:
            raw = _object(layer_payload, "layer")
            if str(raw.get("name", "")) not in {request.layer, f"{request.workspace}:{request.layer}"}:
                raise GeoServerInspectionError("GeoServer layer identity does not match the request")
            style = raw.get("defaultStyle") or {}
            published = GeoServerLayerFacts(name=str(raw.get("name", "")), enabled=bool(raw.get("enabled", False)), advertised=bool(raw.get("advertised", False)), default_style=str(style["name"]) if isinstance(style, dict) and style.get("name") else None)
        exists = feature is not None or published is not None
        return GeoServerInspectionResult(status="inspected" if exists else "not_found", workspace=request.workspace, datastore=request.datastore, layer=request.layer, workspace_exists=True, datastore_exists=True, feature_type=feature, published_layer=published, warnings=[] if exists else ["Feature type and published layer do not exist."])
    except httpx.HTTPError:
        raise GeoServerInspectionError("GeoServer inspection failed; details were redacted") from None
    finally:
        if owns_reader:
            active.close()
