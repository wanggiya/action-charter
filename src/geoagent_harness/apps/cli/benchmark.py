"""Thin benchmark CLI over application runner and definition loader."""
import json
from pathlib import Path
import typer

from geoagent_harness.apps.benchmark.loader import load_suite
from geoagent_harness.apps.benchmark.runner import run_suite

app=typer.Typer(help='Validate and measure governed workflows using isolated benchmark fixtures.')


@app.command('list')
def list_tasks(project_root: Path=typer.Option(Path('.'),'--project-root')):
    try:
        typer.echo(json.dumps([{'id':t.task.id,'available':t.available,'expected':t.task.expected.kind} for t in load_suite(project_root)]))
    except (ValueError,OSError):
        typer.echo('Invalid or unavailable benchmark definitions.',err=True);raise typer.Exit(2)


@app.command('run')
def run(project_root: Path=typer.Option(Path('.'),'--project-root'),
        suite: str=typer.Option('v1','--suite'),fixture: bool=typer.Option(False,'--fixture'),
        profile: str=typer.Option('local','--profile'),task: str|None=typer.Option(None,'--task'),
        include_local_data: bool=typer.Option(False,'--include-local-data'),
        allow_fixture_writes: bool=typer.Option(False,'--allow-fixture-writes')):
    try:
        result,path=run_suite(project_root,fixture=fixture,profile=profile,task_id=task,suite=suite,
            include_local_data=include_local_data,allow_fixture_writes=allow_fixture_writes)
        typer.echo(json.dumps({'run_id':result['run_id'],'directory':str(path),'complete':result['complete'],
            'evidence_kind':result['evidence_kind'],'counts':result['counts'],'tasks':[{'id':r['task_id'],'status':r['status'],'reason':r['reason_code'],'critic':r['advisory_status']} for r in result['results']]}))
    except (ValueError,OSError):
        typer.echo('Benchmark configuration or storage failed; inspect saved run state before retrying.',err=True);raise typer.Exit(2)
    if not result['complete'] or any(r['status'] not in {'passed','skipped','unsupported'} for r in result['results']):raise typer.Exit(1)
