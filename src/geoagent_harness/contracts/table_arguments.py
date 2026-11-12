"""Closed shared CSV source arguments; no data runtime or execution authority."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


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

