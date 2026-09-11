from typer.testing import CliRunner

from geoagent_harness.cli import app


def test_publication_commands_are_registered():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in (
        "plan-geoserver-publication",
        "record-geoserver-publication-approval",
        "execute-geoserver-publication",
        "verify-geoserver-publication",
    ):
        assert name in result.stdout
