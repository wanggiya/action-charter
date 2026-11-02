"""Read-only CLI parity; writes use the existing governed recipe/chat commands."""
import json
from pathlib import Path
import typer
from .service import inspect, effects
from geoagent_harness.mcp_server.settings import load_settings

def install(app):
    group=typer.Typer(help='Inspect PostgreSQL through the shared typed service; writes use authorized workflows.')
    app.add_typer(group,name='postgres')
    @group.command('discover')
    def discover(schema:str=typer.Option('agent_sandbox','--schema'),project_root:Path=typer.Option(Path('.'),'--project-root')):
        _show('discover_postgres_tables',{'target_schema':schema},project_root)
    @group.command('inspect')
    def inspect_table(table:str,schema:str=typer.Option('agent_sandbox','--schema'),preview_rows:int=typer.Option(5,'--preview-rows'),project_root:Path=typer.Option(Path('.'),'--project-root')):
        _show('inspect_postgres_table',{'target_schema':schema,'target_table':table,'preview_rows':preview_rows},project_root)
    @group.command('preflight')
    def preflight(arguments:Path,project_root:Path=typer.Option(Path('.'),'--project-root')):
        """Validate complete mapped source without database writes; workflows bind ancestors."""
        try:_show('validate_postgres_import',json.loads(arguments.read_text()),project_root)
        except (ValueError,OSError):typer.echo('Invalid preflight argument file',err=True);raise typer.Exit(2)
    @group.command('effects')
    def review(operation:str,arguments:Path):
        """Show effects of a JSON argument file; no connection, approval or execution."""
        try:typer.echo(json.dumps(effects(operation,json.loads(arguments.read_text())),indent=2))
        except (ValueError,KeyError,OSError):
            typer.echo('Invalid operation argument file',err=True);raise typer.Exit(2)

def _show(skill,args,root):
    try:typer.echo(json.dumps(inspect(skill,args,load_settings().model_copy(update={'project_root':root.resolve()})),indent=2))
    except (ValueError,OSError) as error:
        typer.echo(str(error),err=True);raise typer.Exit(2) from error
