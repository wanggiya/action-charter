"""Deterministic context candidates, with no model call or implicit authority."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any
from geoagent_harness.context_pack.redaction import redact_value
from geoagent_harness.task_history.service import (
    TASK_ID, TaskHistoryError, _canonical, _digest, load_task_events,
)

MAX_TASKS = 5
MAX_EXCERPTS = 8
MAX_EXCERPT_CHARACTERS = 1000
MAX_QUERY_CHARACTERS = 1000

class ContextRetrievalError(ValueError):
    """Requested history scope or source integrity is invalid."""


def _terms(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.casefold())[:64])


def retrieve_task_context(*, root: Path, query: str, task_ids: list[str]) -> dict[str, Any]:
    """Rank excerpts only within the explicitly selected, verified histories."""
    if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY_CHARACTERS:
        raise ContextRetrievalError("query must contain 1 to 1000 characters")
    if (not isinstance(task_ids, list) or not 1 <= len(task_ids) <= MAX_TASKS
            or any(not isinstance(task, str) or not TASK_ID.fullmatch(task) for task in task_ids)
            or len(set(task_ids)) != len(task_ids)):
        raise ContextRetrievalError("select 1 to 5 unique valid task IDs")
    safe_query = redact_value(query.strip())
    terms = _terms(safe_query)
    if not terms:
        raise ContextRetrievalError("query must contain searchable words")
    candidates, snapshots = [], []
    for task_id in sorted(task_ids):
        try:
            events = load_task_events(root=root, task_id=task_id)
        except (TaskHistoryError, OSError) as exc:
            raise ContextRetrievalError("selected task history failed source verification") from exc
        if not events:
            raise ContextRetrievalError("selected task history is missing or empty")
        snapshots.append({"task_id": task_id, "event_count": len(events),
                          "head_sha256": _digest(_canonical(events[-1]))})
        for event in events:
            payload = event["payload"]
            full_text = payload["summary"] + ("\n" + payload["details"] if payload["details"] else "")
            text = full_text[:MAX_EXCERPT_CHARACTERS]
            matched = sorted(terms & _terms(text))
            if not matched:
                continue
            digest = _digest(_canonical(event))
            candidates.append({"task_id": task_id, "sequence": event["sequence"],
                "event_type": event["event_type"], "text": text,
                "excerpt_truncated": len(full_text) > len(text), "matched_terms": matched,
                "score": len(matched), "occurred_at": event["occurred_at"],
                "source": {"path": f"{task_id}/{event['sequence']:06d}.{digest}.json", "sha256": digest}})
    candidates.sort(key=lambda item: (-item["score"], item["task_id"], -item["sequence"]))
    selected = candidates[:MAX_EXCERPTS]
    basis = {"schema_version": "1.0", "status": "retrieved_not_reviewed",
             "query": safe_query, "selected_task_ids": sorted(task_ids), "source_snapshots": snapshots,
             "excerpts": selected, "candidate_count": len(candidates),
             "truncated": len(candidates) > len(selected), "selection_method": "bounded_keyword_overlap_v1",
             "content_trust": "untrusted_historical_text", "review_performed": False,
             "approval_inferred": False, "execution_performed": False, "model_called": False}
    return {**basis, "context_sha256": _digest(_canonical(basis))}
