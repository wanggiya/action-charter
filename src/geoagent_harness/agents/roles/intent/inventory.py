"""Bounded read-only recovery inventory; reviews never grant work authority."""
from __future__ import annotations
from geoagent_harness.platform.workspace import runtime_store_path, WorkspaceLayout
from geoagent_harness.core.ledger.task_history.service import history_directory, TaskHistoryError
import os
import re
from itertools import islice
from pathlib import Path
from geoagent_harness.agents.memory.context_retrieval import load_reviewed_context
from geoagent_harness.contracts.context_redaction import redact_text
from geoagent_harness.agents.roles.intent.review import load_reviewed_intent


def reviewed_context_inventory(*, project_root: Path) -> dict:
    root = project_root.resolve()
    candidates = []
    findings = []
    truncated = False
    layout = WorkspaceLayout.load(root)
    for kind, folder, prefix in [('context', 'reviewed-contexts', 'context-review'), ('intent', 'reviewed-intents', 'intent-review')]:
        # Inventory reports an unsafe store without following it. Configuration
        # and missing-migration errors still propagate rather than hiding history.
        if (layout.state_root / folder).is_symlink():
            findings.append(f'{kind} review directory is unavailable or unsafe')
            continue
        directory = runtime_store_path(root, folder)
        if not directory.exists() and not directory.is_symlink():
            continue
        try:
            fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                with os.scandir(fd) as entries:
                    batch = list(islice(entries, 201))
                if len(batch) > 200:
                    truncated = True
                for entry in batch[:200]:
                    if re.fullmatch(re.escape(prefix) + r'\.[a-f0-9]{64}\.json', entry.name):
                        candidates.append((entry.stat(follow_symlinks=False).st_mtime, kind, entry.name))
            finally:
                os.close(fd)
        except OSError:
            findings.append(f'{kind} review directory is unavailable or unsafe')
    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    truncated = truncated or len(candidates) > 50
    reviews = []
    for _, kind, filename in candidates[:50]:
        item = dict(kind=kind, review_filename=filename, status='blocked', summary='Unavailable or stale review', reviewed_at=None, reviewer=None, reason='Sources changed, or review is invalid or unavailable; retrieve and review again')
        try:
            record = (load_reviewed_intent(project_root=root, filename=filename) if kind == 'intent' else
                      load_reviewed_context(review_root=runtime_store_path(root, 'reviewed-contexts'), history_root=history_directory(root), filename=filename))
            # Explicitly reject any forged work-authority flags, including older context artifacts.
            if record.get('review_performed') is not True or any(record.get(key) is not False for key in ('plan_approved', 'execution_performed', 'model_called')):
                raise ValueError('invalid review authority')
            text = record['intent']['proposal']['objective'] if kind == 'intent' else record['context']['query']
            item.update(status='available', summary=redact_text(text)[:500], reviewed_at=record['reviewed_at'], reviewer=redact_text(record['reviewer'])[:200], reason=('Exact reviewed intent checked; no history selected and no work authority' if kind == 'intent' and record['intent']['review_filename'] is None else 'Exact review and current source history checked; no work authority'))
        except (OSError, ValueError, TaskHistoryError, KeyError, TypeError):
            pass
        reviews.append(item)
    return dict(schema_version='1.0', status='inspected', reviews=reviews, review_count=len(reviews), inventory_truncated=truncated, findings=findings, files_modified=False, model_called=False, approval_inferred=False, execution_performed=False)
