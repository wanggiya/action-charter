"""Single backend selection point; currently local SQLite plus existing JSON files."""
from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Callable

from geoagent_harness.platform.workspace import runtime_store_path, WorkspaceError
from geoagent_harness.platform.storage.contracts import RepositoryError, WorkspaceRepositories
from geoagent_harness.platform.storage.files import FileJsonRecords, FilePlans
from geoagent_harness.platform.storage.sqlite import connection, SQLiteTransaction


class LocalRepositories:
    def __init__(self, project_root):
        self.project_root = Path(project_root).resolve(strict=True)

    @contextmanager
    def transaction(self, *, write=False):
        with connection(self.project_root, write=write) as db:
            yield SQLiteTransaction(db, write=write) if db is not None else None

    def _directory(self, store, *parts):
        try:
            return runtime_store_path(self.project_root, store, *parts)
        except WorkspaceError as error:
            raise RepositoryError(f'Workspace storage is unsafe or requires migration: {error}') from error

    def runs(self, *, directory=None):
        return FileJsonRecords(directory if directory is not None else self._directory('workflow-state', 'interface-runs'), max_bytes=512_000)

    def documents(self, store, *, directory=None):
        if store not in {'plans', 'planner-conversations'}:
            raise RepositoryError('Unknown document store')
        path = directory if directory is not None else self._directory(store)
        return FilePlans(path) if store == 'plans' else FileJsonRecords(path, max_bytes=2_000_000)


_provider: ContextVar[Callable[[Path], WorkspaceRepositories]] = ContextVar('workspace_repository_provider', default=LocalRepositories)


def repositories(project_root: Path) -> WorkspaceRepositories:
    """Resolve an adapter per operation; no global root/connection cache or user code loading."""
    return _provider.get()(Path(project_root).resolve(strict=True))


@contextmanager
def using_repository_provider(provider: Callable[[Path], WorkspaceRepositories]):
    """Application composition/test hook; not a model tool or a user-supplied entrypoint."""
    token = _provider.set(provider)
    try: yield
    finally: _provider.reset(token)
