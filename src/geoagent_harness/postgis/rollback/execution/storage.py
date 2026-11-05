"""Compatibility facade for shared immutable rollback execution evidence."""
from pathlib import Path
from geoagent_harness.postgis.artifact_storage import ArtifactStore
from .schemas import PostGISRollbackExecutionResult, PostGISRollbackExecutionStorageResult

FILE_NAME = 'EXECUTION.json'
class PostGISRollbackExecutionStorageError(RuntimeError):
    pass

_STORE = ArtifactStore(PostGISRollbackExecutionResult, 'execution_id', 'postgis-rollback-execution',
                       FILE_NAME, 'rollback execution', PostGISRollbackExecutionStorageError, redact=False)


def canonical_postgis_rollback_execution_json(value):
    return _STORE.canonical(value)


def postgis_rollback_execution_sha256(value):
    return _STORE.digest(value)


def persist_postgis_rollback_execution(value, *, execution_root: Path):
    path, digest, value = _STORE.persist(value, execution_root)
    return PostGISRollbackExecutionStorageResult(
        execution_id=value.execution_id, rollback_plan_id=value.rollback_plan_id, rollback_plan_sha256=value.rollback_plan_sha256,
        approval_id=value.approval_id, approval_sha256=value.approval_sha256,
        execution_sha256=digest, execution_directory=path.parent.as_posix(), execution_file=path.as_posix())


def load_postgis_rollback_execution(path: Path, *, execution_root: Path):
    return _STORE.load(path, execution_root)
