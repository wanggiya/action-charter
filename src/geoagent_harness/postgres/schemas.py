"""Closed database contracts. Database/file effects are separate from authority."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier=Annotated[str,Field(pattern=r'^[a-z_][a-z0-9_]{0,62}$')]
Digest=Annotated[str,Field(pattern=r'^[a-f0-9]{64}$')]
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
class Discover(Strict):
    connection_profile:Literal['configured']='configured'
    target_schema:Identifier='agent_sandbox'
class Table(Discover):
    target_table:Identifier
class Inspect(Table):
    preview_rows:int=Field(default=5,ge=0,le=20)
class Column(Strict):
    source:str=Field(min_length=1,max_length=200)
    name:Identifier
    type:Literal['text','bigint','numeric','boolean']='text'
    nullable:bool=True
    null_values:list[Annotated[str,Field(max_length=200)]]|None=Field(default=None,max_length=20)
class ImportCSV(Table):
    connection_sha256:Digest
    path:str|None=Field(default=None,min_length=1,max_length=960)
    source_step:str|None=Field(default=None,pattern=r'^step_[1-9][0-9]*$')
    source_sha256:Digest|None=None
    delimiter:Literal[',','\t']=','
    columns:list[Column]=Field(min_length=1,max_length=100)
    null_values:list[Annotated[str,Field(max_length=200)]]=Field(default_factory=lambda:[''],max_length=20)
    key_columns:list[Identifier]=Field(default_factory=list,max_length=10)
    mode:Literal['create']='create'
    soft_delete_marker:Identifier|None=None
    @model_validator(mode='after')
    def sources(self):
        if (self.path is None)==(self.source_step is None):raise ValueError('Choose exactly one path or validated CSV source_step')
        if self.path and not self.source_sha256:raise ValueError('Original CSV imports require source_sha256 from inspection')
        if self.source_step and self.source_sha256:raise ValueError('Intermediate digest comes from validated source_step, not supplied text')
        if sum(len(c.source.encode())+len(c.name.encode()) for c in self.columns)>6000:raise ValueError('Column mapping exceeds review budget')
        names=[c.name for c in self.columns];sources=[c.source for c in self.columns]
        if self.soft_delete_marker in names:raise ValueError('Optional deletion marker must be a fresh column outside the mapping')
        if self.soft_delete_marker and len(names)>=100:raise ValueError('Marker would exceed the 100-column limit')
        if len(names)!=len(set(names)) or len(sources)!=len(set(sources)):raise ValueError('Column mappings must be unique')
        if len(self.key_columns)!=len(set(self.key_columns)) or set(self.key_columns)-set(names):raise ValueError('Keys must name distinct mapped columns')
        return self
class ExportCSV(Table):
    target_path:str=Field(min_length=1,max_length=960)
    columns:list[Identifier]=Field(min_length=1,max_length=100)
    expected_table_sha256:Digest|None=None
    source_step:str|None=Field(default=None,pattern=r'^step_[1-9][0-9]*$')
    null_token:str=Field(default='\\N',min_length=1,max_length=32)
    @model_validator(mode='after')
    def binding(self):
        if (self.expected_table_sha256 is None)==(self.source_step is None):raise ValueError('Choose exactly one expected_table_sha256 or validated database source_step')
        if len(set(self.columns))!=len(self.columns):raise ValueError('Export columns must be unique')
        if any(ord(c)<32 for c in self.null_token) or ',' in self.null_token or '"' in self.null_token:raise ValueError('Null token must be printable without CSV delimiters')
        return self
class ChangeRows(Table):
    expected_table_sha256:Digest
    key_column:Identifier
    keys:list[Annotated[str,Field(min_length=1,max_length=200)]]=Field(min_length=1,max_length=1000)
    deleted_column:Identifier='is_deleted'
    expected_affected_rows:int=Field(ge=1,le=1000)
    @model_validator(mode='after')
    def exact_keys(self):
        if len(self.keys)!=len(set(self.keys)) or len(self.keys)!=self.expected_affected_rows:raise ValueError('Choose distinct keys with an exact matching affected-row count')
        if sum(len(k.encode()) for k in self.keys)>8000:raise ValueError('Selected keys exceed the review budget')
        if self.key_column==self.deleted_column:raise ValueError('Deletion marker cannot be the key')
        return self
ARGUMENTS={'discover_postgres_tables':Discover,'inspect_postgres_table':Inspect,'validate_postgres_import':ImportCSV,'import_csv_to_postgres':ImportCSV,'export_postgres_to_csv':ExportCSV,'soft_delete_postgres_rows':ChangeRows,'restore_postgres_rows':ChangeRows}
READ_IDS={'discover_postgres_tables','inspect_postgres_table','validate_postgres_import'}
WRITE_IDS=set(ARGUMENTS)-READ_IDS
LABELS={'discover_postgres_tables':'Discover PostgreSQL tables','inspect_postgres_table':'Inspect PostgreSQL table','import_csv_to_postgres':'Import CSV into PostgreSQL','export_postgres_to_csv':'Export PostgreSQL table to CSV','soft_delete_postgres_rows':'Soft delete PostgreSQL rows','restore_postgres_rows':'Restore PostgreSQL rows'}
LABELS['validate_postgres_import']='Validate PostgreSQL import mapping'
