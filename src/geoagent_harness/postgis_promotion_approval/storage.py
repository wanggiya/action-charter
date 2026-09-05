"""Immutable digest-addressed PostGIS promotion approval storage."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from pydantic import ValidationError

from geoagent_harness.postgis_promotion_approval.schemas import (
    PostGISPromotionApproval,
    PostGISPromotionApprovalStorageResult,
)
from geoagent_harness.redaction import redact_value


APPROVAL_FILE_NAME = "APPROVAL.json"


class PostGISPromotionApprovalStorageError(RuntimeError):
    """Raised when immutable approval storage cannot be trusted."""


def _validated_approval_snapshot(
    approval: PostGISPromotionApproval,
) -> PostGISPromotionApproval:
    """Revalidate a detached snapshot before using approval evidence."""
    try:
        return PostGISPromotionApproval.model_validate(
            approval.model_dump(mode="json")
        )
    except ValidationError as exc:
        raise PostGISPromotionApprovalStorageError(
            "promotion approval failed schema validation"
        ) from exc


def canonical_postgis_promotion_approval_json(
    approval: PostGISPromotionApproval,
) -> str:
    """Return canonical human-readable approval JSON."""
    payload = _validated_approval_snapshot(approval).model_dump(mode="json")
    if redact_value(payload) != payload:
        raise PostGISPromotionApprovalStorageError(
            "promotion approval contains unredacted secret material"
        )
    return json.dumps(
        payload, sort_keys=True, indent=2, ensure_ascii=False
    ) + "\n"


def postgis_promotion_approval_sha256(
    approval: PostGISPromotionApproval,
) -> str:
    return hashlib.sha256(
        canonical_postgis_promotion_approval_json(approval).encode("utf-8")
    ).hexdigest()


def persist_postgis_promotion_approval(
    approval: PostGISPromotionApproval,
    *,
    approval_root: Path,
) -> PostGISPromotionApprovalStorageResult:
    """Atomically persist one write-once approval package."""
    approval = _validated_approval_snapshot(approval)
    content = canonical_postgis_promotion_approval_json(approval)
    if approval_root.is_symlink():
        raise PostGISPromotionApprovalStorageError(
            "promotion approval root cannot be a symlink"
        )
    try:
        approval_root.mkdir(parents=True, exist_ok=True)
        root = approval_root.resolve(strict=True)
    except OSError as exc:
        raise PostGISPromotionApprovalStorageError(
            "promotion approval root is unavailable"
        ) from exc
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    directory = root / (
        f"{approval.approval_id}.{digest}.postgis-promotion-approval"
    )
    if directory.exists() or directory.is_symlink():
        raise PostGISPromotionApprovalStorageError(
            "promotion approval package already exists"
        )
    temporary = Path(tempfile.mkdtemp(prefix=".postgis-approval-", dir=root))
    staged = temporary / "record"
    try:
        staged.mkdir()
        with (staged / APPROVAL_FILE_NAME).open(
            "x", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(content)
        staged_digest = hashlib.sha256(
            (staged / APPROVAL_FILE_NAME).read_bytes()
        ).hexdigest()
        if staged_digest != digest:
            raise PostGISPromotionApprovalStorageError(
                "staged promotion approval digest changed"
            )
        os.replace(staged, directory)
        temporary.rmdir()
    except (OSError, PostGISPromotionApprovalStorageError) as exc:
        shutil.rmtree(temporary, ignore_errors=True)
        if isinstance(exc, PostGISPromotionApprovalStorageError):
            raise
        raise PostGISPromotionApprovalStorageError(
            "promotion approval package could not be persisted"
        ) from exc
    final_file = directory / APPROVAL_FILE_NAME
    if hashlib.sha256(final_file.read_bytes()).hexdigest() != digest:
        raise PostGISPromotionApprovalStorageError(
            "persisted promotion approval digest changed"
        )
    return PostGISPromotionApprovalStorageResult(
        approval_id=approval.approval_id,
        plan_id=approval.plan_id,
        plan_sha256=approval.plan_sha256,
        approval_sha256=digest,
        approval_directory=directory.as_posix(),
        approval_file=final_file.as_posix(),
        decision=approval.decision,
        approved_step_ids=approval.approved_step_ids,
    )


def load_postgis_promotion_approval(
    approval_file: Path,
    *,
    approval_root: Path,
) -> PostGISPromotionApproval:
    """Load and verify one canonical digest-addressed approval package."""
    if approval_root.is_symlink():
        raise PostGISPromotionApprovalStorageError(
            "promotion approval root cannot be a symlink"
        )
    try:
        root = approval_root.resolve(strict=True)
        candidate = (
            approval_file
            if approval_file.is_absolute()
            else root / approval_file
        )
        if candidate.is_symlink() or candidate.parent.is_symlink():
            raise PostGISPromotionApprovalStorageError(
                "promotion approval path cannot be a symlink"
            )
        safe = candidate.resolve(strict=True)
    except OSError as exc:
        raise PostGISPromotionApprovalStorageError(
            "promotion approval file is unavailable"
        ) from exc
    if (
        safe.name != APPROVAL_FILE_NAME
        or safe.parent.parent != root
        or not safe.is_file()
    ):
        raise PostGISPromotionApprovalStorageError(
            "promotion approval escaped its approved package"
        )
    try:
        raw = safe.read_text(encoding="utf-8")
        payload = json.loads(raw)
        approval = PostGISPromotionApproval.model_validate(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
        raise PostGISPromotionApprovalStorageError(
            "promotion approval failed schema validation"
        ) from exc
    canonical = canonical_postgis_promotion_approval_json(approval)
    if raw != canonical:
        raise PostGISPromotionApprovalStorageError(
            "promotion approval file is not canonical"
        )
    digest = postgis_promotion_approval_sha256(approval)
    expected = (
        f"{approval.approval_id}.{digest}.postgis-promotion-approval"
    )
    if safe.parent.name != expected:
        raise PostGISPromotionApprovalStorageError(
            "promotion approval package identity is invalid"
        )
    if {item.name for item in safe.parent.iterdir()} != {APPROVAL_FILE_NAME}:
        raise PostGISPromotionApprovalStorageError(
            "promotion approval package contains unexpected files"
        )
    return approval
