"""Immutable existing request roots and trusted application service bindings."""
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

@dataclass(frozen=True)
class RequestContext:
    project_root: Path
    recipe_root: Path | None
    approval_root: Path | None
    task_root: Path | None
    services: ModuleType

# A route already emitted its original early response; do not emit another 200.
RESPONSE_SENT = object()
