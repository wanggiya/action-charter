"""Data-only operation-package definitions and canonical identity; no runtime imports."""
from __future__ import annotations
import hashlib
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator, model_serializer
from geoagent_harness.contracts.text_transform import TextTransform
from geoagent_harness.contracts.table_arguments import Source

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

