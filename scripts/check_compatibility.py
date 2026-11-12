"""Read-only R11 source/contract audit. Never inspect runtime data or import agents."""
import argparse
import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.check_import_layers import compatibility_owners, scan

PUBLIC_TESTS = frozenset({
    'tests/test_r6_layer_ownership.py', 'tests/test_r7_cli_structure.py',
    'tests/test_r8_http_structure.py', 'tests/test_platform_configuration.py',
})


def legacy_imports(content, historical):
    """Detect qualified/from-child imports, including literal dynamic imports."""
    found = []
    for node in ast.walk(ast.parse(content)):
        names = []
        if isinstance(node, ast.Import):
            names = [item.name for item in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            base = node.module or ''
            names = [base + '.' + item.name if base + '.' + item.name in historical else base
                     for item in node.names]
        elif isinstance(node, ast.Call):
            method = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ''
            if method in {'import_module', '__import__'} and node.args and isinstance(node.args[0], ast.Constant):
                if isinstance(node.args[0].value, str):
                    names = [node.args[0].value]
        found.extend((name, node.lineno) for name in names if name in historical)
    return found


def audit(root=ROOT):
    root = Path(root)
    partition = json.loads((root / 'tests/architecture/r11_compatibility.json').read_text())
    retained = compatibility_owners(root)
    historical = set(retained) | set(partition['retired'])
    policy = json.loads((root / 'tests/architecture/import_layers_policy.json').read_text())
    graph = scan(root, policy)
    errors = []
    for edge in graph['edges']:
        if edge.source not in retained and edge.target in retained:
            errors.append(f'Native caller uses compatibility module: {edge.source} -> {edge.target}')
    for name in set(graph['compatibility_modules']) - set(retained):
        errors.append(f'Unclassified compatibility alias: {name}')
    for directory in ('tests', 'scripts', 'docker'):
        for path in sorted((root / directory).rglob('*.py')):
            relative = path.relative_to(root).as_posix()
            if relative in PUBLIC_TESTS or '__pycache__' in path.parts:
                continue
            for name, line in legacy_imports(path.read_text(), historical):
                # The isolated candidate loader deliberately provisions this SDK
                # namespace; it must not shadow native trusted implementation code.
                if relative == 'docker/skill-test-runner/run_candidate_tests.py' and name in {
                    'geoagent_harness.skills', 'geoagent_harness.skill_adapters',
                }:
                    continue
                errors.append(f'{relative}:{line}: use native owner instead of {name}')
    if graph['violations'] or graph['dynamic_imports']:
        errors.append('Native import layers contain upward or dynamic debt')
    return {'retired': len(partition['retired']), 'retained_public': len(retained),
            'native_modules': len(graph['modules']) - len(retained),
            'modules': len(graph['modules']), 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = audit(args.root)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'Compatibility audit failed: {error}\n')
    print(json.dumps(result, indent=2))
    return int(bool(result['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
