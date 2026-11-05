"""Closed result-view contracts. No paths, expressions, SQL or workflow authority."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .spatial_views import SpatialViewOptions


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class ChartAnalysis(Contract):
    group_by: str = Field(min_length=1, max_length=120)
    value: str | None = Field(default=None, min_length=1, max_length=120)
    aggregation: Literal['count', 'sum', 'mean', 'min', 'max']


class ResultFilter(Contract):
    column: str = Field(min_length=1, max_length=200)
    operator: Literal['eq', 'ne', 'gt', 'ge', 'lt', 'le', 'contains', 'is_missing', 'not_missing']
    value: str | float | None = Field(default=None)
    value_type: Literal['text', 'number'] = 'text'

    @model_validator(mode='after')
    def bounded_value(self):
        missing = self.operator in {'is_missing', 'not_missing'}
        if missing != (self.value is None):
            raise ValueError('Missing-value filters omit value; comparisons require value')
        if isinstance(self.value, str) and len(self.value) > 160:
            raise ValueError('Filter text exceeds 160 characters')
        if self.value_type == 'text' and self.value is not None and not isinstance(self.value, str):
            raise ValueError('Text comparison requires a literal string value')
        if self.operator == 'contains' and self.value_type != 'text':
            raise ValueError('Contains is literal text only')
        return self


class ResultSort(Contract):
    column: str = Field(min_length=1, max_length=200)
    descending: bool = False
    value_type: Literal['text', 'number'] = 'text'


class ExplorationQuery(Contract):
    filters: list[ResultFilter] = Field(default_factory=list, max_length=5)
    sort: ResultSort | None = None
    columns: list[str] | None = Field(default=None, min_length=1, max_length=32)
    offset: int = Field(default=0, ge=0, le=10000)
    limit: Literal[25, 50, 100] = 25


class ResultViewSpec(Contract):
    schema_version: Literal['1.0'] = '1.0'
    run_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    step_id: str = Field(pattern=r'^step_[1-9][0-9]*$')
    view: Literal['Table', 'Chart', 'Map']
    query: ExplorationQuery = Field(default_factory=ExplorationQuery)
    chart: ChartAnalysis | None = None
    chart_kind: Literal['bar', 'column', 'line', 'area', 'pie', 'donut'] = 'bar'
    spatial: SpatialViewOptions | None = None
    explanation_fields: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode='after')
    def consistent_view(self):
        if (self.view == 'Chart') != (self.chart is not None):
            raise ValueError('Chart views require an aggregation; other views omit chart')
        if self.view == 'Map' and self.query != ExplorationQuery():
            raise ValueError('Map uses recorded geometry; table queries do not filter map features')
        if self.spatial and (self.view != 'Map' or self.spatial.mode == 'pixel'):
            raise ValueError('Spatial display settings require Map; exact pixel reads use the viewer')
        if self.explanation_fields and (self.chart or self.spatial or self.query != ExplorationQuery()):
            raise ValueError('Recorded explanations do not request new source reads or analysis')
        return self


class ResultViewReply(Contract):
    message: str = Field(min_length=1, max_length=8000)
    plan: None = None
    result_view: ResultViewSpec | None = None
    approval_performed: Literal[False] = False
    execution_performed: Literal[False] = False
