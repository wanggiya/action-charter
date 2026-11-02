"""Closed read-only analytical requests. No expressions, code or implicit exports."""
from pydantic import BaseModel, ConfigDict, Field,model_validator
from typing import Literal
from .statistics import StatisticsSpec


class TableFilter(BaseModel):
    model_config = ConfigDict(extra='forbid')
    column: str = Field(min_length=1, max_length=200)
    value: str = Field(max_length=4096)


class TableSourceOptions(BaseModel):
    """Explicit selection only; no macros, formulas or arbitrary reader options."""
    model_config=ConfigDict(extra='forbid')
    sheet:str|None=Field(default=None,min_length=1,max_length=200)
    header_row:int=Field(default=1,ge=1,le=1000)
    cell_range:str|None=Field(default=None,pattern=r'^[A-Z]{1,3}[1-9][0-9]{0,6}:[A-Z]{1,3}[1-9][0-9]{0,6}$')
    records_key:str|None=Field(default=None,min_length=1,max_length=200)
    @model_validator(mode='after')
    def selection(self):
        if self.cell_range and self.header_row!=1:raise ValueError('Choose cell_range or header_row, not both')
        return self


class ObservedTableSchema(BaseModel):
    """Compact full schema: default types plus explicit per-column overrides."""
    model_config=ConfigDict(extra='forbid')
    columns:list[str]=Field(min_length=1,max_length=100)
    storage_types_default:list[Literal['string','boolean','integer','number','datetime','null']]
    storage_types_overrides:dict[str,list[Literal['string','boolean','integer','number','datetime','null']]]
    null_counts:dict[str,int]
    empty_string_counts:dict[str,int]
    absent_count_means:Literal[0]=0
    @model_validator(mode='after')
    def valid_schema(self):
        names=set(self.columns)
        if len(names)!=len(self.columns):raise ValueError('Table source columns must be unique')
        if any(set(values)-names for values in (self.storage_types_overrides,self.null_counts,self.empty_string_counts)):
            raise ValueError('Table source facts reference unknown columns')
        if any(count<0 for count in [*self.null_counts.values(),*self.empty_string_counts.values()]):
            raise ValueError('Observed counts cannot be negative')
        return self


class TableAnalyticalView(BaseModel):
    model_config=ConfigDict(extra='forbid')
    schema_version:Literal['table-string-view-v1']
    conversion:Literal['native scalars to text; null to empty; dates to ISO','source CSV text']
    missingness:Literal['empty analytical cells and explicitly declared tokens; no imputation']
    numeric_selection:Literal['explicit parameters, never identifier/type inference']


class ResolvedTableSelection(BaseModel):
    model_config=ConfigDict(extra='forbid')
    sheet:str|None=None
    header_row:int|None=Field(default=None,ge=1,le=1048576)
    cell_range:str|None=None
    available_sheets:list[str]=Field(default_factory=list,max_length=32)


class TableSourceDescriptor(BaseModel):
    """Versioned result metadata, never executable input or an approval receipt."""
    model_config=ConfigDict(extra='forbid',populate_by_name=True)
    schema_version:Literal['table-source-v1']
    path:str
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    format:str
    selection:ResolvedTableSelection
    source_options:TableSourceOptions|None
    delimiter:Literal[',','\t']|None
    rows:int=Field(ge=0)
    scope:Literal['complete_selected_table','complete_parsed_file']
    record_grain:Literal['parsed_table_record']
    table_schema:ObservedTableSchema=Field(alias='schema')
    analytical_view:TableAnalyticalView
    verified:Literal['full_sha256_and_reader_identity_checks']
    effects:Literal['read_only']
    execution_authority:Literal[False]
    @model_validator(mode='after')
    def valid_source(self):
        from .source_contracts import table_format
        from geoagent_harness.discovery.source import relative_path
        if relative_path(self.path,'input')!=self.path:raise ValueError('Recorded source paths must be canonical')
        if table_format(self.path).id!=self.format:raise ValueError('Table source format differs from its path')
        if any(c>self.rows for c in [*self.table_schema.null_counts.values(),*self.table_schema.empty_string_counts.values()]):
            raise ValueError('Observed missingness exceeds parsed records')
        return self


class AnalysisOptions(BaseModel):
    model_config = ConfigDict(extra='forbid')
    codebook_path: str | None = Field(default=None, max_length=960)
    profile_columns: list[str] = Field(default_factory=list, max_length=16)
    numeric_columns: list[str] = Field(default_factory=list, max_length=8)
    count_columns: list[str] = Field(default_factory=list, max_length=8)
    distinct_columns: list[str] = Field(default_factory=list, max_length=4)
    quality_columns: list[str] = Field(default_factory=list, max_length=4)
    duplicate_key: list[str] = Field(default_factory=list, max_length=4)
    duplicate_rows: bool = False
    group_by: list[str] = Field(default_factory=list, max_length=3)
    filters: list[TableFilter] = Field(default_factory=list, max_length=6)
    missing_values: dict[str, list[str]] = Field(default_factory=dict, max_length=16)
    offset: int = Field(default=0, ge=0, le=1000000)
    limit: int = Field(default=20, ge=1, le=100)
    statistics: StatisticsSpec | None = None
    source_options:TableSourceOptions|None=None


class TableBinding(BaseModel):
    model_config = ConfigDict(extra='forbid')
    path: str = Field(max_length=960)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class SourceTableReference(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal['table-reference-v1'] = 'table-reference-v1'
    kind: Literal['verified_source_view'] = 'verified_source_view'
    reference_id: str = Field(pattern=r'^[a-f0-9]{64}$')
    sources: list[TableBinding] = Field(min_length=1,max_length=2)
    query: AnalysisOptions
    delimiter: Literal[',','\t']
    row_count: int = Field(ge=0)
    columns: list[str] = Field(min_length=1,max_length=100)
    lifecycle: str = Field(max_length=200)
    effects: Literal['read_only'] = 'read_only'
    executable_by_id: Literal[False] = False

