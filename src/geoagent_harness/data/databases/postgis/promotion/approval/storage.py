"""Compatibility facade for shared immutable promotion approval evidence."""
from pathlib import Path
from geoagent_harness.data.databases.postgis.artifact_storage import ArtifactStore
from geoagent_harness.data.databases.postgis.promotion.approval.schemas import PostGISPromotionApproval, PostGISPromotionApprovalStorageResult

APPROVAL_FILE_NAME = 'APPROVAL.json'
class PostGISPromotionApprovalStorageError(RuntimeError):
    pass

_STORE = ArtifactStore(PostGISPromotionApproval, 'approval_id', 'postgis-promotion-approval',
                       APPROVAL_FILE_NAME, 'promotion approval', PostGISPromotionApprovalStorageError, redact=True)


def canonical_postgis_promotion_approval_json(approval):
    return _STORE.canonical(approval)


def postgis_promotion_approval_sha256(approval):
    return _STORE.digest(approval)


def persist_postgis_promotion_approval(approval, *, approval_root: Path):
    path, digest, approval = _STORE.persist(approval, approval_root)
    return PostGISPromotionApprovalStorageResult(
        approval_id=approval.approval_id, plan_id=approval.plan_id, plan_sha256=approval.plan_sha256,
        approval_sha256=digest, approval_directory=path.parent.as_posix(), approval_file=path.as_posix(),
        decision=approval.decision, approved_step_ids=approval.approved_step_ids)


def load_postgis_promotion_approval(approval_file: Path, *, approval_root: Path):
    return _STORE.load(approval_file, approval_root)
