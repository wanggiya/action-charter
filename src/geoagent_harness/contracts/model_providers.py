"""Trusted model configuration contracts; none grants execution authority."""
from __future__ import annotations
from typing import Annotated, Literal
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator, field_validator

ProfileId=Annotated[str,Field(pattern=r'^[a-z][a-z0-9_-]{0,63}$')]
ModelName=Annotated[str,Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,159}$')]
DataClass=Literal['none','metadata','data_card','aggregates','raw']
ResponseFormat=Literal['json_schema','json_object','text']
DATA_CLASSES=('none','metadata','data_card','aggregates','raw')

class ProviderModel(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True)

class ContextPart(ProviderModel):
    """Code-owned classification bound to one exact outbound context component."""
    kind: Literal['message','response_schema']
    index: int=Field(ge=0)
    data_class: DataClass
    sha256: Annotated[str,Field(pattern=r'^[a-f0-9]{64}$')]

class EgressDecision(ProviderModel):
    highest_class: DataClass
    data_allowed: DataClass
    configured_data_allowed: DataClass
    allowed: bool
    unclassified_parts: int=Field(ge=0)
    nonlocal_restricted: bool

class ProviderLimits(ProviderModel):
    timeout_s: float=Field(default=120,strict=True,gt=0,le=600,allow_inf_nan=False)
    max_tokens: StrictInt=Field(default=1024,ge=1,le=32768)

class ProviderProfile(ProviderModel):
    id: ProfileId
    kind: Literal['local','onsite','gateway','public']='local'
    api: Literal['openai-compatible']='openai-compatible'
    base_url: str=Field(max_length=500)
    credential_ref: Annotated[str,Field(pattern=r'^(env:[A-Z][A-Z0-9_]{0,79}|secret:[A-Za-z0-9][A-Za-z0-9_.-]{0,79})$')]|None=None
    location: Literal['machine','site','organisation','external']='machine'
    data_allowed: DataClass='none'
    model: ModelName|None=None
    listing: Literal['openai-compatible','ollama']='openai-compatible'
    capabilities: Literal['auto','json_schema','json_object','text']='auto'
    limits: ProviderLimits=Field(default_factory=ProviderLimits)

    @model_validator(mode='before')
    @classmethod
    def defaults(cls,value):
        if isinstance(value,dict):
            value=dict(value);kind=value.get('kind','local')
            value.setdefault('data_allowed','raw' if kind=='local' else 'none')
            value.setdefault('location',{'local':'machine','onsite':'site','gateway':'organisation','public':'external'}.get(kind,'machine'))
        return value

    @field_validator('id')
    @classmethod
    def reserved(cls,value):
        if value=='local':raise ValueError('local is reserved for environment compatibility')
        return value

    @field_validator('base_url')
    @classmethod
    def endpoint(cls,value):
        value=value.rstrip('/');u=urlsplit(value)
        try:port=u.port
        except ValueError:raise ValueError('Invalid model endpoint') from None
        if (u.scheme not in {'http','https'} or not u.hostname or u.username or u.password or u.query or u.fragment
                or not u.path.endswith('/v1') or any(c.isspace() or ord(c)<32 for c in value)):
            raise ValueError('Use a compatible /v1 URL without credentials or query')
        return value

class CapabilityFinding(ProviderModel):
    model: ModelName
    profile_sha256: Annotated[str,Field(pattern=r'^[a-f0-9]{64}$')]
    response_format: ResponseFormat

class ProviderState(ProviderModel):
    schema_version: Literal['1.0']='1.0'
    revision: StrictInt=Field(default=0,ge=0)
    selected: ProfileId='local'
    profiles: Annotated[tuple[ProviderProfile,...],Field(max_length=32)]=()
    models: dict[ProfileId,ModelName]=Field(default_factory=dict)
    findings: dict[ProfileId,CapabilityFinding]=Field(default_factory=dict)

    @model_validator(mode='after')
    def consistent(self):
        ids=[p.id for p in self.profiles]
        if len(set(ids))!=len(ids) or (self.selected!='local' and self.selected not in ids):raise ValueError('Invalid profile inventory')
        if set(self.models)-set(ids) or set(self.findings)-set(ids):raise ValueError('Unknown profile setting')
        return self

class ProviderUpdate(ProviderModel):
    profile: ProviderProfile
    expected_revision: StrictInt=Field(ge=0)

class ProviderSelection(ProviderModel):
    profile_id: ProfileId
    expected_revision: StrictInt=Field(ge=0)

class ProviderCheck(ProviderSelection):
    model: ModelName
