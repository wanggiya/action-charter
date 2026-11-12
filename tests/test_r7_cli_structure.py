"""R7 compatibility against pre-extraction commands; no live model or database."""
import ast
import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from typer.main import get_command
from typer.testing import CliRunner

from geoagent_harness import cli

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/architecture/r7_cli_contract.json').read_text())


def original_app():
    # P0-2b explicitly adds one offline command. Preserve the entire original
    # 150-command compatibility snapshot rather than replacing its golden hash.
    app = copy.copy(cli.app)
    app.registered_commands = [item for item in app.registered_commands if item.name != 'project-identity']
    return app


def normalize(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return {'path': str(value)}
    if isinstance(value, (list, tuple)):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    if hasattr(value, 'name'):
        return {'name': value.name, 'type': type(value).__qualname__}
    return {'type': type(value).__qualname__}


def command_contract(command):
    result = {key: normalize(getattr(command, key, None)) for key in (
        'name', 'help', 'short_help', 'epilog', 'hidden', 'deprecated',
        'no_args_is_help', 'invoke_without_command', 'context_settings')}
    result['params'] = []
    for parameter in command.params:
        item = {key: normalize(getattr(parameter, key, None)) for key in (
            'name', 'opts', 'secondary_opts', 'required', 'default', 'nargs',
            'multiple', 'is_flag', 'flag_value', 'count', 'help', 'metavar',
            'envvar', 'hidden', 'show_default', 'show_envvar', 'prompt',
            'prompt_required', 'confirmation_prompt', 'allow_from_autoenv')}
        item['type'] = {'class': type(parameter.type).__qualname__,
                        'name': parameter.type.name,
                        'choices': normalize(getattr(parameter.type, 'choices', None)),
                        'min': normalize(getattr(parameter.type, 'min', None)),
                        'max': normalize(getattr(parameter.type, 'max', None))}
        result['params'].append(item)
    result['commands'] = {name: command_contract(child) for name, child in
                          getattr(command, 'commands', {}).items()}
    return result


def test_all_command_names_order_parameters_and_defaults_match_before_extraction():
    assert 'project-identity' in get_command(cli.app).commands
    command = get_command(original_app())
    contract = command_contract(command)
    digest = hashlib.sha256(json.dumps(contract, separators=(',', ':')).encode()).hexdigest()
    assert len(command.commands) == FIXTURE['top_level_command_count'] == 150
    assert digest == FIXTURE['command_contract_sha256']


def test_every_help_screen_matches_before_extraction():
    runner = CliRunner()
    for name, expected in FIXTURE['help'].items():
        result = runner.invoke(original_app(), [*name.split(), '--help'],
                               env={'COLUMNS': '120', 'TERM': 'dumb', 'NO_COLOR': '1'},
                               terminal_width=120, color=False)
        assert result.exit_code == 0, (name, result.output, result.exception)
        assert hashlib.sha256(result.output.encode()).hexdigest() == expected, (name, result.output)
    assert len(FIXTURE['help']) == 165


def test_all_original_command_bodies_and_signatures_are_unchanged_and_public():
    for name, expected in FIXTURE['functions'].items():
        callback = inspect.unwrap(getattr(cli, name))
        definition = ast.parse(inspect.getsource(callback)).body[0]
        definition.decorator_list = []
        digest = hashlib.sha256(ast.dump(definition, include_attributes=False).encode()).hexdigest()
        assert digest == expected, name
        assert callback.__module__.startswith('geoagent_harness.apps.cli.'), name
    assert len(FIXTURE['functions']) == 110


def test_cli_modules_are_bounded_and_command_groups_do_not_import_each_other():
    directory = ROOT / 'src/geoagent_harness/apps/cli'
    for path in directory.rglob('*.py'):
        content = path.read_text()
        assert len(content.splitlines()) <= 1000, path
        if path.stem in {'main', 'registry', '__init__'}:
            continue
        for node in ast.walk(ast.parse(content)):
            if isinstance(node, ast.ImportFrom) and (node.module or '').startswith(
                    'geoagent_harness.apps.cli.'):
                assert node.module == 'geoagent_harness.apps.cli.common', path


def test_legacy_and_native_entrypoints_share_app_and_identical_help():
    from geoagent_harness.apps.cli.main import app
    assert cli.app is app
    outputs = []
    for module in ('geoagent_harness.cli', 'geoagent_harness.apps.cli.main'):
        result = subprocess.run([sys.executable, '-m', module, '--help'], cwd=ROOT,
                                capture_output=True, text=True, timeout=30,
                                env={**os.environ, 'COLUMNS': '120',
                                     'TERM': 'dumb', 'NO_COLOR': '1'})
        assert result.returncode == 0, result.stderr
        outputs.append(result.stdout)
    # Python's -m invocation appears in Usage; each entrypoint must retain its
    # own name. Compare content after normalizing only that name and padding.
    for index, module in enumerate(('geoagent_harness.cli', 'geoagent_harness.apps.cli.main')):
        assert module in outputs[index]
        outputs[index] = re.sub(r'[ \t]+', ' ', outputs[index].replace(module, 'geoagent'))
    assert outputs[0] == outputs[1]
