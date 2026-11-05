"""Compatibility facade for shared immutable rollback verification evidence."""
from pathlib import Path
from geoagent_harness.postgis.artifact_storage import ArtifactStore
from .schemas import PostGISRollbackVerificationResult

FILE_NAME = 'VERIFICATION.json'
class PostGISRollbackVerificationStorageError(RuntimeError):
    pass

_STORE = ArtifactStore(PostGISRollbackVerificationResult, 'verification_id', 'postgis-rollback-verification',
                       FILE_NAME, 'rollback verification', PostGISRollbackVerificationStorageError, redact=False)


def canonical_postgis_rollback_verification_json(value):
    return _STORE.canonical(value)


def postgis_rollback_verification_sha256(value):
    return _STORE.digest(value)


def persist_postgis_rollback_verification(value, *, verification_root: Path):
    path, digest, value = _STORE.persist(value, verification_root)
    return path


def load_postgis_rollback_verification(path: Path, *, verification_root: Path):
    return _STORE.load(path, verification_root)
