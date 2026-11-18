"""Shared provider actions for Settings and CLI; no workflow execution authority."""
from geoagent_harness.platform.model_gateway.egress import classify_request
from dataclasses import replace
import json
import time

from geoagent_harness.contracts.model_providers import ProviderUpdate,ProviderSelection,ProviderCheck,CapabilityFinding
from geoagent_harness.platform.model_gateway import profiles
from geoagent_harness.platform.model_gateway.client import SharedModelClient,ModelClientError
from geoagent_harness.platform.model_gateway.schemas import ModelRequest,ChatMessage
from geoagent_harness.platform.model_gateway.catalog import catalog,select,Selection


def list_profiles(root):return profiles.public_state(root)


def save_profile(root,request):
    profiles.save(root,request)
    return list_profiles(root)


def select_profile(root,request):
    profiles.select(root,request)
    return list_profiles(root)


def list_models(root,**kwargs):return catalog(root,**kwargs)


def select_model(root,request,**kwargs):return select(root,request,**kwargs)


def check_profile(root,request,*,transport=None):
    from geoagent_harness.platform.model_gateway.catalog import request_selection
    with request_selection(root):return _check_profile(root,request,transport=transport)


def _check_profile(root,request,*,transport=None):
    state=profiles.read(root)
    if state.revision!=request.expected_revision:raise profiles.ProviderError('Provider settings changed; refresh before checking')
    if request.profile_id=='local':raise profiles.ProviderError('Create an explicit profile to record capability checks')
    profile=next((p for p in state.profiles if p.id==request.profile_id),None)
    if profile is None:raise profiles.ProviderError('Unknown provider profile')
    binding=profiles.capture(root)
    binding=replace(binding,state=state.model_copy(update={'selected':profile.id,'models':{**state.models,profile.id:request.model}}))
    settings=binding.settings()
    profiles.require_local(settings)
    schema={'type':'object','properties':{'ok':{'type':'boolean','const':True}},'required':['ok'],'additionalProperties':False}
    probe=classify_request(ModelRequest(messages=[ChatMessage(role='user',content='Return only this JSON object: {"ok":true}. This is a synthetic compatibility check with no project data.')],
        json_mode=True,response_schema=schema,context_class='none',timeout_seconds=min(settings.timeout_seconds,120)), message_classes=('none',), schema_class='none')
    modes=('json_schema','json_object','text') if profile.capabilities=='auto' else (profile.capabilities,)
    deadline=time.monotonic()+min(settings.timeout_seconds,120);attempts=[]
    for mode in modes:
        remaining=deadline-time.monotonic()
        if remaining<=0:return {'status':'unavailable','code':'model_timeout','attempts':attempts,'model_called':bool(attempts),'execution_performed':False}
        try:
            attempts.append(mode)
            result=SharedModelClient(replace(settings,response_format=mode,timeout_seconds=min(settings.timeout_seconds,remaining),max_tokens=min(settings.max_tokens,64)),transport=transport).complete(probe)
            value=json.loads(result.content)
            if value!={'ok':True} or type(value['ok']) is not bool:raise ValueError()
        except ModelClientError as error:
            if error.code=='model_response_format_rejected' and mode!=modes[-1]:continue
            return {'status':'unavailable','code':error.code,'attempts':attempts,'model_called':True,'execution_performed':False}
        except profiles.ProviderError:
            return {'status':'unavailable','code':'model_credentials_invalid','attempts':attempts,'model_called':len(attempts)>1,'execution_performed':False}
        except (ValueError,TypeError):
            return {'status':'unavailable','code':'model_invalid_response','attempts':attempts,'model_called':True,'execution_performed':False}
        finding=CapabilityFinding(model=request.model,profile_sha256=profiles.fingerprint(profile),response_format=mode)
        def change(current):
            return current.model_copy(update={'findings':{**current.findings,profile.id:finding}})
        try:updated=profiles.mutate(root,request.expected_revision,change)
        except profiles.ProviderError:
            return {'status':'stale','code':'profile_changed_during_check','attempts':attempts,'model_called':True,'execution_performed':False}
        return {'status':'compatible','response_format':mode,'profile_id':profile.id,'model':request.model,
            'revision':updated.revision,'attempts':attempts,'model_called':True,'execution_performed':False}
