"""Compatibility facade for shared immutable promotion verification evidence."""
from pathlib import Path
from geoagent_harness.data.databases.postgis.artifact_storage import ArtifactStore
from geoagent_harness.data.databases.postgis.promotion.verification.schemas import PostGISPromotionVerificationResult

FILE_NAME = 'VERIFICATION.json'
class PostGISPromotionVerificationStorageError(RuntimeError):
    pass

_STORE = ArtifactStore(PostGISPromotionVerificationResult, 'verification_id', 'postgis-promotion-verification',
                       FILE_NAME, 'promotion verification', PostGISPromotionVerificationStorageError, redact=False)


def canonical_postgis_promotion_verification_json(value):
    return _STORE.canonical(value)


def postgis_promotion_verification_sha256(value):
    return _STORE.digest(value)


def persist_postgis_promotion_verification(value, *, verification_root: Path):
    path, digest, value = _STORE.persist(value, verification_root)
    return path


def load_postgis_promotion_verification(path: Path, *, verification_root: Path):
    return _STORE.load(path, verification_root)
