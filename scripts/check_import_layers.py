"""Static Phase 0 dependency check. Never import application modules or update debt."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys

PACKAGE = 'geoagent_harness'
ROOT = Path(__file__).resolve().parents[1]
POLICY = Path('tests/architecture/import_layers_policy.json')
BASELINE = Path('tests/architecture/import_layers_baseline.json')


@dataclass(frozen=True, order=True)
class Edge:
    source: str
    target: str
    line: int
    kind: str
    column: int = 0


def module_name(path: Path, package_root: Path) -> str:
    parts = list(path.relative_to(package_root).with_suffix('').parts)
    if parts[-1] == '__init__':
        parts.pop()
    return '.'.join([PACKAGE, *parts])


def layer_for(module: str, policy: dict) -> int:
    if module in policy['exact_modules']:
        return policy['exact_modules'][module]
    matches = [prefix for prefix in policy['modules']
               if module == prefix or module.startswith(prefix + '.')]
    if not matches:
        raise ValueError(f'Unclassified application module: {module}')
    return policy['modules'][max(matches, key=len)]


def relative_name(name: str, package: str, level: int) -> str:
    parts = package.split('.')
    if level > len(parts):
        raise ValueError('Relative import escapes the application package')
    base = '.'.join(parts[:len(parts) - level + 1])
    return base + ('.' + name if name else '')


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + '.' + node.attr
    return ''


def literal_string(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def compatibility_owners(root: Path) -> dict:
    """R6 is immutable history; R11 explicitly partitions retirement/public API."""
    historical = root / 'tests/architecture/r6_module_owners.json'
    if not historical.exists():
        return {}
    owners = json.loads(historical.read_text())
    partition_path = root / 'tests/architecture/r11_compatibility.json'
    if not partition_path.exists():
        return owners
    partition = json.loads(partition_path.read_text())
    if (partition.get('schema_version') != 1
            or partition.get('historical_sha256') != hashlib.sha256(historical.read_bytes()).hexdigest()):
        raise ValueError('R11 historical compatibility inventory changed')
    retained, retired = partition['retained'], partition['retired']
    if set(retained) & set(retired) or set(retained) | set(retired) != set(owners):
        raise ValueError('R11 must classify every historical adapter exactly once')
    for name, original in owners.items():
        record = retained.get(name, retired.get(name))
        if any(record.get(key) != value for key, value in original.items()):
            raise ValueError(f'R11 changed historical adapter identity: {name}')
        if name in retained and (not record.get('reasons') or not all(isinstance(r, str) and r.strip() for r in record['reasons'])):
            raise ValueError(f'R11 retained boundary needs evidence: {name}')
        if name in retired:
            path = root / 'src' / Path(*name.split('.'))
            path = path / '__init__.py' if original['package'] else path.with_suffix('.py')
            if not record.get('reason') or path.exists() or path.is_symlink():
                raise ValueError(f'R11 retired adapter remains or lacks justification: {name}')
    for name, digest in partition.get('preserved_contracts', {}).items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'R11 preserved contract changed; explicit review required: {name}')
    return retained


def scan(root: Path, policy: dict) -> dict:
    """Include local/conditional imports; resolve from-package children without execution."""
    if policy.get('schema_version') != 1:
        raise ValueError('Unsupported layer policy version')
    for prefix, layer in {**policy['modules'], **policy['exact_modules']}.items():
        if (not (prefix == PACKAGE or prefix.startswith(PACKAGE + '.'))
                or type(layer) is not int or not 0 <= layer <= 6):
            raise ValueError('Layer policy requires explicit internal module prefixes and levels 0–6')
    if PACKAGE in policy['modules']:
        raise ValueError('A catch-all application prefix would hide unclassified new packages')
    package_root = root / 'src' / PACKAGE
    paths = sorted(package_root.rglob('*.py'))
    if not paths:
        raise ValueError(f'No Python source under {package_root}')
    modules = {module_name(path, package_root): path for path in paths}
    if len(modules) != len(paths):
        raise ValueError('Ambiguous module and package paths')
    layers = {name: layer_for(name, policy) for name in modules}
    # R6 keeps historical paths as application compatibility adapters, never as
    # an exemption for live core/data code. Bind every adapter's reviewed bytes
    # and native owner; ordinary layer rules reject native imports of adapters.
    owners_path = root / 'tests/architecture/r6_module_owners.json'
    if owners_path.exists():
        owners = compatibility_owners(root)
        if (root / 'tests/architecture/r11_compatibility.json').exists():
            public_packages = [name for name, record in owners.items() if record['package']]
            hidden = [name for name in modules if name not in owners
                      and any(name.startswith(package + '.') for package in public_packages)]
            if hidden:
                raise ValueError(f'New implementation under retired compatibility namespace: {hidden}')
        for legacy, item in owners.items():
            if legacy not in modules or item['owner'] not in modules:
                raise ValueError(f'Compatibility adapter/owner is missing: {legacy}')
            if layers[legacy] != 6:
                raise ValueError(f'Compatibility adapter must be an application export: {legacy}')
            content = modules[legacy].read_bytes()
            if hashlib.sha256(content).hexdigest() != item['sha256']:
                raise ValueError(f'Compatibility adapter changed; review its delegation: {legacy}')
            tree = ast.parse(content)
            for node in tree.body:
                if isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef)) or (
                    isinstance(node, ast.FunctionDef) and node.name not in {'__getattr__', '__dir__'}
                ):
                    raise ValueError(f'Business logic is forbidden in compatibility adapters: {legacy}')
    edges: set[Edge] = set()
    dynamic: list[dict] = []
    compatibility: list[str] = []
    for source, path in modules.items():
        content = path.read_text(encoding='utf-8')
        tree = ast.parse(content, filename=str(path))
        nodes = list(ast.walk(tree))
        package = source if path.name == '__init__.py' else source.rpartition('.')[0]
        importers = {'__import__': 'builtin'}
        importlib_names: set[str] = set()
        builtins_names: set[str] = set()
        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'importlib':
                        importlib_names.add(alias.asname or alias.name)
                    if alias.name == 'builtins':
                        builtins_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom) and not node.level:
                for alias in node.names:
                    if node.module == 'importlib' and alias.name == 'import_module':
                        importers[alias.asname or alias.name] = 'importlib'
                    if node.module == 'builtins' and alias.name == '__import__':
                        importers[alias.asname or alias.name] = 'builtin'

        def add(target: str, node: ast.AST, kind: str) -> None:
            if target == PACKAGE or target.startswith(PACKAGE + '.'):
                if target not in modules:
                    raise ValueError(f'{source}:{node.lineno}: unknown internal import {target}')
                edges.add(Edge(source, target, node.lineno, kind, node.col_offset))

        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    add(alias.name, node, 'import')
            elif isinstance(node, ast.ImportFrom):
                base = relative_name(node.module or '', package, node.level) if node.level else node.module or ''
                targets = set()
                for alias in node.names:
                    child = base + '.' + alias.name
                    targets.add(child if child in modules else base)
                for target in sorted(targets):
                    add(target, node, 'from')
            elif isinstance(node, ast.Call):
                name = dotted(node.func)
                kind = importers.get(name)
                if name in {n + '.import_module' for n in importlib_names}:
                    kind = 'importlib'
                if name in {n + '.__import__' for n in builtins_names}:
                    kind = 'builtin'
                if kind is None:
                    continue
                keywords = {item.arg: item.value for item in node.keywords}
                target = literal_string(node.args[0] if node.args else keywords.get('name'))
                if target is not None and kind == 'importlib' and target.startswith('.'):
                    package_node = node.args[1] if len(node.args) > 1 else keywords.get('package')
                    explicit_package = literal_string(package_node)
                    if isinstance(package_node, ast.Name) and package_node.id == '__package__':
                        explicit_package = package
                    if isinstance(package_node, ast.Name) and package_node.id == '__name__':
                        explicit_package = source
                    if explicit_package:
                        level = len(target) - len(target.lstrip('.'))
                        target = relative_name(target[level:], explicit_package, level)
                    else:
                        target = None
                elif target is not None and kind == 'builtin':
                    level_node = node.args[4] if len(node.args) > 4 else keywords.get('level', ast.Constant(0))
                    if not isinstance(level_node, ast.Constant) or type(level_node.value) is not int:
                        target = None
                    elif level_node.value:
                        if level_node.value < 0:
                            raise ValueError(f'{source}:{node.lineno}: negative import level')
                        target = relative_name(target, package, level_node.value)
                    # __import__('pkg', fromlist=('child',)) also imports child modules.
                    fromlist = node.args[3] if len(node.args) > 3 else keywords.get('fromlist')
                    if fromlist is not None and target is not None:
                        try:
                            children = ast.literal_eval(fromlist)
                        except (ValueError, TypeError):
                            target = None
                        else:
                            if not isinstance(children, (tuple, list)) or not all(isinstance(c, str) for c in children):
                                target = None
                            else:
                                for child in children:
                                    if target + '.' + child in modules:
                                        add(target + '.' + child, node, 'dynamic-literal')
                if target is None:
                    dynamic.append({'source': source, 'expression': ast.dump(node, include_attributes=False),
                                    'source_sha256': hashlib.sha256(content.encode()).hexdigest()})
                else:
                    add(target, node, 'dynamic-literal')
            elif isinstance(node, ast.Assign):
                if any(isinstance(t, ast.Subscript) and dotted(t.value) == 'sys.modules'
                       and isinstance(t.slice, ast.Name) and t.slice.id == '__name__' for t in node.targets):
                    compatibility.append(source)
    violations = [edge for edge in sorted(edges) if layers[edge.target] > layers[edge.source]]
    return {'modules': layers, 'edges': sorted(edges), 'violations': violations,
            'dynamic_imports': dynamic, 'compatibility_modules': sorted(set(compatibility))}


def compare(scan_result: dict, baseline: dict, policy_sha256: str) -> list[str]:
    """Exact debt counts prevent a removed dependency from remaining permitted."""
    if baseline.get('schema_version') != 1 or baseline.get('policy_sha256') != policy_sha256:
        raise ValueError('Baseline version/policy digest mismatch; review the layer policy explicitly')
    expected: dict[tuple[str, str, str], int] = {}
    for item in baseline['violations']:
        key = (item['source'], item['target'], item['kind'])
        if key in expected or type(item['count']) is not int or item['count'] <= 0:
            raise ValueError('Duplicate or invalid baseline dependency')
        if not item.get('reason', '').strip() or not item.get('follow_up', '').strip():
            raise ValueError('Each baseline dependency needs a reason and follow-up task')
        expected[key] = item['count']
    actual = Counter((e.source, e.target, e.kind) for e in scan_result['violations'])
    errors = []
    for key in sorted(set(expected) | set(actual)):
        old, now = expected.get(key, 0), actual.get(key, 0)
        if now > old:
            errors.append(f'NEW/INCREASED upward dependency {key}: {old} -> {now}')
        elif now < old:
            errors.append(f'REMOVED/REDUCED debt {key}: {old} -> {now}; shrink the baseline')
    reviewed = []
    for item in baseline['dynamic_import_reviews']:
        if not item.get('reason', '').strip() or not item.get('follow_up', '').strip():
            raise ValueError('Dynamic import review needs a reason and follow-up')
        reviewed.append({k: item[k] for k in ('source', 'expression', 'source_sha256')})
    sort_key = lambda item: (item['source'], item['expression'], item['source_sha256'])
    if sorted(reviewed, key=sort_key) != sorted(scan_result['dynamic_imports'], key=sort_key):
        errors.append('Unreviewed/changed/stale dynamic import; review expression AND source digest')
    return errors


def report(result: dict, errors: list[str]) -> dict:
    counts = Counter((e.source, e.target, e.kind) for e in result['violations'])
    groups = Counter(f'L{result["modules"][e.source]} -> L{result["modules"][e.target]}' for e in result['violations'])
    return {'module_count': len(result['modules']), 'import_occurrences': len(result['edges']),
            'upward_dependencies': len(counts), 'upward_occurrences': len(result['violations']),
            'by_layer': dict(sorted(groups.items())),
            'dynamic_import_reviews': len(result['dynamic_imports']),
            'compatibility_modules': result['compatibility_modules'],
            'violations': [dict(source=e.source, target=e.target, line=e.line, column=e.column, kind=e.kind) for e in result['violations']],
            'errors': errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--json', action='store_true', help='Print measured dependencies and regression findings')
    parser.add_argument('--strict', action='store_true', help='Fail on all debt, including the recorded baseline')
    args = parser.parse_args(argv)
    try:
        policy_path = args.root / POLICY
        policy = json.loads(policy_path.read_text())
        baseline = json.loads((args.root / BASELINE).read_text())
        result = scan(args.root, policy)
        errors = compare(result, baseline, hashlib.sha256(policy_path.read_bytes()).hexdigest())
        if args.strict and (result['violations'] or result['dynamic_imports']):
            errors.append('Strict exit gate: upward dependencies/dynamic import debt remain')
        data = report(result, errors)
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
        if args.json:
            print(json.dumps({'errors': [str(error)]}, indent=2))
        else:
            print(f'Import layer check failed: {error}', file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f'{data["module_count"]} modules; {data["import_occurrences"]} internal import occurrences; '
              f'{data["upward_dependencies"]} recorded upward dependencies '
              f'({data["upward_occurrences"]} occurrences); '
              f'{data["dynamic_import_reviews"]} dynamic review(s).')
        status = ('FAILED' if errors else
                  'passed; remaining debt is NOT a clean layer exit' if result['violations'] or result['dynamic_imports']
                  else 'passed; native layer exit is clean')
        print('Baseline check: ' + status)
        for error in errors:
            print(error)
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
