"""Typed final discovery results, distinct from full geometry/pixel inspection."""
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field


class Evidence(BaseModel):
    model_config=ConfigDict(extra='allow',allow_inf_nan=False)
    schema_version:Literal['spatial-discovery-v1']
    phase:Literal['completed']
    verification:Literal['sha256_complete']
    statistics_scope:Literal['driver_metadata_only']
    file_bytes:int=Field(ge=0,le=1024**3)
    file_count:int=Field(ge=1,le=5)


class Metadata(BaseModel):
    model_config=ConfigDict(extra='allow',allow_inf_nan=False)
    source:str=Field(max_length=960)
    source_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    source_manifest:dict[str,str]
    discovery:Evidence
    effects:Literal['read_only']
    execution_performed:Literal[True]
    validation_performed:Literal[False]
    filesystem_modified:Literal[False]
    database_modified:Literal[False]


class RasterBandDetails(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    band:int=Field(ge=1,le=128)
    block_shape:list[int]=Field(min_length=2,max_length=2)
    color_interpretation:str
    description:str|None
    unit:str|None
    scale:float|None
    offset:float|None
    overview_levels:list[int]=Field(max_length=16)
    metadata:dict[str,str]


class RasterOverview(BaseModel):
    model_config=ConfigDict(extra='forbid')
    factor:int=Field(ge=1)
    width:int=Field(gt=0)
    height:int=Field(gt=0)


class RasterDetails(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    schema_version:Literal['raster-details-v1']
    crs_wkt:str|None=Field(max_length=2048)
    tiled:bool
    compression:str
    interleave:str|None
    metadata:dict[str,dict[str,str]]
    bands:list[RasterBandDetails]=Field(max_length=16)
    overview_dimensions:list[RasterOverview]=Field(max_length=16)
    bands_truncated:bool
    metadata_truncated:bool
    statistics_scope:Literal['stored_tags_only_not_recomputed']
    overview_scope:Literal['first_band_exact_dimensions']


class RasterMetadata(Metadata):
    operation:Literal['inspect_raster']
    driver:Literal['GTiff']
    width:int=Field(gt=0)
    height:int=Field(gt=0)
    band_count:int=Field(gt=0,le=128)
    data_types:list[str]=Field(min_length=1,max_length=128)
    crs:str|None
    bounds:dict[str,float]
    transform:list[float]=Field(min_length=6,max_length=6)
    nodata_values:list[float|None]=Field(max_length=128)
    technical_details:RasterDetails|None=None


class Layer(BaseModel):
    model_config=ConfigDict(extra='allow',allow_inf_nan=False)
    name:str=Field(max_length=120)
    crs:str|None
    geometry_type:str
    feature_count:int|None=Field(ge=0)
    feature_count_basis:Literal['driver_available_metadata','not_computed_expensive']
    fields:list[dict[str,str]]=Field(max_length=100)
    field_count:int=Field(ge=0)
    fields_truncated:bool
    extent:dict[str,float]|None


class VectorMetadata(Metadata):
    operation:Literal['inspect_vector']
    driver:Literal['GPKG','ESRI Shapefile']
    layers:list[Layer]=Field(min_length=1,max_length=8)
