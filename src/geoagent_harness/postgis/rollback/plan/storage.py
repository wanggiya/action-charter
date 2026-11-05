"""Compatibility facade for shared immutable rollback plans."""
from pathlib import Path
from geoagent_harness.postgis.artifact_storage import ArtifactStore
from .schemas import PostGISRollbackPlan, PostGISRollbackPlanStorageResult

ROLLBACK_PLAN_FILE_NAME = 'ROLLBACK_PLAN.json'
class PostGISRollbackPlanStorageError(RuntimeError):
    pass

_STORE = ArtifactStore(PostGISRollbackPlan, 'rollback_plan_id', 'postgis-rollback-plan',
                       ROLLBACK_PLAN_FILE_NAME, 'rollback plan', PostGISRollbackPlanStorageError)


def canonical_postgis_rollback_plan_json(value):
    return _STORE.canonical(value)


def postgis_rollback_plan_sha256(value):
    return _STORE.digest(value)


def persist_postgis_rollback_plan(value, *, rollback_plan_root: Path):
    path, digest, value = _STORE.persist(value, rollback_plan_root)
    return PostGISRollbackPlanStorageResult(rollback_plan_id=value.rollback_plan_id,
        promotion_plan_id=value.promotion_plan_id, execution_id=value.execution_id,
        verification_id=value.verification_id, rollback_plan_sha256=digest,
        rollback_plan_directory=path.parent.as_posix(), rollback_plan_file=path.as_posix())


def load_postgis_rollback_plan(rollback_plan_file: Path, *, rollback_plan_root: Path):
    return _STORE.load(rollback_plan_file, rollback_plan_root)
