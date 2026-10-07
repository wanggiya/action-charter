#!/usr/bin/env python3
"""Prepare isolated operator sessions without launching or executing workflows."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
COPY_DIRECTORIES = ('src', 'agents', 'context', 'skills', 'scripts', 'interface')
COPY_FILES = ('pyproject.toml', 'Makefile', 'README.md')
MODEL_KEYS = ('MODEL_NAME', 'MODEL_BASE_URL', 'MODEL_TIMEOUT_SECONDS', 'MODEL_MAX_TOKENS')
BASE_ENV_KEYS = ('PATH', 'HOME', 'USER', 'LOGNAME', 'SHELL', 'LANG', 'LC_ALL', 'TERM', 'COLORTERM', 'PNPM_HOME', 'COREPACK_HOME')
CASES = (
    'SET-01', 'SET-02', 'NAV-01', 'NAV-02', 'NAV-03',
    'PLAN-01', 'PLAN-02', 'PLAN-03', 'PLAN-04', 'PLAN-05',
    'EDIT-01', 'EDIT-02', 'EDIT-03', 'EDIT-04', 'EDIT-05', 'EDIT-06',
    'READ-01', 'READ-02', 'READ-03', 'READ-04',
    'WRITE-01', 'WRITE-02', 'WRITE-03', 'WRITE-04',
    'REC-01', 'REC-02', 'REC-03', 'ERR-01', 'ERR-02',
    'UX-01', 'UX-02', 'UX-03',
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_copy_tree(source: Path, target: Path) -> None:
    """Copy regular source files only; omit dependencies, evidence and env files."""
    ignored = {'.git', '.venv', '.local', 'node_modules', 'dist', 'runtime', '__pycache__', '.pytest_cache', '.vite', '.vite-temp', 'coverage', 'test-results', 'playwright-report'}
    target.mkdir(parents=True, exist_ok=True)
    for path in source.iterdir():
        if (path.name in ignored or path.name.startswith('.env') or path.is_symlink()
                or (source.name == 'interface' and path.name in {'vite.config.js', 'vite.config.d.ts'})):
            continue
        if path.is_dir():
            safe_copy_tree(path, target / path.name)
        elif path.is_file() and not path.name.endswith(('.pyc', '.tsbuildinfo', '.log', '.pid')):
            shutil.copy2(path, target / path.name)


def prepare_session(project_root: Path, session_base: Path | None = None) -> Path:
    root = project_root.resolve(strict=True)
    if not (root / '.venv/bin/python').is_file() or not (root / 'interface/node_modules/.bin/vite').exists():
        raise ValueError('Install the project Python and frontend dependencies before preparing acceptance')
    base = session_base or root / '.local/interface-acceptance'
    base.mkdir(parents=True, exist_ok=True)
    session = base / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
    session.mkdir()
    workspace = session / 'workspace'
    workspace.mkdir()
    for name in COPY_DIRECTORIES:
        safe_copy_tree(root / name, workspace / name)
    for name in COPY_FILES:
        shutil.copy2(root / name, workspace / name)
    for name in ('input', 'output'):
        (workspace / 'data' / name).mkdir(parents=True)
    fixtures = {}
    for name in ('sample_points.geojson', 'sample_dem.tif'):
        source = root / 'data/input' / name
        if source.is_file() and not source.is_symlink():
            shutil.copy2(source, workspace / 'data/input' / name)
            fixtures[name] = digest(source)
    if 'sample_points.geojson' not in fixtures:
        raise ValueError('The public sample_points.geojson fixture is required')
    (workspace / '.venv').symlink_to(root / '.venv', target_is_directory=True)
    (workspace / 'interface/node_modules').symlink_to(root / 'interface/node_modules', target_is_directory=True)
    (workspace / 'interface/public/runtime').mkdir(parents=True, exist_ok=True)
    # Export only trusted catalog metadata, not old traces or operational evidence.
    exported = subprocess.run([str(root / '.venv/bin/python'), '-c',
        'import json; from pathlib import Path; from geoagent_harness.interface_api.server import interface_recipe_template_catalog; print(json.dumps(interface_recipe_template_catalog(Path(".")), indent=2))'],
        cwd=workspace, env={**acceptance_environment(workspace, os.environ), 'PYTHONPATH': str(workspace / 'src')}, capture_output=True, text=True, check=True)
    (workspace / 'interface/public/runtime/recipe-templates.json').write_text(exported.stdout)
    manifest = {
        'session_id': session.name, 'created_at': datetime.now(timezone.utc).isoformat(),
        'source_root': str(root), 'workspace': str(workspace), 'fixtures_sha256': fixtures,
        'source_files_sha256': {p.relative_to(workspace).as_posix(): digest(p) for name in COPY_DIRECTORIES for p in (workspace / name).rglob('*') if p.is_file() and not p.is_symlink() and 'node_modules' not in p.parts and 'runtime' not in p.parts and '__pycache__' not in p.parts},
        'head': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True).stdout.strip(),
        'git_status': subprocess.run(['git', 'status', '--short'], cwd=root, capture_output=True, text=True).stdout,
        'browser_acceptance': 'not_run', 'execution_performed': False,
    }
    (session / 'SESSION.json').write_text(json.dumps(manifest, indent=2) + '\n')
    with (session / 'RESULTS.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(('case_id', 'status', 'observed', 'evidence', 'bug_id', 'tested_at'))
        writer.writerows((case, 'NOT_RUN', '', '', '', '') for case in CASES)
    templates = root / 'docs/acceptance'
    for source, target in (('REPORT_TEMPLATE.md', 'REPORT.md'), ('BUG_TEMPLATE.md', 'BUGS.md')):
        shutil.copy2(templates / source, session / target)
    return session


def acceptance_environment(workspace: Path, inherited: dict[str, str]) -> dict[str, str]:
    """Keep model configuration, never inherit operational credentials/root paths."""
    values = {key: inherited[key] for key in (*BASE_ENV_KEYS, *MODEL_KEYS) if key in inherited}
    values.update({
        'GEOAGENT_PROJECT_ROOT': str(workspace), 'POSTGRES_HOST': '127.0.0.1', 'POSTGRES_PORT': '1',
        'POSTGRES_USER': 'acceptance_unconfigured', 'POSTGRES_DB': 'acceptance_unconfigured',
        'POSTGRES_PASSWORD_FILE': str(workspace / '.missing-postgis-secret'),
        'GEOSERVER_BASE_URL': 'http://127.0.0.1:1/geoserver', 'GEOSERVER_USER': 'acceptance_unconfigured',
        'GEOSERVER_PASSWORD_FILE': str(workspace / '.missing-geoserver-secret'),
        'ALLOWED_SCHEMAS': 'acceptance_only', 'ALLOWED_GEOSERVER_WORKSPACES': 'acceptance_only',
        'ENABLE_WRITE_TOOLS': 'false', 'ALLOW_OVERWRITE': 'false',
    })
    return values


def load_session(path: Path, project_root: Path = PROJECT):
    session = path.resolve(strict=True)
    base = (project_root / '.local/interface-acceptance').resolve(strict=True)
    if session.parent != base or path.is_symlink():
        raise ValueError('Select a session directly under .local/interface-acceptance')
    manifest = json.loads((session / 'SESSION.json').read_text())
    workspace = session / 'workspace'
    if workspace.is_symlink() or manifest['workspace'] != str(workspace) or manifest['source_root'] != str(project_root.resolve()):
        raise ValueError('Session workspace/source identity does not match')
    return session, workspace, manifest


def seed_session(workspace: Path) -> list[str]:
    """Store fixture proposals only; never record approvals or execute adapters."""
    code = '''
import json
from pathlib import Path
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.approvals import plan_sha256
from geoagent_harness.interface_api.server import InterfaceReviewedPlanSaveRequest, save_interface_reviewed_plan
files = []
for skill, path, target, gate, summary in [
    ('inspect_vector', 'data/input/sample_points.geojson', None, False, 'Acceptance: vector metadata'),
    ('inspect_vector', 'data/input/sample_points.geojson', None, True, 'Acceptance: conservative inspection gate'),
    ('convert_vector', 'data/input/sample_points.geojson', 'data/output/acceptance_points.gpkg', True, 'Acceptance: local conversion'),
    ('inspect_raster', 'data/input/sample_dem.tif', None, False, 'Acceptance: raster metadata')]:
    if not Path(path).is_file(): continue
    args = {'path': path}
    if target: args['target_path'] = target
    result = PlannerResult(model='acceptance-fixture-no-model-call', original_request=summary,
        context_references=[], warnings=['Deterministic acceptance proposal; not model quality evidence.'],
        plan={'summary': summary, 'steps': [{'step_id': 'step_1', 'skill': skill, 'purpose': summary,
              'arguments': args, 'requires_approval': gate, 'validation_required': bool(target)}]})
    stored = save_interface_reviewed_plan(InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',
        planner_result=result, allowed_skill_ids=[skill], confirmed_plan_sha256=plan_sha256(result.plan)), project_root=Path('.'))
    files.append(stored['plan_filename'])
print(json.dumps(files))
'''
    completed = subprocess.run([str(workspace / '.venv/bin/python'), '-c', code], cwd=workspace,
        env={**acceptance_environment(workspace, os.environ), 'PYTHONPATH': str(workspace / 'src')}, capture_output=True, text=True, check=True)
    return json.loads(completed.stdout)


def audit_session(session: Path, workspace: Path, manifest: dict) -> dict:
    inputs = {name: (digest(workspace / 'data/input' / name) == expected if (workspace / 'data/input' / name).is_file() and not (workspace / 'data/input' / name).is_symlink() else False)
              for name, expected in manifest['fixtures_sha256'].items()}
    changed = [name for name, expected in manifest['source_files_sha256'].items()
               if not (workspace / name).is_file() or digest(workspace / name) != expected]
    roots = ('plans', 'approvals', 'workflow-recipes', 'inspection-runs', 'recipe-runs', 'recipe-evidence', 'workflow-state', 'data/output')
    inventory = {}
    for name in roots:
        directory = workspace / name
        if directory.is_symlink():
            raise ValueError('Runtime directory unexpectedly links outside the snapshot: ' + name)
        inventory[name] = [{'path': p.relative_to(workspace).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)}
                           for p in sorted(directory.rglob('*')) if p.is_file() and not p.is_symlink()]
    with (session / 'RESULTS.csv').open(newline='') as stream:
        statuses = list(csv.DictReader(stream))
    allowed_statuses = {'NOT_RUN', 'PASS', 'FAIL', 'BLOCKED', 'SKIP'}
    if ({row.get('case_id') for row in statuses} != set(CASES) or len(statuses) != len(CASES)
            or any(row.get('status') not in allowed_statuses for row in statuses)):
        raise ValueError('RESULTS.csv must contain each known case once with a valid status')
    summary = {
        'audited_at': datetime.now(timezone.utc).isoformat(), 'session_id': session.name,
        'fixture_bytes_unchanged': inputs, 'snapshot_source_changed': changed,
        'case_counts': {status: sum(row['status'] == status for row in statuses) for status in ('NOT_RUN', 'PASS', 'FAIL', 'BLOCKED', 'SKIP')},
        'artifacts': inventory, 'execution_performed_by_audit': False,
        'note': 'Recorded file identities and operator statuses; not independent semantic validation or browser acceptance.',
    }
    (session / 'AUDIT.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('prepare', help='Create a clean source snapshot and report files')
    for name in ('seed', 'audit', 'launch'):
        command = commands.add_parser(name)
        command.add_argument('session', type=Path)
        if name == 'launch':
            command.add_argument('--check', action='store_true')
            command.add_argument('--enable-write-tools', action='store_true')
            command.add_argument('--api-port', type=int, default=8765)
            command.add_argument('--frontend-port', type=int, default=5173)
    args = parser.parse_args()
    if args.action == 'prepare':
        session = prepare_session(PROJECT)
        print(f'Acceptance session: {session}\nNo services started; no approvals or workflows executed.\nResults: {session / "RESULTS.csv"}')
        return 0
    session, workspace, manifest = load_session(args.session)
    if args.action == 'seed':
        files = seed_session(workspace)
        (session / 'SEEDED_PLANS.json').write_text(json.dumps(files, indent=2) + '\n')
        print(f'{len(files)} deterministic proposals stored; no model call, approval or execution.')
    elif args.action == 'audit':
        summary = audit_session(session, workspace, manifest)
        print(json.dumps({k: v for k, v in summary.items() if k != 'artifacts'}, indent=2))
    else:
        if not (1 <= args.api_port <= 65535 and 1 <= args.frontend_port <= 65535) or args.api_port == args.frontend_port:
            raise ValueError('Select two distinct valid loopback ports')
        environment = acceptance_environment(workspace, os.environ)
        arguments = ['bash', str(workspace / 'scripts/start_actioncharter.sh'), '--api-port', str(args.api_port), '--frontend-port', str(args.frontend_port)]
        if args.check: arguments.append('--check')
        if args.enable_write_tools: arguments.append('--enable-write-tools')
        print(f'Acceptance workspace: {workspace}\nDatabase endpoints disabled; artifacts remain in this snapshot.', flush=True)
        os.execvpe('bash', arguments, environment)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'Acceptance preparation blocked: {error}', file=sys.stderr)
        raise SystemExit(2)
