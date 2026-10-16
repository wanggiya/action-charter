"""CLI adapter for the same non-executing method-memory service as the UI."""
from pathlib import Path
import json
import typer


def register(app):
    @app.command('method-memory')
    def command(request_file: Path | None = typer.Option(None, '--request-file'),
                project_root: Path = typer.Option(Path('.'), '--project-root')):
        from .method_memory import MethodRequest, method_action
        from .server import InterfaceApiError
        from geoagent_harness.model import ModelClientError, ModelSettingsError
        from geoagent_harness.context_pack.redaction import redact_text
        try:
            if request_file is not None:
                if request_file.is_symlink() or not request_file.is_file() or request_file.stat().st_size > 64000:
                    raise ValueError('Choose a regular method request JSON file under 64 KB')
                request = MethodRequest.model_validate_json(request_file.read_text())
            else:
                request = MethodRequest(action='state')
            typer.echo(json.dumps(method_action(request, project_root=project_root), indent=2))
        except (ValueError, OSError, InterfaceApiError, ModelClientError, ModelSettingsError) as error:
            # Validation errors can contain original source values; do not echo them.
            message = str(error) if isinstance(error, (InterfaceApiError, ModelClientError, ModelSettingsError)) else 'Method request failed its typed or file bounds'
            typer.echo('Error: ' + redact_text(message)[:1000], err=True)
            raise typer.Exit(2)
