from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
from geoagent_harness.contracts.analysis_options import TableFilter
class DatasetOptions(BaseModel):
    model_config=ConfigDict(extra='forbid')
    codebook_path:str|None=Field(default=None,max_length=960)
    missing_values:dict[str,list[str]]=Field(default_factory=dict,max_length=100)
    role_overrides:dict[str,Literal['numerical','count','categorical','ordered_category','identifier','text','uncertain']]=Field(default_factory=dict,max_length=100)
    group_by:list[str]=Field(default_factory=list,max_length=3)
    numeric_columns:list[str]=Field(default_factory=list,max_length=8)
    distinct_columns:list[str]=Field(default_factory=list,max_length=4)
    filters:list[TableFilter]=Field(default_factory=list,max_length=6)
    preview_columns:list[str]=Field(default_factory=list,max_length=16)
    preview_offset:int=Field(default=0,ge=0,le=1000000)
    preview_limit:int=Field(default=20,ge=1,le=100)
