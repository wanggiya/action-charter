"""Explicit immutable context review, with source rechecking and no work authority."""
from __future__ import annotations
import fcntl
import json
import os
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from .service import retrieve_task_context, ContextRetrievalError
from geoagent_harness.context_pack.redaction import redact_value
from geoagent_harness.task_history.service import DIGEST, _canonical, _digest, _task_dir

class ContextReviewError(ValueError):
    """Context review is stale, invalid or unsafe."""


def save_reviewed_context(*, history_root: Path, review_root: Path, query: str,
                          task_ids: list[str], confirmed_context_sha256: str,
                          reviewer: str, reason: str, now: datetime | None = None) -> dict:
    if not DIGEST.fullmatch(confirmed_context_sha256 or ""):
        raise ContextReviewError("context digest is invalid")
    if (not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 200
            or not isinstance(reason, str) or not reason.strip() or len(reason) > 2000):
        raise ContextReviewError("reviewer and reason are required within their limits")
    # Validate the selection before locking, then regenerate under append locks.
    retrieve_task_context(root=history_root, query=query, task_ids=task_ids)
    with ExitStack() as stack:
        for task_id in sorted(task_ids):
            task = _task_dir(history_root, task_id)
            descriptor = os.open(task / ".lock", os.O_RDONLY | os.O_NOFOLLOW)
            stream = stack.enter_context(os.fdopen(descriptor, "rb"))
            fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
        context = retrieve_task_context(root=history_root, query=query, task_ids=task_ids)
        if context["context_sha256"] != confirmed_context_sha256:
            raise ContextReviewError("context sources or selection changed; retrieve and review again")
        if not context["excerpts"]:
            raise ContextReviewError("empty retrieval cannot be stored as reviewed context")
        timestamp = now or datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            raise ContextReviewError("review timestamp requires a timezone")
        record = {"schema_version": "1.0", "status": "reviewed_context_only",
                  "context": context, "context_sha256": confirmed_context_sha256,
                  "reviewer": redact_value(reviewer.strip()), "reason": redact_value(reason.strip()),
                  "reviewed_at": timestamp.isoformat(), "review_performed": True,
                  "plan_approved": False, "execution_performed": False, "model_called": False}
        raw = _canonical(record)
        record_digest = _digest(raw)
        filename = f"context-review.{record_digest}.json"
        if review_root.is_symlink() or (review_root.exists() and not review_root.is_dir()):
            raise ContextReviewError("review root is unsafe")
        review_root.mkdir(parents=True, exist_ok=True)
        directory = os.open(review_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        temporary = f".pending-{uuid4().hex}"
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            try:
                os.link(temporary, filename, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
            except FileExistsError as exc:
                raise ContextReviewError("exact review record already exists") from exc
            os.fsync(directory)
        finally:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass
            os.close(directory)
    return {"schema_version": "1.0", "status": "reviewed_context_stored",
            "review_filename": filename, "review_sha256": record_digest,
            "context_sha256": confirmed_context_sha256, "review_performed": True,
            "plan_approved": False, "execution_performed": False, "model_called": False}


def load_reviewed_context(*, review_root: Path, filename: str, history_root: Path) -> dict:
    """Recheck record bytes and current source snapshot before future model use."""
    import re
    if not re.fullmatch(r"context-review\.[a-f0-9]{64}\.json", filename):
        raise ContextReviewError("review filename is invalid")
    if review_root.is_symlink():
        raise ContextReviewError("review root is unsafe")
    directory = os.open(review_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        descriptor = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        import stat
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 32768:
                raise ContextReviewError("review artifact is unsafe or oversized")
            raw = stream.read(32769)
        if len(raw) > 32768 or _digest(raw) != filename.split(".")[1]:
            raise ContextReviewError("review artifact digest mismatch")
        record = json.loads(raw)
        if _canonical(record) != raw or record.get("status") != "reviewed_context_only":
            raise ContextReviewError("review artifact is invalid")
        context = record["context"]
        current = retrieve_task_context(root=history_root, query=context["query"], task_ids=context["selected_task_ids"])
        if current != context or current["context_sha256"] != record["context_sha256"]:
            raise ContextReviewError("reviewed context is stale; retrieve and review again")
        return record
    finally:
        os.close(directory)
