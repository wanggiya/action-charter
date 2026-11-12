"""Compatibility facade for shared immutable rollback approval evidence."""
from pathlib import Path
from geoagent_harness.data.databases.postgis.artifact_storage import ArtifactStore
from geoagent_harness.data.databases.postgis.rollback.approval.schemas import PostGISRollbackApproval, PostGISRollbackApprovalStorageResult

FILE_NAME = 'APPROVAL.json'
class PostGISRollbackApprovalStorageError(RuntimeError):
    pass

_STORE = ArtifactStore(PostGISRollbackApproval, 'approval_id', 'postgis-rollback-approval',
                       FILE_NAME, 'rollback approval', PostGISRollbackApprovalStorageError, redact=True)


def canonical_postgis_rollback_approval_json(value):
    return _STORE.canonical(value)


def postgis_rollback_approval_sha256(value):
    return _STORE.digest(value)


def persist_postgis_rollback_approval(value, *, approval_root: Path):
    path, digest, value = _STORE.persist(value, approval_root)
    return PostGISRollbackApprovalStorageResult(
        approval_id=value.approval_id, rollback_plan_id=value.rollback_plan_id, rollback_plan_sha256=value.rollback_plan_sha256,
        approval_sha256=digest, approval_directory=path.parent.as_posix(), approval_file=path.as_posix(),
        decision=value.decision, approved_step_ids=value.approved_step_ids)


def load_postgis_rollback_approval(path: Path, *, approval_root: Path):
    return _STORE.load(path, approval_root)
