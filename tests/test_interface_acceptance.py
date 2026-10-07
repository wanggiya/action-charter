"""Acceptance preparation isolates source snapshots, credentials and evidence."""
import importlib.util
import json
import os
from pathlib import Path
from shutil import copyfile

import pytest

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('interface_acceptance', PROJECT / 'scripts/interface_acceptance.py')
acceptance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acceptance)


@pytest.fixture
def source(tmp_path):
    root = tmp_path / 'source'
    root.mkdir()
    for name in acceptance.COPY_DIRECTORIES:
        (root / name).mkdir()
    for name in acceptance.COPY_FILES:
        (root / name).write_text('acceptance fixture source\n')
    (root / '.venv').symlink_to(PROJECT / '.venv', target_is_directory=True)
    (root / 'interface/node_modules/.bin').mkdir(parents=True)
    (root / 'interface/node_modules/.bin/vite').write_text('dependency sentinel')
    (root / 'context/SKILLS_INDEX.yaml').write_text((PROJECT / 'context/SKILLS_INDEX.yaml').read_text())
    (root / 'context/RECIPE_TEMPLATES.yaml').write_text((PROJECT / 'context/RECIPE_TEMPLATES.yaml').read_text())
    (root / 'data/input').mkdir(parents=True)
    copyfile(PROJECT / 'data/input/sample_points.geojson', root / 'data/input/sample_points.geojson')
    (root / 'data/input/private.geojson').write_text('private data should not enter acceptance')
    (root / 'plans').mkdir()
    (root / 'plans/private-plan.json').write_text('private runtime evidence')
    (root / 'interface/.env.local').write_text('PRIVATE_KEY=do-not-copy')
    (root / 'src/working-change.py').write_text('uncommitted_change = True\n')
    (root / 'src/private-link').symlink_to(root / 'data/input/private.geojson')
    (root / 'docs/acceptance').mkdir(parents=True)
    for name in ('REPORT_TEMPLATE.md', 'BUG_TEMPLATE.md'):
        copyfile(PROJECT / 'docs/acceptance' / name, root / 'docs/acceptance' / name)
    return root


def test_prepare_copies_current_source_and_public_fixtures_without_authority(source):
    session = acceptance.prepare_session(source)
    workspace = session / 'workspace'
    assert (workspace / 'src/working-change.py').read_text() == 'uncommitted_change = True\n'
    assert not (workspace / 'src/private-link').exists()
    assert not (workspace / 'interface/.env.local').exists()
    assert not (workspace / 'data/input/private.geojson').exists()
    assert not (workspace / 'plans').exists()
    assert not (workspace / 'approvals').exists()
    assert not list((workspace / 'data/output').iterdir())
    manifest = json.loads((session / 'SESSION.json').read_text())
    assert manifest['execution_performed'] is False
    assert manifest['browser_acceptance'] == 'not_run'
    assert 'src/working-change.py' in manifest['source_files_sha256']
    assert (workspace / '.venv').resolve() == (source / '.venv').resolve()
    assert len((session / 'RESULTS.csv').read_text().splitlines()) == len(acceptance.CASES) + 1
    assert (workspace / 'interface/public/runtime/recipe-templates.json').is_file()


def test_launch_environment_does_not_inherit_credentials_authority_or_external_roots(tmp_path):
    inherited = {'PATH': '/usr/bin', 'MODEL_NAME': 'fixture-model', 'MODEL_BASE_URL': 'http://127.0.0.1:11434/v1',
                 'POSTGRES_HOST': 'live-postgis', 'POSTGRES_PASSWORD_FILE': '/live/secret',
                 'GEOSERVER_BASE_URL': 'https://live.example', 'GEOAGENT_OUTPUT_ROOT': '/live/data',
                 'AWS_SECRET_ACCESS_KEY': 'private', 'ENABLE_WRITE_TOOLS': 'true', 'ALLOW_OVERWRITE': 'true'}
    env = acceptance.acceptance_environment(tmp_path, inherited)
    assert env['MODEL_NAME'] == 'fixture-model'
    assert env['POSTGRES_HOST'] == '127.0.0.1' and env['POSTGRES_PORT'] == '1'
    assert env['GEOSERVER_BASE_URL'] == 'http://127.0.0.1:1/geoserver'
    assert env['ENABLE_WRITE_TOOLS'] == 'false' and env['ALLOW_OVERWRITE'] == 'false'
    assert 'AWS_SECRET_ACCESS_KEY' not in env and 'GEOAGENT_OUTPUT_ROOT' not in env
    assert env['POSTGRES_PASSWORD_FILE'].startswith(str(tmp_path))


def test_seed_is_repeatable_and_creates_only_proposals(source):
    session = acceptance.prepare_session(source)
    workspace = session / 'workspace'
    first = acceptance.seed_session(workspace)
    second = acceptance.seed_session(workspace)
    assert first == second and len(first) == 3
    assert len(list((workspace / 'plans').glob('*.json'))) == 3
    assert not (workspace / 'approvals').exists()
    assert not (workspace / 'inspection-runs').exists()
    assert not list((workspace / 'data/output').iterdir())
    for file in first:
        record = json.loads((workspace / 'plans' / file).read_text())
        assert record['model'] == 'acceptance-fixture-no-model-call'
        assert not record['plan']['execution_performed']


def test_audit_detects_source_and_fixture_changes_without_marking_acceptance_passed(source):
    session = acceptance.prepare_session(source)
    _, workspace, manifest = acceptance.load_session(session, source)
    (workspace / 'src/working-change.py').write_text('changed after snapshot\n')
    (workspace / 'data/input/sample_points.geojson').write_text('changed fixture\n')
    audit = acceptance.audit_session(session, workspace, manifest)
    assert audit['fixture_bytes_unchanged']['sample_points.geojson'] is False
    assert 'src/working-change.py' in audit['snapshot_source_changed']
    assert audit['case_counts']['PASS'] == 0
    assert audit['case_counts']['NOT_RUN'] == len(acceptance.CASES)
    assert audit['execution_performed_by_audit'] is False
    assert (source / 'src/working-change.py').read_text() == 'uncommitted_change = True\n'


def test_load_refuses_workspace_redirect_and_foreign_session(source):
    session = acceptance.prepare_session(source)
    with pytest.raises(ValueError, match='directly under'):
        acceptance.load_session(source, source)
    manifest_path = session / 'SESSION.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['workspace'] = '/live/workspace'
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='identity'):
        acceptance.load_session(session, source)


def test_audit_refuses_symlinked_runtime_root(source):
    session = acceptance.prepare_session(source)
    _, workspace, manifest = acceptance.load_session(session, source)
    (workspace / 'plans').symlink_to(source / 'plans', target_is_directory=True)
    with pytest.raises(ValueError, match='links outside'):
        acceptance.audit_session(session, workspace, manifest)
