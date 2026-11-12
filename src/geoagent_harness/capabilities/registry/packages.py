"""Data-only packages bind one trusted adapter; no package code is imported."""
from __future__ import annotations
import json
import os
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory

from geoagent_harness.contracts.text_transform import TextTransform
from geoagent_harness.contracts.table_arguments import Source
from geoagent_harness.contracts.operation_packages import PackageError, ProjectionArguments, Fixture, OperationPackage, canonical, package_sha, configuration, parse_package, ADAPTER_ENTRYPOINT, VERIFIER, DIRECTORY, MAX_BYTES
from geoagent_harness.platform.storage.operation_packages import _directory, installed_packages, package_skills


def test_package(value, *, timeout_seconds=20):
    package=parse_package(value)
    if package.adapter=='csv_text_transform':
        from geoagent_harness.capabilities.testing import test_text_package
        return test_text_package(package,timeout_seconds=timeout_seconds)
    from geoagent_harness.platform.settings import load_settings
    from geoagent_harness.data.tabular.service import read_frame, run_operation, validate_output
    package=parse_package(value)
    from importlib.metadata import version
    if version('pandas')!='3.0.5':raise PackageError('This adapter requires the declared pandas 3.0.5 runtime; installing a package does not install dependencies')
    results=[]
    for fixture in package.tests:
        with TemporaryDirectory(prefix='actioncharter-adapter-test-') as temporary:
            root=Path(temporary);(root/'data/input').mkdir(parents=True)
            (root/'data/input/fixture.csv').write_text(fixture.csv)
            settings=load_settings({}).model_copy(update={'project_root':root,'enable_write_tools':True,'allow_overwrite':False})
            outcome=run_operation('select_csv_columns',{'path':'data/input/fixture.csv','columns':package.columns,'target_path':'data/output/result.csv'},settings)
            expected=read_frame(fixture.expected_csv.encode())
            actual=read_frame((root/'data/output/result.csv').read_bytes())
            results.append({'passed':actual.equals(expected) and validate_output(outcome,settings)['passed'],'row_count':len(actual),'columns':list(actual.columns)})
    return {'package_sha256':package_sha(package),'package_id':package.id,'passed':all(r['passed'] for r in results),'cases':results,'scope':'temporary_fixtures_only','dependency_installed':False,'approval_performed':False,'execution_performed':False,'fixture_execution_performed':True}

def install_package(value, digest, *, root, confirm=False):
    package=parse_package(value)
    if not confirm or package_sha(package)!=digest:raise PackageError('Explicit installation and exact tested package digest required')
    current=installed_packages(root)
    if package.id in current:
        if package_sha(current[package.id])!=digest:raise PackageError('Operation ID already installed with different content')
        return {'id':package.id,'status':'already_installed','package_sha256':digest,'approval_performed':False,'execution_performed':False}
    if len(current)>=20:raise PackageError('Installed package limit reached; no dependency or package was installed')
    report=test_package(package.model_dump())
    if not report['passed']:raise PackageError('Package fixture tests failed')
    content=json.dumps({'package':package.model_dump(mode='json'),'package_sha256':digest},sort_keys=True,separators=(',',':')).encode()
    if len(content)>MAX_BYTES:raise PackageError('Installed record exceeds its bound')
    try:
        with ExitStack() as stack:
            parent=_directory(stack,root,create=True)
            import fcntl
            fcntl.flock(parent,fcntl.LOCK_EX)
            current=installed_packages(root)
            if package.id in current or len(current)>=20:
                raise PackageError('Package registry changed during testing; reload before installing')
            import uuid
            name=f'{package.id}.json';temporary=f'.package.{uuid.uuid4().hex}.tmp'
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            try:
                with os.fdopen(fd,'wb') as handle:handle.write(content);handle.flush();os.fsync(handle.fileno())
                os.link(temporary,name,src_dir_fd=parent,dst_dir_fd=parent,follow_symlinks=False)
                os.fsync(parent)
            finally:os.unlink(temporary,dir_fd=parent)
    except OSError as error:raise PackageError('Package installation failed; existing records were not replaced') from error
    return {'id':package.id,'status':'installed','package_sha256':digest,'approval_performed':False,'execution_performed':False,'dependency_installed':False,
        **({'test_report':report,'fixture_batches':1} if package.adapter=='csv_text_transform' else {})}

def execute_projection(skill, arguments, settings, completed_results=None):
    from geoagent_harness.data.tabular.service import run_operation
    from geoagent_harness.contracts.paths import TabularError
    args=ProjectionArguments.model_validate(arguments)
    from geoagent_harness.data.tabular.service import pd
    if pd.__version__!='3.0.5':raise TabularError('Installed adapter runtime does not match pandas 3.0.5')
    package=installed_packages(settings.project_root).get(skill)
    if package is None or package_sha(package)!=args.package_sha256:
        raise TabularError('Installed adapter is missing or differs from the exact approved package digest')
    if package.adapter=='csv_text_transform':
        from geoagent_harness.data.tabular.text import execute_text
        outcome=execute_text(skill,args,package.text_transform,settings,completed_results)
    else:
        outcome=run_operation('select_csv_columns',{**args.model_dump(exclude_none=True,exclude={'package_sha256'}),'columns':package.columns},settings,completed_results)
    return {**outcome,'operation':skill,'package_sha256':args.package_sha256}
