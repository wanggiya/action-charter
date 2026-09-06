from typer.testing import CliRunner
from geoagent_harness.cli import app

def test_verify_postgis_rollback_command_is_registered():
    result=CliRunner().invoke(app,['--help'])
    assert result.exit_code==0
    assert 'verify-postgis-rollback' in result.stdout
