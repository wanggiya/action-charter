"""Immutable storage for PostGIS rollback approvals."""
import hashlib, json, os, shutil, tempfile
from pathlib import Path
from pydantic import ValidationError
from geoagent_harness.redaction import redact_value
from .schemas import PostGISRollbackApproval, PostGISRollbackApprovalStorageResult

FILE_NAME = "APPROVAL.json"
class PostGISRollbackApprovalStorageError(RuntimeError): pass

def canonical_postgis_rollback_approval_json(value):
    try: snapshot=PostGISRollbackApproval.model_validate(value.model_dump(mode="json"))
    except ValidationError as exc: raise PostGISRollbackApprovalStorageError("rollback approval failed schema validation") from exc
    payload=snapshot.model_dump(mode="json")
    if redact_value(payload)!=payload: raise PostGISRollbackApprovalStorageError("rollback approval contains unredacted secrets")
    return json.dumps(payload,sort_keys=True,indent=2,ensure_ascii=False)+"\n"

def postgis_rollback_approval_sha256(value): return hashlib.sha256(canonical_postgis_rollback_approval_json(value).encode()).hexdigest()

def persist_postgis_rollback_approval(value,*,approval_root:Path):
    content=canonical_postgis_rollback_approval_json(value); digest=hashlib.sha256(content.encode()).hexdigest()
    if approval_root.is_symlink(): raise PostGISRollbackApprovalStorageError("rollback approval root cannot be a symlink")
    try: approval_root.mkdir(parents=True,exist_ok=True); root=approval_root.resolve(strict=True)
    except OSError as exc: raise PostGISRollbackApprovalStorageError("rollback approval root unavailable") from exc
    directory=root/f"{value.approval_id}.{digest}.postgis-rollback-approval"
    if directory.exists() or directory.is_symlink(): raise PostGISRollbackApprovalStorageError("rollback approval package already exists")
    temporary=Path(tempfile.mkdtemp(prefix=".postgis-rollback-approval-",dir=root)); staged=temporary/"record"
    try:
        staged.mkdir(); (staged/FILE_NAME).write_text(content,encoding="utf-8",newline="\n"); os.replace(staged,directory); temporary.rmdir()
    except OSError as exc:
        shutil.rmtree(temporary,ignore_errors=True); raise PostGISRollbackApprovalStorageError("rollback approval could not be persisted") from exc
    return PostGISRollbackApprovalStorageResult(approval_id=value.approval_id,rollback_plan_id=value.rollback_plan_id,rollback_plan_sha256=value.rollback_plan_sha256,approval_sha256=digest,approval_directory=directory.as_posix(),approval_file=(directory/FILE_NAME).as_posix(),decision=value.decision,approved_step_ids=value.approved_step_ids)

def load_postgis_rollback_approval(path:Path,*,approval_root:Path):
    try:
        root=approval_root.resolve(strict=True); candidate=path if path.is_absolute() else root/path
        if approval_root.is_symlink() or candidate.is_symlink() or candidate.parent.is_symlink(): raise OSError
        safe=candidate.resolve(strict=True)
        if safe.name!=FILE_NAME or safe.parent.parent!=root or not safe.is_file(): raise OSError
        raw=safe.read_text(encoding="utf-8"); value=PostGISRollbackApproval.model_validate_json(raw)
    except (OSError,UnicodeError,ValidationError) as exc: raise PostGISRollbackApprovalStorageError("rollback approval evidence invalid") from exc
    digest=postgis_rollback_approval_sha256(value)
    if raw!=canonical_postgis_rollback_approval_json(value) or safe.parent.name!=f"{value.approval_id}.{digest}.postgis-rollback-approval": raise PostGISRollbackApprovalStorageError("rollback approval package identity invalid")
    if {x.name for x in safe.parent.iterdir()}!={FILE_NAME}: raise PostGISRollbackApprovalStorageError("rollback approval package contains unexpected files")
    return value
