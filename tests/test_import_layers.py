"""Known-good and regression fixtures for the static architecture gate; no app imports."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('actioncharter_import_layers', ROOT / 'scripts/check_import_layers.py')
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


@pytest.fixture
def project(tmp_path):
    policy_bytes = (ROOT / 'tests/architecture/import_layers_fixture_policy.json').read_bytes()
    (tmp_path / checker.POLICY).parent.mkdir(parents=True)
    (tmp_path / checker.POLICY).write_bytes(policy_bytes)
    write(tmp_path, '__init__.py', '')
    write(tmp_path, 'storage/__init__.py', '')
    write(tmp_path, 'planner/__init__.py', '')
    write(tmp_path, 'planner/schemas.py', 'class Plan: pass\n')
    return tmp_path, json.loads(policy_bytes), hashlib.sha256(policy_bytes).hexdigest()


def write(root, path, text):
    destination = root / 'src/geoagent_harness' / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text)
    return destination


def debt(result, digest):
    """Synthetic reviewed debt; production baseline is explicit versioned JSON."""
    counts = Counter((e.source, e.target, e.kind) for e in result['violations'])
    return {'schema_version': 1, 'policy_sha256': digest,
            'violations': [dict(source=s, target=t, kind=k, count=n,
                                reason='Known fixture violation', follow_up='fixture')
                           for (s, t, k), n in sorted(counts.items())],
            'dynamic_import_reviews': [dict(item, reason='Known fixture expression', follow_up='fixture')
                                       for item in result['dynamic_imports']]}


def test_repository_layer_debt_matches_reviewed_baseline():
    policy_path = ROOT / checker.POLICY
    result = checker.scan(ROOT, json.loads(policy_path.read_text()))
    baseline = json.loads((ROOT / checker.BASELINE).read_text())
    errors = checker.compare(result, baseline, hashlib.sha256(policy_path.read_bytes()).hexdigest())
    assert not errors, '\n'.join(errors)


def test_relative_child_alias_local_and_type_checking_imports(project):
    root, policy, _ = project
    write(root, 'storage/backend.py', '''
from typing import TYPE_CHECKING
import geoagent_harness.planner.schemas as plans
from ..planner import schemas as other_plans
from geoagent_harness import planner
if TYPE_CHECKING:
    from geoagent_harness.planner.schemas import Plan
def later():
    from ..planner.schemas import Plan as DelayedPlan
''')
    result = checker.scan(root, policy)
    assert [(e.target, e.line, e.kind) for e in result['violations']] == [
        ('geoagent_harness.planner', 5, 'from'),
        ('geoagent_harness.planner.schemas', 3, 'import'),
        ('geoagent_harness.planner.schemas', 4, 'from'),
        ('geoagent_harness.planner.schemas', 7, 'from'),
        ('geoagent_harness.planner.schemas', 9, 'from')]


def test_downward_same_layer_and_cli_adapter_imports_are_allowed(project):
    root, policy, _ = project
    write(root, 'planner/service.py', 'from ..planner.schemas import Plan\nfrom ..storage import backend\n')
    write(root, 'storage/backend.py', 'VALUE = 1\n')
    write(root, 'tabular/__init__.py', '')
    write(root, 'tabular/cli.py', 'from geoagent_harness.planner.schemas import Plan\n')
    result = checker.scan(root, policy)
    assert not result['violations']
    assert result['modules']['geoagent_harness.tabular.cli'] == 6


@pytest.mark.parametrize('extra', [
    'from ..planner.schemas import Plan\n',
    'from ..planner import service\n',
])
def test_new_edge_or_increased_occurrence_fails(project, extra):
    root, policy, digest = project
    path = write(root, 'storage/backend.py', 'from ..planner.schemas import Plan\n')
    write(root, 'planner/service.py', '')
    baseline = debt(checker.scan(root, policy), digest)
    path.write_text(path.read_text() + extra)
    assert any('NEW/INCREASED' in item for item in checker.compare(checker.scan(root, policy), baseline, digest))


def test_removed_edge_cannot_remain_as_a_future_allowance(project):
    root, policy, digest = project
    path = write(root, 'storage/backend.py', 'from ..planner.schemas import Plan\n')
    baseline = debt(checker.scan(root, policy), digest)
    path.write_text('')
    assert any('shrink the baseline' in item for item in checker.compare(checker.scan(root, policy), baseline, digest))


def test_two_imports_on_one_line_still_count_as_two_occurrences(project):
    root, policy, digest = project
    path = write(root, 'storage/backend.py', 'from ..planner.schemas import Plan\n')
    baseline = debt(checker.scan(root, policy), digest)
    path.write_text('from ..planner.schemas import Plan; from ..planner.schemas import Plan\n')
    result = checker.scan(root, policy)
    assert len(result['violations']) == 2
    assert any('NEW/INCREASED' in item for item in checker.compare(result, baseline, digest))


def test_scan_never_executes_sources_and_line_changes_do_not_expand_debt(project):
    root, policy, digest = project
    sentinel = root / 'executed'
    text = f'from pathlib import Path\nPath({str(sentinel)!r}).write_text("bad")\n'
    text += 'raise RuntimeError("Never execute this source")\nfrom ..planner.schemas import Plan\n'
    path = write(root, 'storage/backend.py', text)
    baseline = debt(checker.scan(root, policy), digest)
    path.write_text('\n\n' + text)
    assert not checker.compare(checker.scan(root, policy), baseline, digest)
    assert not sentinel.exists()


@pytest.mark.parametrize('path,text,match', [
    ('new_area.py', '', 'Unclassified'),
    ('storage/backend.py', 'import geoagent_harness.missing\n', 'unknown internal'),
    ('storage/backend.py', 'from ...planner import schemas\n', 'unknown internal|escapes'),
    ('storage/backend.py', 'this is invalid python !!!', 'invalid syntax'),
])
def test_unknown_modules_missing_targets_and_parse_errors_fail(project, path, text, match):
    root, policy, _ = project
    write(root, path, text)
    with pytest.raises((ValueError, SyntaxError), match=match):
        checker.scan(root, policy)


def test_literal_dynamic_imports_follow_the_same_layer_rules(project):
    root, policy, _ = project
    write(root, 'storage/backend.py', '''
import importlib as lib
from importlib import import_module as load
from builtins import __import__ as builtin_load
lib.import_module('geoagent_harness.planner.schemas')
load('..planner.schemas', __package__)
builtin_load('geoagent_harness.planner', fromlist=('schemas',))
''')
    result = checker.scan(root, policy)
    assert not result['dynamic_imports']
    assert len(result['violations']) == 4
    assert all(e.kind == 'dynamic-literal' for e in result['violations'])
    assert any(e.target == 'geoagent_harness.planner.schemas' and e.line == 7 for e in result['violations'])


def test_unresolved_dynamic_imports_require_expression_and_file_review(project):
    root, policy, digest = project
    path = write(root, 'storage/backend.py', 'from importlib import import_module\nimport_module(module_name)\n')
    result = checker.scan(root, policy)
    empty = debt({'violations': [], 'dynamic_imports': []}, digest)
    assert checker.compare(result, empty, digest)
    baseline = debt(result, digest)
    assert not checker.compare(result, baseline, digest)
    path.write_text(path.read_text() + '\nmodule_name = "geoagent_harness.planner"\n')
    assert checker.compare(checker.scan(root, policy), baseline, digest)


def test_compatibility_alias_is_visible_and_cannot_hide_reverse_import(project):
    root, policy, _ = project
    write(root, 'task_actions/__init__.py', '')
    write(root, 'task_actions/conversation.py', '')
    write(root, 'interface_api/__init__.py', '')
    write(root, 'interface_api/conversation.py', '''import sys
from geoagent_harness.task_actions import conversation as _implementation
sys.modules[__name__] = _implementation
''')
    write(root, 'storage/backend.py', 'from geoagent_harness.interface_api import conversation\n')
    result = checker.scan(root, policy)
    assert result['compatibility_modules'] == ['geoagent_harness.interface_api.conversation']
    assert [(e.source, e.target) for e in result['violations']] == [
        ('geoagent_harness.storage.backend', 'geoagent_harness.interface_api.conversation')]


def test_baseline_metadata_and_policy_edits_require_explicit_review(project):
    root, policy, digest = project
    write(root, 'storage/backend.py', 'from ..planner.schemas import Plan\n')
    result = checker.scan(root, policy)
    baseline = debt(result, digest)
    with pytest.raises(ValueError, match='policy digest mismatch'):
        checker.compare(result, baseline, 'changed-policy')
    baseline['violations'][0]['reason'] = ''
    with pytest.raises(ValueError, match='reason and follow-up'):
        checker.compare(result, baseline, digest)
    policy['modules']['geoagent_harness'] = 6
    with pytest.raises(ValueError, match='catch-all'):
        checker.scan(root, policy)


def test_check_and_strict_exit_modes_do_not_update_the_baseline(project, capsys):
    root, policy, digest = project
    write(root, 'storage/backend.py', 'from ..planner.schemas import Plan\n')
    baseline_path = root / checker.BASELINE
    baseline_path.write_text(json.dumps(debt(checker.scan(root, policy), digest)))
    before = baseline_path.read_bytes()
    assert checker.main(['--root', str(root), '--json']) == 0
    data = json.loads(capsys.readouterr().out)
    assert data['upward_dependencies'] == 1 and not data['errors']
    assert checker.main(['--root', str(root), '--strict']) == 1
    assert 'Strict exit gate' in capsys.readouterr().out
    assert baseline_path.read_bytes() == before


def test_strict_mode_passes_a_clean_graph_and_rejects_reviewed_unknown_imports(project, capsys):
    root, policy, digest = project
    baseline_path = root / checker.BASELINE
    baseline_path.write_text(json.dumps(debt(checker.scan(root, policy), digest)))
    assert checker.main(['--root', str(root), '--strict']) == 0
    capsys.readouterr()
    write(root, 'storage/backend.py', 'from importlib import import_module\nimport_module(requested)\n')
    baseline_path.write_text(json.dumps(debt(checker.scan(root, policy), digest)))
    assert checker.main(['--root', str(root)]) == 0
    capsys.readouterr()
    assert checker.main(['--root', str(root), '--strict']) == 1
    assert 'dynamic import debt remain' in capsys.readouterr().out
