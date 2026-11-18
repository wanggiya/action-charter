"""Bounded evidence projections, never execution or data-egress authority."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

Count = Annotated[int, Field(strict=True, ge=0)]
Label = Annotated[str, Field(min_length=1, max_length=200)]


class CardModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class CardField(CardModel):
    name: Label
    storage_type: str | None = Field(default=None, max_length=200)
    observed_type: str | None = Field(default=None, max_length=80)
    candidate_role: Literal['numerical','count','categorical','ordered_category','identifier','text','uncertain'] | None = None
    missing_count: Count | None = None
    distinct_count: Count | None = None
    numeric_count: Count | None = None
    mean: FiniteFloat | None = None
    minimum: FiniteFloat | None = None
    maximum: FiniteFloat | None = None
    sample_standard_deviation: FiniteFloat | None = None


class DataCard(CardModel):
    schema_version: Literal['data-card-v1'] = 'data-card-v1'
    source: str = Field(min_length=1, max_length=960)
    source_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    identity_basis: Literal['file_sha256', 'package_manifest_sha256', 'pending', 'not_recorded']
    kind: Literal['table', 'vector', 'raster']
    scope: Literal['complete_parsed_file', 'complete_selected_table', 'filtered_rows', 'sample', 'driver_metadata', 'not_recorded']
    freshness: Literal['recorded_read_not_current_file_check'] = 'recorded_read_not_current_file_check'
    file_bytes: Count | None = None
    source_rows: Count | None = None
    profile_rows: Count | None = None
    field_count: Count | None = None
    fields: tuple[CardField, ...] = Field(default=(), max_length=32)
    fields_omitted: Count = 0
    selection: dict = Field(default_factory=dict)
    missingness: Literal['empty_cells', 'native_nulls', 'declared_policy', 'not_recorded'] = 'not_recorded'
    excess_duplicate_rows: Count | None = None
    width: Count | None = None
    height: Count | None = None
    band_count: Count | None = None
    layer_count: Count | None = None
    crs: str | None = Field(default=None, max_length=240)
    roles_are_candidates: Literal[True] = True
    execution_authority: Literal[False] = False

    @model_validator(mode='after')
    def consistent(self):
        from geoagent_harness.contracts.paths import relative_path
        if relative_path(self.source, 'input') != self.source:
            raise ValueError('A Data Card requires a normalized input source')
        if (self.source_sha256 is None) != (self.identity_basis in {'pending', 'not_recorded'}):
            raise ValueError('Data Card identity basis does not match its digest')
        if len({f.name for f in self.fields}) != len(self.fields):
            raise ValueError('Data Card field names must be unique')
        if self.field_count is not None and self.field_count != len(self.fields) + self.fields_omitted:
            raise ValueError('Data Card field coverage does not reconcile')
        if self.source_rows is not None and self.profile_rows is not None and self.profile_rows > self.source_rows:
            raise ValueError('Data Card row scope does not reconcile')
        for field in self.fields:
            if self.profile_rows is not None and any(count is not None and count > self.profile_rows for count in (field.missing_count, field.distinct_count, field.numeric_count)):
                raise ValueError('Data Card field counts exceed their population')
            if self.scope in {'sample', 'driver_metadata', 'not_recorded'} and any(value is not None for value in (field.missing_count, field.distinct_count, field.numeric_count, field.mean, field.minimum, field.maximum, field.sample_standard_deviation)):
                raise ValueError('Partial metadata cannot claim complete field statistics')
        if len(self.model_dump_json().encode()) > 8000:
            raise ValueError('Data Card exceeds its 8 KB contract')
        return self
