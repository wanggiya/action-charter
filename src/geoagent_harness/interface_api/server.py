"""Small fail-closed HTTP boundary for non-mutating interface operations."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import re
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
from geoagent_harness.recipes import (
    RecipePolicyError,
    RecipeStorageError,
    load_recipe,
    recipe_sha256,
    save_recipe,
    validate_recipe_policy,
)


MAX_INTERFACE_REQUEST_BYTES = 65_536
MAX_INTERFACE_RECIPES = 200
SAFE_RECIPE_FILENAME = re.compile(
    r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$"
)
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
        "recipe_sha256": recipe_sha256(result.recipe),
        "files_modified": False,
        "approval_performed": False,
        "execution_performed": False,
    }


def save_interface_reviewed_recipe(
    payload: object,
    *,
    confirmed_recipe_sha256: str,
    project_root: Path,
    recipe_root: Path | None = None,
) -> dict[str, Any]:
    """Recompile, verify the reviewed digest, and immutably save one recipe."""

    if not isinstance(confirmed_recipe_sha256, str) or len(confirmed_recipe_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in confirmed_recipe_sha256
    ):
        raise InterfaceApiError("confirmed recipe digest is invalid")
    proposal = RecipeProposal.model_validate(payload)
    root = _trusted_root(project_root)
    compiled = compile_recipe_proposal(
        proposal,
        registry=load_skill_registry(root),
    )
    digest = recipe_sha256(compiled.recipe)
    if digest != confirmed_recipe_sha256:
        raise InterfaceApiError("reviewed recipe digest no longer matches")
    destination = recipe_root if recipe_root is not None else root / "workflow-recipes"
    if destination.is_symlink():
        raise InterfaceApiError("recipe root cannot be a symlink")
    saved, path = save_recipe(compiled.recipe, recipe_root=destination)
    return {
        "schema_version": "1.0",
        "status": "stored",
        "recipe_id": saved.recipe_id,
        "recipe_sha256": recipe_sha256(saved),
        "recipe_filename": path.name,
        "recipe_saved": True,
        "approval_performed": False,
        "execution_performed": False,
    }


def interface_saved_recipe_inventory(
    *,
    project_root: Path,
    recipe_root: Path | None = None,
) -> dict[str, Any]:
    """Return bounded safe summaries of immutable stored recipes."""

    root = _trusted_root(project_root)
    destination = recipe_root if recipe_root is not None else root / "workflow-recipes"
    if destination.is_symlink():
        raise InterfaceApiError("recipe root cannot be a symlink")
    if not destination.exists():
        recipes: list[dict[str, Any]] = []
    else:
        paths = sorted(destination.glob("*.json"), key=lambda path: path.name)
        if len(paths) > MAX_INTERFACE_RECIPES:
            raise InterfaceApiError("recipe inventory exceeds its limit")
        registry = load_skill_registry(root)
        recipes = []
        for path in paths:
            if path.is_symlink() or path.resolve().parent != destination.resolve():
                raise InterfaceApiError("recipe inventory contains an unsafe artifact")
            recipe = load_recipe(path, recipe_root=destination)
            policy = validate_recipe_policy(recipe, registry=registry)
            recipes.append({
                "recipe_id": recipe.recipe_id,
                "recipe_sha256": recipe_sha256(recipe),
                "recipe_filename": path.name,
                "steps": [
                    {"step_id": step.step_id, "skill_id": step.skill_id}
                    for step in recipe.steps
                ],
                "approval_required_step_ids": policy.approval_required_step_ids,
                "validation_required_step_ids": policy.validation_required_step_ids,
            })
    return {
        "schema_version": "1.0",
        "status": "inspected",
        "recipes": recipes,
        "recipe_count": len(recipes),
        "inventory_performed": True,
        "recipe_modified": False,
        "approval_performed": False,
        "execution_performed": False,
    }


def prepare_interface_recipe_approval(
    *,
    recipe_filename: str,
    confirmed_recipe_sha256: str,
    project_root: Path,
    recipe_root: Path | None = None,
) -> dict[str, Any]:
    """Prepare a digest-bound approval request without recording a decision."""

    if not isinstance(recipe_filename, str) or not SAFE_RECIPE_FILENAME.fullmatch(recipe_filename):
        raise InterfaceApiError("recipe filename is invalid")
    if not isinstance(confirmed_recipe_sha256, str) or not re.fullmatch(
        r"[a-f0-9]{64}", confirmed_recipe_sha256
    ):
        raise InterfaceApiError("confirmed recipe digest is invalid")
    root = _trusted_root(project_root)
    destination = recipe_root if recipe_root is not None else root / "workflow-recipes"
    if destination.is_symlink():
        raise InterfaceApiError("recipe root cannot be a symlink")
    recipe = load_recipe(destination / recipe_filename, recipe_root=destination)
    digest = recipe_sha256(recipe)
    if digest != confirmed_recipe_sha256:
        raise InterfaceApiError("stored recipe digest no longer matches")
    policy = validate_recipe_policy(recipe, registry=load_skill_registry(root))
    if not policy.approval_required_step_ids:
        raise InterfaceApiError("recipe has no approval-required steps")
    request = {
        "schema_version": "1.0",
        "status": "prepared_not_recorded",
        "recipe_id": recipe.recipe_id,
        "recipe_filename": recipe_filename,
        "recipe_sha256": digest,
        "steps": [
            {"step_id": step.step_id, "skill_id": step.skill_id}
            for step in recipe.steps
        ],
        "approval_required_step_ids": policy.approval_required_step_ids,
        "validation_required_step_ids": policy.validation_required_step_ids,
        "approval_recorded": False,
        "execution_performed": False,
    }
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"))
    return {
        **request,
        "approval_request_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def _handler(
    project_root: Path,
    recipe_root: Path | None = None,
) -> type[BaseHTTPRequestHandler]:
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
            if self.path == "/api/v1/recipes":
                try:
                    self._send(HTTPStatus.OK, interface_saved_recipe_inventory(
                        project_root=project_root,
                        recipe_root=recipe_root,
                    ))
                except (
                    InterfaceApiError,
                    RecipePolicyError,
                    RecipeStorageError,
                    SkillRegistryError,
                    OSError,
                    ValueError,
                ):
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "trusted recipe inventory is unavailable"})
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "endpoint is not available"})

        def do_POST(self) -> None:  # noqa: N802
            if self._reject_origin():
                return
            if self.path not in {
                "/api/v1/recipe-proposals/compile",
                "/api/v1/recipe-proposals/save-reviewed",
                "/api/v1/recipes/prepare-approval",
            }:
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
                if self.path == "/api/v1/recipe-proposals/compile":
                    response = compile_interface_recipe_proposal(payload, project_root=project_root)
                elif self.path == "/api/v1/recipe-proposals/save-reviewed":
                    if not isinstance(payload, dict) or set(payload) != {
                        "proposal",
                        "confirmed_recipe_sha256",
                        "action",
                    } or payload.get("action") != "save_reviewed_recipe":
                        raise InterfaceApiError("reviewed save request is invalid")
                    response = save_interface_reviewed_recipe(
                        payload["proposal"],
                        confirmed_recipe_sha256=payload["confirmed_recipe_sha256"],
                        project_root=project_root,
                        recipe_root=recipe_root,
                    )
                else:
                    if not isinstance(payload, dict) or set(payload) != {
                        "recipe_filename",
                        "confirmed_recipe_sha256",
                        "action",
                    } or payload.get("action") != "prepare_recipe_approval":
                        raise InterfaceApiError("approval preparation request is invalid")
                    response = prepare_interface_recipe_approval(
                        recipe_filename=payload["recipe_filename"],
                        confirmed_recipe_sha256=payload["confirmed_recipe_sha256"],
                        project_root=project_root,
                        recipe_root=recipe_root,
                    )
            except (json.JSONDecodeError, ValidationError):
                self._send(HTTPStatus.BAD_REQUEST, {"error": "recipe proposal is invalid"})
                return
            except RecipeCompilationError:
                self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "recipe proposal could not be compiled"})
                return
            except InterfaceApiError as exc:
                status = HTTPStatus.CONFLICT if "digest no longer matches" in str(exc) else HTTPStatus.BAD_REQUEST
                self._send(status, {"error": str(exc)})
                return
            except RecipeStorageError:
                self._send(HTTPStatus.CONFLICT, {"error": "reviewed recipe could not be stored immutably"})
                return
            except (SkillRegistryError, OSError, ValueError):
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
