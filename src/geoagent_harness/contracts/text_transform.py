"""Closed data-only text-transform definitions; no Python or regex execution."""
from __future__ import annotations
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class TextStep(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['strip','upper','lower','collapse_whitespace','replace_literal']
    old: str | None = Field(default=None, min_length=1, max_length=128)
    new: str | None = Field(default=None, max_length=128)
    @model_validator(mode='after')
    def replacement(self):
        if self.kind == 'replace_literal':
            if self.old is None or self.new is None: raise ValueError('Literal replacement needs old and new strings')
        elif self.old is not None or self.new is not None:
            raise ValueError('Replacement arguments only apply to replace_literal')
        return self


class TextTransform(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_column: str = Field(min_length=1, max_length=100)
    output_column: str = Field(min_length=1, max_length=100)
    steps: list[TextStep] = Field(min_length=1, max_length=5)
    @model_validator(mode='after')
    def names(self):
        for name in (self.source_column,self.output_column):
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,99}',name):
                raise ValueError('Pilot column names must be ASCII identifiers')
        if self.source_column == self.output_column: raise ValueError('Use a new output column; original columns are preserved')
        return self

