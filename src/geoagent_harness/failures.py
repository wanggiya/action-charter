"""Shared structured failure taxonomy for the harness."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.redaction import redact_text


class FailureCategory(str, Enum):
    """Stable high-level failure categories."""

    INVALID_INPUT = "invalid_input"
    CONFIGURATION = "configuration"
    POLICY_DENIED = "policy_denied"
    APPROVAL_REJECTED = "approval_rejected"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    TIMEOUT = "timeout"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    EXTERNAL_RESPONSE_INVALID = "external_response_invalid"
    EXECUTION_FAILED = "execution_failed"
    VALIDATION_FAILED = "validation_failed"
    CANCELLED = "cancelled"
    INTERNAL_ERROR = "internal_error"


class FailureStage(str, Enum):
    """Workflow stage where a failure was observed."""

    CONFIGURATION = "configuration"
    CONTEXT = "context"
    PLANNING = "planning"
    APPROVAL = "approval"
    EXECUTION = "execution"
    VALIDATION = "validation"
    REPORTING = "reporting"
    CRITIQUE = "critique"
    MODEL = "model"
    MCP = "mcp"
    ARTIFACT = "artifact"


class RetryDisposition(str, Enum):
    """Whether and how a failed operation may be retried."""

    NEVER = "never"
    SAFE_READ_ONLY = "safe_read_only"
    MANUAL_REVIEW = "manual_review"


_EXIT_CODES: dict[FailureCategory, int] = {
    FailureCategory.INVALID_INPUT: 2,
    FailureCategory.CONFIGURATION: 2,
    FailureCategory.POLICY_DENIED: 2,
    FailureCategory.APPROVAL_REJECTED: 2,
    FailureCategory.NOT_FOUND: 2,
    FailureCategory.CONFLICT: 2,
    FailureCategory.TIMEOUT: 3,
    FailureCategory.DEPENDENCY_UNAVAILABLE: 3,
    FailureCategory.EXTERNAL_RESPONSE_INVALID: 4,
    FailureCategory.EXECUTION_FAILED: 4,
    FailureCategory.VALIDATION_FAILED: 1,
    FailureCategory.CANCELLED: 130,
    FailureCategory.INTERNAL_ERROR: 5,
}


class FailureRecord(BaseModel):
    """Secret-redacted structured description of one failure."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    category: FailureCategory
    code: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    stage: FailureStage
    message: str = Field(
        min_length=1,
        max_length=2000,
    )
    retry: RetryDisposition
    exit_code: int = Field(ge=1, le=255)
    cause_type: str = Field(
        min_length=1,
        max_length=200,
    )
    secrets_redacted: Literal[True] = True


class GeoAgentError(RuntimeError):
    """Base error carrying stable failure metadata."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "geoagent_error",
        category: FailureCategory = (
            FailureCategory.INTERNAL_ERROR
        ),
        retry: RetryDisposition = (
            RetryDisposition.NEVER
        ),
    ) -> None:
        super().__init__(message)

        self.code = code
        self.category = category
        self.retry = retry


def exit_code_for_category(
    category: FailureCategory,
) -> int:
    """Return the stable CLI exit code for a category."""

    return _EXIT_CODES[category]


def failure_from_exception(
    exception: BaseException,
    *,
    stage: FailureStage,
) -> FailureRecord:
    """Convert an exception into secret-redacted evidence."""

    if isinstance(exception, KeyboardInterrupt):
        category = FailureCategory.CANCELLED
        code = "operator_cancelled"

        if stage in {
            FailureStage.EXECUTION,
            FailureStage.MCP,
        }:
            retry = RetryDisposition.MANUAL_REVIEW
        else:
            retry = RetryDisposition.NEVER

        raw_message = "Operation cancelled by operator"

    elif isinstance(exception, GeoAgentError):
        category = exception.category
        code = exception.code
        retry = exception.retry
        raw_message = str(exception)

    else:
        category = FailureCategory.INTERNAL_ERROR
        code = "unclassified_internal_error"
        retry = RetryDisposition.NEVER
        raw_message = str(exception)

    message = redact_text(raw_message).strip()

    if not message:
        message = "Operation failed without an error message"

    return FailureRecord(
        category=category,
        code=code,
        stage=stage,
        message=message,
        retry=retry,
        exit_code=exit_code_for_category(category),
        cause_type=type(exception).__name__,
        secrets_redacted=True,
    )
