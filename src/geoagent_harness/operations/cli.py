"""Registered operation/library discovery and explicit package installation."""
from pathlib import Path
import json
import typer

def register(app):
    def emit(callback):
        try:typer.echo(json.dumps(callback(),indent=2))
        except (ValueError,OSError,RuntimeError) as error:
            from geoagent_harness.context_pack.redaction import redact_text
            typer.echo('Error: '+redact_text(str(error))[:1000],err=True);raise typer.Exit(2)

    @app.command('operations')
    def operations(project_root:Path=typer.Option(Path('.'),'--project-root'),query:str=typer.Option('','--query')):
        from .registry import operation_catalog
        emit(lambda:operation_catalog(project_root,query))

    @app.command('library-inventory')
    def libraries():
        from .discovery import library_inventory
        emit(library_inventory)

    @app.command('discover-libraries')
    def discover(project_root:Path=typer.Option(Path('.'),'--project-root'),distribution:list[str]=typer.Option([],'--distribution'),include_private:bool=typer.Option(False,'--include-private')):
        from .discovery import ScanRequest
        from .api import scan
        emit(lambda:scan(ScanRequest(distributions=distribution,include_private=include_private),project_root))

    @app.command('saved-library-scans')
    def saved(project_root:Path=typer.Option(Path('.'),'--project-root')):
        from .storage import saved_scans
        emit(lambda:saved_scans(project_root))

    @app.command('search-library-functions')
    def search(scan_sha:str=typer.Argument(),project_root:Path=typer.Option(Path('.'),'--project-root'),query:str=typer.Option('','--query'),distribution:str=typer.Option('','--distribution'),kind:str=typer.Option('','--kind'),offset:int=typer.Option(0,'--offset'),limit:int=typer.Option(50,'--limit')):
        from .storage import read_scan,candidate_page
        emit(lambda:candidate_page(read_scan(project_root,scan_sha),query,distribution,kind,offset,limit))

    def manifest(path):
        if path.is_symlink() or not path.is_file() or path.stat().st_size>64000:raise ValueError('Choose a regular bounded JSON package file')
        return json.loads(path.read_text())

    @app.command('test-operation-package')
    def test(path:Path=typer.Argument()):
        from .packages import test_package
        emit(lambda:test_package(manifest(path)))

    @app.command('install-operation-package')
    def install(path:Path=typer.Argument(),package_sha:str=typer.Option(...,'--package-sha'),confirm:bool=typer.Option(False,'--confirm-install'),project_root:Path=typer.Option(Path('.'),'--project-root')):
        from .packages import install_package
        emit(lambda:install_package(manifest(path),package_sha,root=project_root,confirm=confirm))
