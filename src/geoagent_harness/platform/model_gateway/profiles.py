"""Bounded workspace provider configuration and private credential resolution."""
from __future__ import annotations
from dataclasses import dataclass,replace
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import stat
from urllib.parse import urlsplit
from pydantic import ValidationError

from geoagent_harness.contracts.model_providers import ProviderState,ProviderProfile
from geoagent_harness.platform.model_settings import ModelSettings,ModelSettingsError,_parse_model_settings
from geoagent_harness.platform.storage.files import FileJsonRecords
from geoagent_harness.platform.workspace import WorkspaceLayout,ensure_state_root

class ProviderError(ModelSettingsError):
    pass


def store(root):
    return FileJsonRecords(WorkspaceLayout.load(Path(root)).state_root,max_bytes=65536)


def read(root):
    try:return ProviderState.model_validate(store(root).read('model-providers.json'))
    except FileNotFoundError:return ProviderState()
    except (OSError,ValueError,RuntimeError):raise ProviderError('Provider configuration is invalid or unavailable') from None


def fingerprint(profile):
    return hashlib.sha256(profile.model_dump_json().encode()).hexdigest()


def loopback(url):
    host=urlsplit(url).hostname
    if host=='localhost':return True
    try:return ipaddress.ip_address(host).is_loopback
    except ValueError:return False


def require_local(settings):
    if settings.provider_profile_id!='local' and not loopback(settings.base_url):
        raise ProviderError('Non-local profiles remain blocked pending provider qualification')


def mutate(root,revision,change):
    from geoagent_harness.platform.storage.metadata import transaction
    try:
        ensure_state_root(Path(root))
        # Existing metadata write transactions serialize cross-process configuration updates.
        with transaction(Path(root),write=True):
            current=read(root)
            if current.revision!=revision:raise ProviderError('Provider settings changed; refresh before applying')
            value=change(current).model_copy(update={'revision':revision+1})
            value=ProviderState.model_validate(value.model_dump())
            target=store(root);target.ensure();target.replace('model-providers.json',value.model_dump_json())
            return value
    except ProviderError:raise
    except (OSError,ValueError,RuntimeError):raise ProviderError('Provider configuration could not be saved') from None


def save(root,request):
    def change(state):
        profiles=[p for p in state.profiles if p.id!=request.profile.id]+[request.profile]
        findings={k:v for k,v in state.findings.items() if k!=request.profile.id}
        models={k:v for k,v in state.models.items() if k!=request.profile.id}
        return state.model_copy(update={'profiles':tuple(profiles),'findings':findings,'models':models})
    return mutate(root,request.expected_revision,change)


def select(root,request):
    def change(state):
        if request.profile_id!='local':
            profile=next((p for p in state.profiles if p.id==request.profile_id),None)
            if profile is None:raise ProviderError('Unknown provider profile')
            if not loopback(profile.base_url):raise ProviderError('Non-local profiles remain blocked pending provider qualification')
        return state.model_copy(update={'selected':request.profile_id})
    return mutate(root,request.expected_revision,change)


def public_state(root):
    state=read(root)
    from geoagent_harness.platform.model_gateway.egress import allowance
    def policy(settings):
        configured,effective,restricted=allowance(settings)
        return {'data_allowed':configured,'effective_data_allowed':effective,
            'nonlocal_restricted':restricted,'egress_policy':'context-parts-v1'}
    try:legacy_policy=policy(replace(capture(root),state=None).settings(discovery=True))
    except ModelSettingsError:legacy_policy={'data_allowed':'none','effective_data_allowed':'none','nonlocal_restricted':True,'egress_policy':'context-parts-v1'}
    return {'schema_version':'1.0','revision':state.revision,'selected_profile':state.selected,
        'profiles':[{'id':'local','kind':'local','location':'machine','listing':'ollama','data_allowed':'raw',
            'model':None,'capabilities':'launcher','credential_configured':False,'enabled':True,**legacy_policy}]+[
            {**{k:getattr(p,k) for k in ('id','kind','location','listing','data_allowed','model','capabilities')},
             **policy(ModelSettings(base_url=p.base_url,model=p.model or 'discovery-placeholder',timeout_seconds=p.limits.timeout_s,
                 max_tokens=p.limits.max_tokens,provider_profile_id=p.id,data_allowed=p.data_allowed)),
             'credential_configured':p.credential_ref is not None,'enabled':loopback(p.base_url)} for p in state.profiles],
        'nonlocal_enabled':False,'model_called':False,'execution_performed':False}


@dataclass(frozen=True)
class Binding:
    root: Path
    values: dict
    state: ProviderState|None
    model_override: str|None
    reasoning_override: str|None
    invalid: bool=False

    def settings(self, *, discovery=False):
        if self.invalid:raise ProviderError('Provider configuration is invalid or unavailable')
        state=self.state
        if state is None or state.selected=='local':
            return replace(_parse_model_settings(self.values,model_override='discovery-placeholder' if discovery else self.model_override,
                reasoning_override=self.reasoning_override),credential_root=str(self.root))
        p=next(p for p in state.profiles if p.id==state.selected)
        model=state.models.get(p.id) or p.model
        if not model and not discovery:raise ModelSettingsError('MODEL_NAME is required')
        mode=p.capabilities
        if mode=='auto':
            finding=state.findings.get(p.id)
            mode=finding.response_format if finding and finding.model==model and finding.profile_sha256==fingerprint(p) else 'json_schema'
        reasoning=self.values.get('MODEL_REASONING_EFFORT') or None
        if self.reasoning_override and self.reasoning_override!='environment':reasoning=None if self.reasoning_override=='provider' else self.reasoning_override
        if reasoning not in {None,'none','low','medium','high'}:raise ModelSettingsError('Invalid reasoning configuration')
        return ModelSettings(base_url=p.base_url,model=model or 'discovery-placeholder',timeout_seconds=p.limits.timeout_s,
            max_tokens=p.limits.max_tokens,reasoning_effort=reasoning,response_format=mode,
            provider_profile_id=p.id,provider_kind=p.kind,provider_location=p.location,data_allowed=p.data_allowed,
            credential_ref=p.credential_ref,credential_root=str(self.root),listing=p.listing)


def capture(root,values=None,model_override=None,reasoning_override=None):
    if reasoning_override is None:
        from geoagent_harness.platform.configuration import selected_reasoning
        reasoning_override=selected_reasoning.get()
    values=dict(os.environ if values is None else values)
    values={k:values[k] for k in ('MODEL_NAME','MODEL_BASE_URL','MODEL_TIMEOUT_SECONDS','MODEL_MAX_TOKENS','MODEL_REASONING_EFFORT','MODEL_RESPONSE_FORMAT','MODEL_DATA_ALLOWED') if k in values}
    try:state=read(root);invalid=False
    except ProviderError:state=None;invalid=True
    return Binding(Path(root).resolve(),values,state,model_override,reasoning_override,invalid)


def headers(settings):
    require_local(settings)  # Before reading any credential or opening any connection.
    u=urlsplit(settings.base_url)
    if u.username or u.password or u.query or u.fragment:raise ProviderError('Model endpoint must not contain credentials or query parameters')
    reference=settings.credential_ref
    if not reference:return {}
    try:
        if reference.startswith('env:'):value=os.environ.get(reference[4:],'')
        elif reference.startswith('secret:'):
            directory=Path(settings.credential_root)/'.secrets';path=directory/reference[7:]
            if any(p.is_symlink() for p in (directory,path,*directory.parents)):raise ValueError()
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            with os.fdopen(fd,'rb') as stream:
                meta=os.fstat(stream.fileno())
                if not stat.S_ISREG(meta.st_mode) or meta.st_nlink!=1 or meta.st_size>8192:raise ValueError()
                value=stream.read(8193).decode().strip()
        else:raise ValueError()
        if not value or len(value)>8192 or any(ord(c)<33 or ord(c)>126 for c in value):raise ValueError()
    except (OSError,ValueError,UnicodeError):raise ProviderError('Model credential is missing or invalid; check its configured reference') from None
    return {'Authorization':'Bearer '+value}
