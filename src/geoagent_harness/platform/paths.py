"""Translate shared workspace path errors at the API/service boundary."""
from geoagent_harness.platform.workspace import runtime_store_path as _store, ensure_state_root as _ensure, runtime_reference_path as _reference, WorkspaceError


def runtime_store_path(root, store, *parts):
    try:
        return _store(root, store, *parts)
    except WorkspaceError as error:
        from geoagent_harness.contracts.errors import InterfaceApiError
        raise InterfaceApiError(f'Workspace storage is unsafe or requires migration: {error}') from error


def ensure_state_root(root):
    try:
        _ensure(root)
    except WorkspaceError as error:
        from geoagent_harness.contracts.errors import InterfaceApiError
        raise InterfaceApiError(f'Workspace storage is unsafe: {error}') from error


def runtime_reference_path(root, reference):
    try: return _reference(root, reference)
    except WorkspaceError as error:
        from geoagent_harness.contracts.errors import InterfaceApiError
        raise InterfaceApiError(f'Workspace storage is unsafe: {error}') from error
