"""Data-only packages bind one trusted adapter; no package code is imported."""
from __future__ import annotations
import hashlib
import json
import os
import re
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator, model_serializer
from geoagent_harness.capabilities.text import TextTransform
from geoagent_harness.tabular.schemas import Source

ADAPTER_ENTRYPOINT = 'geoagent_harness.operations.packages:execute_projection'
VERIFIER = 'geoagent_harness.tabular.service:validate_output'
DIRECTORY = 'operation-packages'
MAX_BYTES = 64000

class PackageError(ValueError):
    pass

class ProjectionArguments(Source):
    package_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')

class Fixture(BaseModel):
    model_config = ConfigDict(extra='forbid')
    csv: str = Field(min_length=1,max_length=16000)
    expected_csv: str = Field(min_length=1,max_length=16000)

class OperationPackage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal['1.0'] = '1.0'
    id: str = Field(pattern=r'^ext_[a-z][a-z0-9_]{0,60}$')
    name: str = Field(min_length=1,max_length=100)
    version: str = Field(pattern=r'^\d+\.\d+\.\d+$')
    runtime: Literal['pandas==3.0.5'] = 'pandas==3.0.5'
    candidate_function: Literal['pandas.core.indexing.IndexingMixin.loc','pandas.Series.str'] = 'pandas.core.indexing.IndexingMixin.loc'
    adapter: Literal['csv_column_projection','csv_text_transform']
    columns: list[str] = Field(default_factory=list,max_length=100)
    text_transform: TextTransform | None = None
    tests: list[Fixture] = Field(min_length=1,max_length=5)
    @model_validator(mode='after')
    def distinct_columns(self):
        if self.adapter=='csv_column_projection' and (not self.columns or self.text_transform is not None or self.candidate_function!='pandas.core.indexing.IndexingMixin.loc'):
            raise ValueError('Projection requires fixed columns and its trusted projection adapter')
        if self.adapter=='csv_text_transform' and (self.columns or self.text_transform is None or self.candidate_function!='pandas.Series.str'):
            raise ValueError('Text adapter requires its closed transform and trusted text runtime')
        if len(set(self.columns))!=len(self.columns) or any(not c or len(c)>200 for c in self.columns):
            raise ValueError('Choose unique bounded column names')
        return self
    @model_serializer(mode='wrap')
    def compatible_manifest(self, handler):
        value=handler(self)
        if value['text_transform'] is None:value.pop('text_transform')
        return value


def canonical(package):
    return json.dumps(package.model_dump(mode='json'),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

def package_sha(package):
    return hashlib.sha256(canonical(package)).hexdigest()

def configuration(package):
    value={'adapter':package.adapter,'columns':package.columns,'candidate_function':package.candidate_function,'runtime':package.runtime}
    if package.text_transform is not None:value['text_transform']=package.text_transform.model_dump(mode='json')
    return value

def parse_package(value):
    package=OperationPackage.model_validate(value)
    if len(canonical(package))>MAX_BYTES:raise PackageError('Package exceeds 64 KB')
    return package

def _directory(stack, root, create=False):
    fd=os.open(Path(root).resolve(strict=True),os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    stack.callback(os.close,fd)
    if create:
        try:os.mkdir(DIRECTORY,0o700,dir_fd=fd)
        except FileExistsError:pass
    fd=os.open(DIRECTORY,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
    stack.callback(os.close,fd)
    return fd

def installed_packages(root):
    directory=Path(root)/DIRECTORY
    if not directory.exists() and not directory.is_symlink():return {}
    result={}
    try:
        with ExitStack() as stack:
            parent=_directory(stack,root)
            entries=[name for name in os.listdir(parent) if not re.fullmatch(r'\.package\.[a-f0-9]{32}\.tmp',name)]
            if len(entries)>20:raise PackageError('Installed package count exceeds 20')
            for filename in sorted(entries):
                if not re.fullmatch(r'ext_[a-z][a-z0-9_]{0,60}\.json',filename):raise PackageError('Unexpected installed package record')
                fd=os.open(filename,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
                with os.fdopen(fd,'rb') as handle:data=handle.read(MAX_BYTES+1)
                if len(data)>MAX_BYTES:raise PackageError('Installed package exceeds its bound')
                stored=json.loads(data)
                if set(stored)!={'package','package_sha256'}:raise PackageError('Installed package record has unknown fields')
                package=parse_package(stored['package'])
                if filename!=f'{package.id}.json' or stored['package_sha256']!=package_sha(package):raise PackageError('Installed package identity/digest mismatch')
                if package.id in result:raise PackageError('Conflicting installed versions; explicit update is not supported')
                result[package.id]=package
    except OSError as error:raise PackageError('Installed package directory/file is unsafe or unavailable') from error
    return result

def package_skills(root):
    from geoagent_harness.skill_registry.schemas import SkillDefinition
    return [SkillDefinition(id=p.id,version=p.version,status='implemented',kind='transformation',access='artifact_write',approval_required=True,validation_required=True,entrypoint=ADAPTER_ENTRYPOINT,verifier=VERIFIER) for p in installed_packages(root).values()]

def test_package(value, *, timeout_seconds=20):
    package=parse_package(value)
    if package.adapter=='csv_text_transform':
        from geoagent_harness.capabilities.testing import test_text_package
        return test_text_package(package,timeout_seconds=timeout_seconds)
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.tabular.service import read_frame, run_operation, validate_output
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
    from geoagent_harness.tabular.service import run_operation, TabularError
    args=ProjectionArguments.model_validate(arguments)
    from geoagent_harness.tabular.service import pd
    if pd.__version__!='3.0.5':raise TabularError('Installed adapter runtime does not match pandas 3.0.5')
    package=installed_packages(settings.project_root).get(skill)
    if package is None or package_sha(package)!=args.package_sha256:
        raise TabularError('Installed adapter is missing or differs from the exact approved package digest')
    if package.adapter=='csv_text_transform':
        from geoagent_harness.capabilities.text import execute_text
        outcome=execute_text(skill,args,package.text_transform,settings,completed_results)
    else:
        outcome=run_operation('select_csv_columns',{**args.model_dump(exclude_none=True,exclude={'package_sha256'}),'columns':package.columns},settings,completed_results)
    return {**outcome,'operation':skill,'package_sha256':args.package_sha256}
