"""Advisory outcome/method schemas; no model calls, persistence or authority."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class MethodSuggestion(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title:str=Field(min_length=1,max_length=120)
    purpose:str=Field(min_length=1,max_length=500)
    operations:list[str]=Field(min_length=1,max_length=20)
    limitations:list[str]=Field(min_length=1,max_length=6)

class OutcomeAssessment(BaseModel):
    model_config=ConfigDict(extra='forbid')
    deterministic_status:Literal['completed','failed','cancelled','interrupted','validation_failed']
    conclusion:Literal['supported','needs_attention']
    summary:str=Field(min_length=1,max_length=1800)
    findings:list[str]=Field(max_length=8)
    limitations:list[str]=Field(min_length=1,max_length=8)
    reusable_method:MethodSuggestion|None=None
