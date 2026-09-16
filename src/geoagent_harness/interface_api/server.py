"""Small fail-closed HTTP boundary for non-mutating interface operations."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from geoagent_harness.recipe_catalog import (
    RecipeTemplateCatalogError,
    load_recipe_template_catalog,
)
from geoagent_harness.recipe_proposals import (
    RecipeCompilationError,
    RecipeProposal,
    compile_recipe_proposal,
)
from geoagent_harness.skill_registry import (
    SkillRegistryError,
    load_skill_registry,
)


MAX_INTERFACE_REQUEST_BYTES = 65_536
LOOPBACK_HOST = "127.0.0.1"


class InterfaceApiError(RuntimeError):
    """Raised when the bounded interface API cannot fulfill a request."""


def _trusted_root(project_root: Path) -> Path:
    try:
        resolved = project_root.resolve(strict=True)
    except OSError as exc:
        raise InterfaceApiError("trusted project root is unavailable") from exc
    if not resolved.is_dir():
        raise InterfaceApiError("trusted project root must be a directory")
    return resolved


def interface_recipe_template_catalog(project_root: Path) -> dict[str, Any]:
    """Return the same validated non-executing catalog projection as the CLI."""

    catalog = load_recipe_template_catalog(_trusted_root(project_root))
    return {
        "schema_version": catalog.schema_version,
        "templates": [template.model_dump(mode="json") for template in catalog.templates],
        "catalog_validated": True,
        "files_modified": False,
        "execution_performed": False,
    }


def compile_interface_recipe_proposal(
    payload: object,
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Validate and compile one proposal without persistence or execution."""

    proposal = RecipeProposal.model_validate(payload)
    root = _trusted_root(project_root)
    result = compile_recipe_proposal(
        proposal,
        registry=load_skill_registry(root),
    )
    if result.recipe_saved or result.approval_performed or result.execution_performed:
        raise InterfaceApiError("compiler crossed the non-mutating interface boundary")
    return {
        "schema_version": "1.0",
        "status": "compiled",
        "result": result.model_dump(mode="json"),
        "files_modified": False,
        "approval_performed": False,
        "execution_performed": False,
    }


def _handler(project_root: Path) -> type[BaseHTTPRequestHandler]:
    class InterfaceRequestHandler(BaseHTTPRequestHandler):
        server_version = "ActionCharterInterface/1.0"
        sys_version = ""

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _send(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'")
            self.end_headers()
            self.wfile.write(body)

        def _reject_origin(self) -> bool:
            origin = self.headers.get("Origin")
            if origin is None or origin in {
                "http://127.0.0.1:5173",
                "http://localhost:5173",
            }:
                return False
            self._send(HTTPStatus.FORBIDDEN, {"error": "request origin is not allowed"})
            return True

        def do_GET(self) -> None:  # noqa: N802
            if self._reject_origin():
                return
            if self.path == "/api/v1/health":
                self._send(HTTPStatus.OK, {
                    "schema_version": "1.0",
                    "status": "ready",
                    "bound_to_loopback": True,
                    "write_authority": False,
                    "execution_authority": False,
                })
                return
            if self.path == "/api/v1/recipe-templates":
                try:
                    self._send(HTTPStatus.OK, interface_recipe_template_catalog(project_root))
                except (InterfaceApiError, RecipeTemplateCatalogError):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "trusted template catalog is unavailable"})
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "endpoint is not available"})

        def do_POST(self) -> None:  # noqa: N802
            if self._reject_origin():
                return
            if self.path != "/api/v1/recipe-proposals/compile":
                self._send(HTTPStatus.NOT_FOUND, {"error": "endpoint is not available"})
                return
            if self.headers.get_content_type() != "application/json":
                self._send(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "application/json is required"})
                return
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                length = -1
            if length < 1 or length > MAX_INTERFACE_REQUEST_BYTES:
                self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request body size is invalid"})
                return
            try:
                payload = json.loads(self.rfile.read(length))
                response = compile_interface_recipe_proposal(payload, project_root=project_root)
            except (json.JSONDecodeError, ValidationError):
                self._send(HTTPStatus.BAD_REQUEST, {"error": "recipe proposal is invalid"})
                return
            except RecipeCompilationError:
                self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "recipe proposal could not be compiled"})
                return
            except (InterfaceApiError, SkillRegistryError, OSError, ValueError):
                self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "trusted compilation service is unavailable"})
                return
            self._send(HTTPStatus.OK, response)

    return InterfaceRequestHandler


def serve_interface_api(
    *,
    project_root: Path,
    host: str = LOOPBACK_HOST,
    port: int = 8765,
    server_factory: Callable[..., ThreadingHTTPServer] = ThreadingHTTPServer,
) -> None:
    """Serve the non-mutating API and refuse non-loopback binding."""

    if host != LOOPBACK_HOST:
        raise InterfaceApiError("interface API must bind to 127.0.0.1")
    if port < 1 or port > 65_535:
        raise InterfaceApiError("interface API port is invalid")
    root = _trusted_root(project_root)
    server = server_factory((host, port), _handler(root))
    try:
        server.serve_forever()
    finally:
        server.server_close()
