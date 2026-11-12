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
    script = "\nimport importlib.abc\nimport sys\n\nclass NoGIS(importlib.abc.MetaPathFinder):\n    def find_spec(self, fullname, path=None, target=None):\n        if fullname.split('.')[0] in {'geopandas', 'pyogrio', 'rasterio', 'shapely', 'pyproj'}:\n            raise ModuleNotFoundError('Optional GIS dependency must not load: ' + fullname)\n\nsys.meta_path.insert(0, NoGIS())\nfrom typer.testing import CliRunner\nfrom geoagent_harness.apps.cli.main import app\nassert 'geoagent_harness.interface_api.server' not in sys.modules\nresult = CliRunner().invoke(app, __import__('json').loads(sys.argv[1]))\nprint(result.output)\nif result.exception:\n    raise result.exception\nassert result.exit_code == 0\nassert 'geoagent_harness.interface_api.server' not in sys.modules\n"
    result = subprocess.run([sys.executable, '-c', script, json.dumps(arguments)],
                            cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
