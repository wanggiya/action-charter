"""Agent-image startup must not import the optional GIS execution stack."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('arguments', [
    ['--help'],
    *[['agent-info', agent, '--agents-root', str(ROOT / 'agents')]
      for agent in ('planner', 'executor', 'critic')],
    ['recipe-template-catalog', '--project-root', str(ROOT)],
])
def test_agent_container_contract_without_gis_imports(arguments):
    # Fresh interpreters avoid success due to modules cached by earlier tests.
    script = '''
import importlib.abc
import sys

class NoGIS(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'geopandas', 'pyogrio', 'rasterio', 'shapely', 'pyproj'}:
            raise ModuleNotFoundError('Optional GIS dependency must not load: ' + fullname)

sys.meta_path.insert(0, NoGIS())
from typer.testing import CliRunner
from geoagent_harness.cli import app
assert 'geoagent_harness.interface_api.server' not in sys.modules
result = CliRunner().invoke(app, __import__('json').loads(sys.argv[1]))
print(result.output)
if result.exception:
    raise result.exception
assert result.exit_code == 0
assert 'geoagent_harness.interface_api.server' not in sys.modules
'''
    result = subprocess.run([sys.executable, '-c', script, json.dumps(arguments)],
                            cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
