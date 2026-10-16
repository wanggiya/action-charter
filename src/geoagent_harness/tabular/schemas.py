"""Closed tabular arguments: data values only, never pandas expressions/callables."""
from __future__ import annotations
from typing import Literal, Annotated
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

Scalar = Annotated[str, Field(max_length=4096)] | int | float | bool
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class InspectCSV(Strict):
    path: str = Field(min_length=1, max_length=960)
    delimiter: Literal[',', '\t'] = ','
    preview_rows: int = Field(default=5, ge=0, le=20)

def _source_schema(schema):
    """Expose the same exclusive source choice enforced at runtime to models."""
    pairs=[('path','source_step')]
    if 'right_path' in schema.get('properties',{}):
        pairs.append(('right_path','right_step'))
    schema.setdefault('allOf',[]).extend({'oneOf':[
        {'required':[left],'properties':{left:{'type':'string'},right:{'type':'null'}}},
        {'required':[right],'properties':{right:{'type':'string'},left:{'type':'null'}}},
    ]} for left,right in pairs)


class Source(Strict):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, json_schema_extra=_source_schema)
    path: str | None = Field(default=None, min_length=1, max_length=960)
    source_step: str | None = Field(default=None, pattern=r'^step_[1-9][0-9]*$')
    delimiter: Literal[',', '\t'] = ','
    target_path: str = Field(min_length=1, max_length=960)
    @model_validator(mode='after')
    def one_source(self):
        if (self.path is None) == (self.source_step is None):
            raise ValueError('Choose exactly one path or source_step')
        return self

class SelectColumns(Source):
    columns: list[str] = Field(min_length=1, max_length=100)

class Predicate(Strict):
    column: str = Field(min_length=1, max_length=200)
    operator: Literal['eq','ne','gt','ge','lt','le','is_missing','not_missing']
    value: Scalar | None = None
    value_type: Literal['text','number'] = 'text'
    @model_validator(mode='after')
    def required_value(self):
        if self.operator not in {'is_missing','not_missing'} and self.value is None:
            raise ValueError('Comparison requires a scalar value')
        if self.operator in {'is_missing','not_missing'} and self.value is not None:
            raise ValueError('Missing-value predicates have no comparison value')
        return self

class FilterRows(Source):
    predicates: list[Predicate] = Field(min_length=1, max_length=20)
    match: Literal['all','any'] = 'all'

class HandleMissing(Source):
    method: Literal['fill','drop_rows']
    fill_values: dict[str, Scalar] = Field(default_factory=dict)
    columns: list[str] = Field(default_factory=list, max_length=100)
    @model_validator(mode='after')
    def valid_strategy(self):
        if self.method == 'fill' and (not self.fill_values or self.columns):
            raise ValueError('fill requires fill_values only')
        if self.method == 'drop_rows' and self.fill_values:
            raise ValueError('drop_rows does not accept fill_values')
        if len(self.fill_values) > 100:
            raise ValueError('Too many fill columns')
        return self

class JoinTables(Source):
    right_delimiter: Literal[',', '\t'] = ','
    right_path: str | None = Field(default=None, min_length=1, max_length=960)
    right_step: str | None = Field(default=None, pattern=r'^step_[1-9][0-9]*$')
    keys: list[str] = Field(min_length=1, max_length=10)
    how: Literal['inner','left'] = 'inner'
    cardinality: Literal['one_to_one','many_to_one','one_to_many'] = 'many_to_one'
    @model_validator(mode='after')
    def one_right_source(self):
        if (self.right_path is None) == (self.right_step is None):
            raise ValueError('Choose exactly one right_path or right_step')
        return self

class Aggregation(Strict):
    column: str = Field(min_length=1,max_length=200)
    function: Literal['sum','mean','min','max','count']
    output_column: str = Field(min_length=1,max_length=200)

class Aggregate(Source):
    by: list[str] = Field(min_length=1,max_length=20)
    aggregations: list[Aggregation] = Field(min_length=1,max_length=100)

class ExportCSV(Source):
    pass

class VectorAttributes(Strict):
    path: str = Field(min_length=1,max_length=960)
    target_path: str = Field(min_length=1,max_length=960)

ARGUMENTS = {
    'inspect_csv': InspectCSV, 'select_csv_columns': SelectColumns, 'filter_csv_rows': FilterRows,
    'handle_csv_missing': HandleMissing, 'join_csv': JoinTables, 'aggregate_csv': Aggregate,
    'export_csv': ExportCSV, 'vector_attributes_to_csv': VectorAttributes,
}
LABELS = {'inspect_csv':'Inspect CSV table','select_csv_columns':'Select table columns','filter_csv_rows':'Filter table rows','handle_csv_missing':'Handle missing table values','join_csv':'Join CSV tables','aggregate_csv':'Group and aggregate table','export_csv':'Export CSV results','vector_attributes_to_csv':'Extract vector attributes as CSV'}
WRITE_IDS = set(ARGUMENTS) - {'inspect_csv'}


def is_extension(id):
    import re
    return bool(re.fullmatch(r'ext_[a-z][a-z0-9_]{0,60}',id))

def is_table_write(id):
    return id in WRITE_IDS or is_extension(id)
