"""Immutable storage for transactional rollback evidence."""
import hashlib,json,os,shutil,tempfile
from pathlib import Path
from pydantic import ValidationError
from .schemas import PostGISRollbackExecutionResult,PostGISRollbackExecutionStorageResult
FILE_NAME="EXECUTION.json"
class PostGISRollbackExecutionStorageError(RuntimeError): pass
def canonical_postgis_rollback_execution_json(value):
    try: snapshot=PostGISRollbackExecutionResult.model_validate(value.model_dump(mode="json"))
    except ValidationError as exc: raise PostGISRollbackExecutionStorageError("rollback execution failed schema validation") from exc
    return json.dumps(snapshot.model_dump(mode="json"),sort_keys=True,indent=2,ensure_ascii=False)+"\n"
def postgis_rollback_execution_sha256(value): return hashlib.sha256(canonical_postgis_rollback_execution_json(value).encode()).hexdigest()
def persist_postgis_rollback_execution(value,*,execution_root:Path):
    content=canonical_postgis_rollback_execution_json(value); digest=hashlib.sha256(content.encode()).hexdigest()
    if execution_root.is_symlink(): raise PostGISRollbackExecutionStorageError("rollback execution root cannot be a symlink")
    try: execution_root.mkdir(parents=True,exist_ok=True); root=execution_root.resolve(strict=True)
    except OSError as exc: raise PostGISRollbackExecutionStorageError("rollback execution root unavailable") from exc
    directory=root/f"{value.execution_id}.{digest}.postgis-rollback-execution"
    if directory.exists() or directory.is_symlink(): raise PostGISRollbackExecutionStorageError("rollback execution package already exists")
    temporary=Path(tempfile.mkdtemp(prefix=".postgis-rollback-execution-",dir=root)); staged=temporary/"record"
    try: staged.mkdir(); (staged/FILE_NAME).write_text(content,encoding="utf-8",newline="\n"); os.replace(staged,directory); temporary.rmdir()
    except OSError as exc: shutil.rmtree(temporary,ignore_errors=True); raise PostGISRollbackExecutionStorageError("rollback execution could not be persisted") from exc
    return PostGISRollbackExecutionStorageResult(execution_id=value.execution_id,rollback_plan_id=value.rollback_plan_id,rollback_plan_sha256=value.rollback_plan_sha256,approval_id=value.approval_id,approval_sha256=value.approval_sha256,execution_sha256=digest,execution_directory=directory.as_posix(),execution_file=(directory/FILE_NAME).as_posix())
def load_postgis_rollback_execution(path:Path,*,execution_root:Path):
    try:
        root=execution_root.resolve(strict=True); candidate=path if path.is_absolute() else root/path
        if execution_root.is_symlink() or candidate.is_symlink() or candidate.parent.is_symlink(): raise OSError
        safe=candidate.resolve(strict=True)
        if safe.name!=FILE_NAME or safe.parent.parent!=root or not safe.is_file(): raise OSError
        raw=safe.read_text(encoding="utf-8"); value=PostGISRollbackExecutionResult.model_validate_json(raw)
    except (OSError,UnicodeError,ValidationError) as exc: raise PostGISRollbackExecutionStorageError("rollback execution evidence invalid") from exc
    digest=postgis_rollback_execution_sha256(value)
    if raw!=canonical_postgis_rollback_execution_json(value) or safe.parent.name!=f"{value.execution_id}.{digest}.postgis-rollback-execution": raise PostGISRollbackExecutionStorageError("rollback execution package identity invalid")
    if {x.name for x in safe.parent.iterdir()}!={FILE_NAME}: raise PostGISRollbackExecutionStorageError("rollback execution package contains unexpected files")
    return value
