"""Closed read-only analytical requests. No expressions, code or implicit exports."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class TableFilter(BaseModel):
    model_config = ConfigDict(extra='forbid')
    column: str = Field(min_length=1, max_length=200)
    value: str = Field(max_length=4096)


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

