"""Explicit immutable review of resolved intent, never work approval."""
from __future__ import annotations
import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field, model_validator
from geoagent_harness.intent.service import IntentProposal, IntentError
from geoagent_harness.context_retrieval import load_reviewed_context
from geoagent_harness.task_history.service import _canonical, _digest
from geoagent_harness.context_pack.redaction import redact_value

class IntentResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal["1.0"]
    agent_id: Literal["intent"]
    model: str = Field(min_length=1, max_length=200)
    original_request: str = Field(min_length=1, max_length=4000)
    clarification_answers: list[str] = Field(max_length=5)
    review_filename: str | None = Field(pattern=r"^context-review\.[a-f0-9]{64}\.json$")
    context_sha256: str | None = Field(pattern=r"^[a-f0-9]{64}$")
    proposal: IntentProposal
    status: Literal["proposed_not_saved"]
    human_review_required: Literal[True]
    correction_attempted: bool = False  # Older 22C/D proposals did not record this flag.
    model_called: Literal[True]
    plan_created: Literal[False]
    approval_inferred: Literal[False]
    execution_performed: Literal[False]
    tools_called: Literal[False]

    @model_validator(mode="after")
    def explicit_context_pair(self):
        if (self.review_filename is None) != (self.context_sha256 is None):
            raise ValueError("history filename and digest must both be present or both null")
        if self.review_filename is None and self.proposal.cited_sequences:
            raise ValueError("no-history intent cannot cite historical events")
        return self

class IntentReviewRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal["1.0"]
    status: Literal["reviewed_intent_only"]
    intent: IntentResult
    intent_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewer: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    reviewed_at: str
    review_performed: Literal[True]
    plan_approved: Literal[False]
    execution_performed: Literal[False]
    model_called: Literal[False]


def _checked_intent(payload: dict, root: Path) -> tuple[IntentResult, str]:
    try:
        intent = IntentResult.model_validate(payload)
    except ValueError as exc:
        raise IntentError("intent envelope is invalid") from exc
    if any(not answer.strip() or len(answer) > 1000 for answer in intent.clarification_answers):
        raise IntentError("clarification answers are invalid")
    if intent.review_filename is not None:
        context = load_reviewed_context(review_root=root / "reviewed-contexts", history_root=root / "task-history", filename=intent.review_filename)
        if context["context_sha256"] != intent.context_sha256:
            raise IntentError("intent context digest mismatch")
        if context.get("review_performed") is not True or context.get("plan_approved") is not False:
            raise IntentError("context review metadata is invalid")
        if not set(intent.proposal.cited_sequences).issubset({e["sequence"] for e in context["context"]["excerpts"]}):
            raise IntentError("intent citations are unavailable")
    return intent, _digest(_canonical(intent.model_dump()))


def inspect_intent_for_review(*, payload: dict, project_root: Path) -> dict:
    intent, digest = _checked_intent(payload, project_root.resolve())
    resolved = intent.proposal.status == "intent_proposed"
    return {"schema_version": "1.0", "status": "ready_for_intent_review" if resolved else "clarification_required",
            "intent_sha256": digest, "review_allowed": resolved, "intent": intent.model_dump(),
            "review_performed": False, "plan_approved": False, "execution_performed": False, "model_called": False}


def read_intent_file(path: Path) -> dict:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 65536:
            raise IntentError("intent file is unsafe or oversized")
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise IntentError("intent file is oversized")
    return json.loads(raw)


def save_reviewed_intent(*, payload: dict, project_root: Path, confirmed_intent_sha256: str,
                         reviewer: str, reason: str, now: datetime | None = None) -> dict:
    root = project_root.resolve()
    intent, digest = _checked_intent(payload, root)
    if intent.proposal.status != "intent_proposed":
        raise IntentError("unresolved clarification cannot be stored as reviewed intent")
    if digest != confirmed_intent_sha256:
        raise IntentError("intent changed; inspect and review again")
    if not reviewer.strip() or not reason.strip() or len(reviewer) > 200 or len(reason) > 2000:
        raise IntentError("bounded reviewer and reason are required")
    timestamp = now or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise IntentError("review timestamp requires timezone")
    record = IntentReviewRecord(schema_version="1.0",status="reviewed_intent_only",intent=intent,
        intent_sha256=digest,reviewer=redact_value(reviewer.strip()),reason=redact_value(reason.strip()),
        reviewed_at=timestamp.isoformat(),review_performed=True,plan_approved=False,execution_performed=False,model_called=False)
    raw = _canonical(record.model_dump()); record_digest = _digest(raw)
    filename = f"intent-review.{record_digest}.json"
    destination = root / "reviewed-intents"
    if destination.is_symlink():
        raise IntentError("intent review root is unsafe")
    destination.mkdir(exist_ok=True)
    directory = os.open(destination,os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    pending = f".pending-{uuid4().hex}"
    try:
        descriptor=os.open(pending,os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,0o600,dir_fd=directory)
        with os.fdopen(descriptor,"wb") as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        # Recheck context after preparing bytes and before publishing.
        _checked_intent(payload, root)
        try:
            os.link(pending,filename,src_dir_fd=directory,dst_dir_fd=directory,follow_symlinks=False)
        except FileExistsError as exc:
            raise IntentError("exact intent review already exists") from exc
        os.fsync(directory)
    finally:
        try:os.unlink(pending,dir_fd=directory)
        except FileNotFoundError:pass
        os.close(directory)
    return {"schema_version":"1.0","status":"reviewed_intent_stored","review_filename":filename,
            "review_sha256":record_digest,"intent_sha256":digest,"review_performed":True,
            "plan_approved":False,"execution_performed":False,"model_called":False}


def load_reviewed_intent(*, project_root: Path, filename: str) -> dict:
    if not re.fullmatch(r"intent-review\.[a-f0-9]{64}\.json",filename):
        raise IntentError("intent review filename is invalid")
    root=project_root.resolve()
    directory=os.open(root / "reviewed-intents",os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        descriptor=os.open(filename,os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,dir_fd=directory)
        with os.fdopen(descriptor,"rb") as stream:
            info=os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 65536:
                raise IntentError("intent review is unsafe or oversized")
            raw=stream.read(65537)
    finally:os.close(directory)
    if len(raw)>65536 or _digest(raw)!=filename.split(".")[1]:
        raise IntentError("intent review digest mismatch")
    try:record=IntentReviewRecord.model_validate(json.loads(raw))
    except ValueError as exc:raise IntentError("intent review schema is invalid") from exc
    if _canonical(record.model_dump())!=raw:
        raise IntentError("intent review is not canonical")
    intent,digest=_checked_intent(record.intent.model_dump(),root)
    if digest!=record.intent_sha256 or intent.proposal.status!="intent_proposed":
        raise IntentError("intent review scope is invalid")
    return record.model_dump()
