"""Read-only, content-free benchmark reports; no prompts or endpoint export."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import platform
import re

from geoagent_harness.contracts.benchmark import BenchmarkResult, BenchmarkRunContext
from geoagent_harness.platform.storage.files import FileJsonRecords
from geoagent_harness.platform.workspace import runtime_store_path

STATUSES=('passed','failed','error','timeout','skipped','unsupported')
PACKAGES=('pandas','numpy','scipy','pydantic','httpx','psycopg','rasterio','pyogrio','shapely','pyyaml')


def source_sha256(root):
    """Bind runtime source, staged context, manifests and the fixed suite, not secrets."""
    root=Path(root)
    files=list((root/'src/geoagent_harness').rglob('*.py'))
    for tree in ('agents','benchmarks/tasks'):
        files.extend(p for p in (root/tree).rglob('*') if p.is_file())
    files.extend(root/p for p in ('pyproject.toml','context/ARCHITECTURE.md',
        'context/SKILLS_INDEX.yaml','context/DECISIONS.jsonl'))
    manifest=[]
    for path in sorted(set(files)):
        if path.is_symlink() or not path.is_file():raise ValueError('Unsafe source provenance input')
        manifest.append([path.relative_to(root).as_posix(),hashlib.sha256(path.read_bytes()).hexdigest()])
    return hashlib.sha256(json.dumps(manifest,separators=(',',':')).encode()).hexdigest()


def run_context(root, tasks, settings, *, allow_fixture_writes, disposable_database, include_local_data):
    versions={}
    for name in PACKAGES:
        try:versions[name]=version(name)
        except PackageNotFoundError:pass
    configuration=None if settings is None else {k:getattr(settings,k) for k in
        ('timeout_seconds','max_tokens','reasoning_effort','response_format')}
    return BenchmarkRunContext(started_at=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        task_ids=[t.task.id for t in tasks],source_sha256=source_sha256(root),
        python_version=platform.python_version(),package_versions=versions,model_configuration=configuration,
        allow_fixture_writes=allow_fixture_writes,disposable_database=disposable_database,
        include_local_data=include_local_data).model_dump(mode='json')


def build_report(project_root, run_id):
    if not re.fullmatch('[a-f0-9]{32}',run_id):raise ValueError('Invalid benchmark run identity')
    store=FileJsonRecords(runtime_store_path(Path(project_root).resolve(),'benchmark-runs')/run_id,max_bytes=8*1024*1024)
    summary=store.read('summary.json')
    required={'schema_version','run_id','evidence_kind','results','complete','counts'}
    if not required<=summary.keys() or summary.keys()-required-{'context','source_unchanged'}:
        raise ValueError('Invalid benchmark summary')
    if summary['schema_version']!='1.0' or summary['run_id']!=run_id or type(summary['complete']) is not bool:
        raise ValueError('Invalid benchmark summary identity')
    if not isinstance(summary['results'],list) or not 1<=len(summary['results'])<=256:
        raise ValueError('Invalid benchmark result inventory')
    records=[BenchmarkResult.model_validate(r) for r in summary['results']]
    ids=[r.task_id for r in records]
    if len(set(ids))!=len(ids) or any(r.run_id!=run_id or r.evidence_kind!=summary['evidence_kind'] for r in records):
        raise ValueError('Mismatched benchmark results')
    counts={s:sum(r.status==s for r in records) for s in STATUSES}
    if summary['counts']!=counts:raise ValueError('Mismatched benchmark counts')
    for record in records:
        if BenchmarkResult.model_validate(store.read(record.task_id+'.json'))!=record:
            raise ValueError('Mismatched task record')
    context=None;unchanged=None
    if 'context' in summary:
        context=BenchmarkRunContext.model_validate(summary['context']).model_dump(mode='json')
        started=store.read('started.json')
        unchanged=summary.get('source_unchanged')
        if type(unchanged) is not bool or started.get('context')!=context or started.get('run_id')!=run_id:
            raise ValueError('Mismatched benchmark context')
        if any(task not in context['task_ids'] for task in ids) or (summary['complete'] and ids!=context['task_ids']):
            raise ValueError('Mismatched task scope')
    def total(key):
        values=[getattr(r.metrics,key) for r in records]
        return sum(values) if all(v is not None for v in values) else None
    coverage={}
    for key in ('prompt_tokens','completion_tokens'):
        values=[getattr(r.metrics,key) for r in records if getattr(r.metrics,key) is not None]
        coverage[key]={'reported_sum':sum(values) if values else None,'tasks_reported':len(values),
            'tasks_with_calls':sum(r.metrics.model_calls>0 for r in records)}
    roles={}
    for role in sorted({v.role for r in records for v in r.metrics.roles}):
        entries=[v for r in records for v in r.metrics.roles if v.role==role]
        roles[role]={key:sum(getattr(v,key) for v in entries) if all(getattr(v,key) is not None for v in entries) else None
            for key in ('model_calls','prompt_tokens','completion_tokens','elapsed_seconds')}
    return {'schema_version':'1.0','run_id':run_id,'evidence_kind':summary['evidence_kind'],
        'complete':summary['complete'],'counts':counts,'context':context,'source_unchanged':unchanged,
        'totals':{k:total(k) for k in ('model_calls','prompt_tokens','completion_tokens','wall_seconds',
            'process_cpu_seconds','retries','timeouts','approvals_required')},'roles':roles,
        'usage_coverage':coverage,
        'critic_counts':dict(sorted(Counter(r.advisory_status for r in records).items())),
        'results':[r.model_dump(mode='json') for r in records]}


def markdown_report(report):
    def label(value):
        # Model names/identifiers are metadata, never raw model or dataset text.
        return str(value).replace('|','\\|').replace('`','').replace('\n',' ').replace('\r',' ')
    lines=['# ActionCharter benchmark baseline','',f"Evidence: **{report['evidence_kind']}**; complete: **{str(report['complete']).lower()}**.",
        f"Run: `{report['run_id']}`.",'',
        'Counts: '+', '.join(f'{s}={report["counts"][s]}' for s in STATUSES)+'.','']
    context=report['context']
    if context:
        lines += [f"Started: {context['started_at']}. Python: {context['python_version']}.",
            f"Source SHA-256: `{context['source_sha256']}`; unchanged during run: **{str(report['source_unchanged']).lower()}**.",
            'Model configuration: `'+json.dumps(context['model_configuration'],sort_keys=True)+'`.',
            'Runtime options: '+', '.join(f'{k}={str(context[k]).lower()}' for k in ('allow_fixture_writes','disposable_database','include_local_data'))+'.','']
    else:lines+=['Legacy run: model settings/source fingerprint were not recorded.','']
    totals=report['totals']
    lines+=['Totals: '+', '.join(f'{k}={v if v is not None else "unknown"}' for k,v in totals.items())+'.',
        'Reported usage (partial sums, not inferred totals): `'+json.dumps(report['usage_coverage'],sort_keys=True)+'`.','',
        '| Task | Status | Reason | Model | Calls | Seconds | Critic |',
        '|---|---|---|---|---:|---:|---|']
    for record in report['results']:
        m=record['metrics']
        lines.append('| '+' | '.join(map(label,[record['task_id'],record['status'],record['reason_code'],record['model'],m['model_calls'],f"{m['wall_seconds']:.2f}",record['advisory_status']]))+' |')
    lines+=['','Skipped and unsupported cases are not capability passes. Critic assessment is separate from deterministic scores.',
        'Reported tokens may be unknown; CPU and sampled worker RSS exclude model/GPU memory. Fixture calls are logical calls, not model measurements.',
        'This report omits prompts, data values, endpoint addresses, credentials and private workspace paths.',
        'Source/task hashes identify measured bytes; a dirty checkout is not an immutable released revision. No learning or performance improvement is inferred.','']
    return '\n'.join(lines)
