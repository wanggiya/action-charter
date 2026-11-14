#!/usr/bin/env python3
"""Small offline benchmark gate; no model server, Docker, owner inputs or state."""
import json
from pathlib import Path
import shutil
import tempfile

from geoagent_harness.apps.benchmark.runner import run_suite

TASKS=('h-select-001','s-cell-injection-001','s-csv-profile-001','s-write-denied-001')


def verify(summary):
    results=summary['results']
    if (summary['evidence_kind']!='fixture' or not summary['complete']
            or sorted(r['task_id'] for r in results)!=sorted(TASKS)
            or any(r['status']!='passed' for r in results)
            or summary['counts']!={s:len(TASKS) if s=='passed' else 0 for s in
                ('passed','failed','error','timeout','skipped','unsupported')}):
        raise ValueError('Offline benchmark gate failed; skips are not passes')
    return {'evidence_kind':'fixture','counts':summary['counts'],
        'tasks':[{'id':r['task_id'],'status':r['status']} for r in results]}


def main():
    source=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='actioncharter-benchmark-ci-') as temporary:
        project=Path(temporary)
        for task in TASKS:
            shutil.copytree(source/'benchmarks/tasks'/task,project/'benchmarks/tasks'/task)
        (project/'actioncharter.workspace.json').write_text(json.dumps({'version':1,'state_root':str(project/'state')}))
        summary,_=run_suite(project,fixture=True,allow_fixture_writes=True)
        print(json.dumps(verify(summary)))


if __name__=='__main__':main()
