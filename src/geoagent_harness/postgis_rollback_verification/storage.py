"""Immutable storage for independent rollback verification."""
import hashlib, json, os, shutil, tempfile
from pathlib import Path
from pydantic import ValidationError
from .schemas import PostGISRollbackVerificationResult

FILE_NAME = "VERIFICATION.json"
class PostGISRollbackVerificationStorageError(RuntimeError): pass

def canonical_postgis_rollback_verification_json(value):
    try:
        snapshot = PostGISRollbackVerificationResult.model_validate(value.model_dump(mode="json"))
    except ValidationError as exc:
        raise PostGISRollbackVerificationStorageError("rollback verification failed schema validation") from exc
    return json.dumps(snapshot.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False) + "\n"

def postgis_rollback_verification_sha256(value):
    return hashlib.sha256(canonical_postgis_rollback_verification_json(value).encode()).hexdigest()

def persist_postgis_rollback_verification(value, *, verification_root: Path):
    content = canonical_postgis_rollback_verification_json(value)
    digest = hashlib.sha256(content.encode()).hexdigest()
    if verification_root.is_symlink():
        raise PostGISRollbackVerificationStorageError("rollback verification root cannot be a symlink")
    try:
        verification_root.mkdir(parents=True, exist_ok=True)
        root = verification_root.resolve(strict=True)
    except OSError as exc:
        raise PostGISRollbackVerificationStorageError("rollback verification root unavailable") from exc
    directory = root / f"{value.verification_id}.{digest}.postgis-rollback-verification"
    if directory.exists() or directory.is_symlink():
        raise PostGISRollbackVerificationStorageError("rollback verification package already exists")
    temporary = Path(tempfile.mkdtemp(prefix=".postgis-rollback-verification-", dir=root))
    staged = temporary / "record"
    try:
        staged.mkdir()
        (staged / FILE_NAME).write_text(content, encoding="utf-8", newline="\n")
        os.replace(staged, directory)
        temporary.rmdir()
    except OSError as exc:
        shutil.rmtree(temporary, ignore_errors=True)
        raise PostGISRollbackVerificationStorageError("rollback verification could not be persisted") from exc
    return directory / FILE_NAME

def load_postgis_rollback_verification(path: Path, *, verification_root: Path):
    try:
        root = verification_root.resolve(strict=True)
        candidate = path if path.is_absolute() else root / path
        if verification_root.is_symlink() or candidate.is_symlink() or candidate.parent.is_symlink():
            raise OSError
        safe = candidate.resolve(strict=True)
        if safe.name != FILE_NAME or safe.parent.parent != root or not safe.is_file():
            raise OSError
        raw = safe.read_text(encoding="utf-8")
        value = PostGISRollbackVerificationResult.model_validate_json(raw)
    except (OSError, UnicodeError, ValidationError) as exc:
        raise PostGISRollbackVerificationStorageError("rollback verification evidence invalid") from exc
    digest = postgis_rollback_verification_sha256(value)
    expected = f"{value.verification_id}.{digest}.postgis-rollback-verification"
    if raw != canonical_postgis_rollback_verification_json(value) or safe.parent.name != expected:
        raise PostGISRollbackVerificationStorageError("rollback verification package identity invalid")
    if {x.name for x in safe.parent.iterdir()} != {FILE_NAME}:
        raise PostGISRollbackVerificationStorageError("rollback verification package contains unexpected files")
    return value
