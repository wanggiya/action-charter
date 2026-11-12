"""Compatibility facade for shared immutable promotion execution evidence."""
from pathlib import Path
from geoagent_harness.data.databases.postgis.artifact_storage import ArtifactStore
from geoagent_harness.data.databases.postgis.promotion.execution.schemas import PostGISPromotionExecutionResult, PostGISPromotionExecutionStorageResult

EXECUTION_FILE_NAME = 'EXECUTION.json'
class PostGISPromotionExecutionStorageError(RuntimeError):
    pass

_STORE = ArtifactStore(PostGISPromotionExecutionResult, 'execution_id', 'postgis-promotion-execution',
                       EXECUTION_FILE_NAME, 'promotion execution', PostGISPromotionExecutionStorageError, redact=False)


def canonical_postgis_promotion_execution_json(result):
    return _STORE.canonical(result)


def postgis_promotion_execution_sha256(result):
    return _STORE.digest(result)


def persist_postgis_promotion_execution(result, *, execution_root: Path):
    path, digest, result = _STORE.persist(result, execution_root)
    return PostGISPromotionExecutionStorageResult(
        execution_id=result.execution_id, plan_id=result.plan_id, plan_sha256=result.plan_sha256,
        approval_id=result.approval_id, approval_sha256=result.approval_sha256,
        execution_sha256=digest, execution_directory=path.parent.as_posix(), execution_file=path.as_posix())


def load_postgis_promotion_execution(execution_file: Path, *, execution_root: Path):
    return _STORE.load(execution_file, execution_root)
