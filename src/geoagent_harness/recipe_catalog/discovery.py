"""Read-only bounded Planner recipe discovery, without private library bindings."""
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DiscoveryRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['search', 'inspect']
    query: str = Field(default='', max_length=200)
    recipe_id: str | None = Field(default=None, pattern=r'^recipe_[a-z][a-z0-9_]{0,55}$')
    method_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')


def _enum(value, schema):
    if 'enum' in schema and value in schema['enum']: return True
    if 'const' in schema and value == schema['const']: return True
    return any(_enum(value, item) for item in schema.get('anyOf', []))


def library_structure(recipe, root):
    from .composition import _builtins, recipe_digest
    from geoagent_harness.operations.registry import argument_models, NAMES
    builtin=recipe.id in {r.id for r in _builtins()}
    models=argument_models(root)
    safe=True
    steps=[]
    for step in recipe.steps:
        schema=models[step.skill].model_json_schema()
        arguments={}
        for key,value in step.arguments.items():
            reference=isinstance(value,dict) and ((set(value)=={'$parameter'} and isinstance(value['$parameter'],str) and value['$parameter'] in recipe.parameters) or (set(value)=={'$step'} and value['$step'] in {s.step_id for s in recipe.steps}))
            if reference or _enum(value,schema.get('properties',{}).get(key,{})) or value is None:
                arguments[key]=value
            else:
                arguments[key]={'current_binding_required':True}
                safe=False
        steps.append({'step_id':step.step_id,'skill':step.skill,'arguments':arguments,'depends_on':step.depends_on,'csv_source_parameter':step.csv_source_parameter})
    return {'id':recipe.id,'recipe_sha256':recipe_digest(recipe),'name':recipe.name if builtin else ' → '.join(NAMES.get(s.skill,s.skill) for s in recipe.steps)[:180],
            'description':recipe.description if builtin else 'Registered method structure; bind current inputs and parameters. Private fixed values are not exposed.',
            'parameters':{key:{'type':p.type,'description':p.description if builtin else 'Current '+p.type+' binding'} for key,p in recipe.parameters.items()},
            'skills':[s.skill for s in recipe.steps],'steps':steps,'output_contract':recipe.output_contract,
            'composition_available':safe,'visibility':'catalog_definition_without_private_literals',
            'limitation':'Past registration/test results do not grant authority or validate new inputs.'}


def discover(request, *, root, conversation_id, available, use_history=True, selected_id=None):
    from .composition import catalog
    from .successful import inventory
    from geoagent_harness.planner.successful_retrieval import retrieve
    definitions={key:value for key,value in catalog(root).items() if all(s.skill in available for s in value.steps)}
    rows=[]
    # Own-chat records never become public library definitions merely by success.
    try:
        own=inventory(root,conversation_id=conversation_id) if use_history or selected_id else []
    except Exception:
        own=[]
    own=[r for r in own if r['contract_status']=='current' and all(o['skill_id'] in available for o in r['operations']) and (use_history or r['method_id']==selected_id)]
    if request.action=='inspect':
        if bool(request.recipe_id)==bool(request.method_id):
            return {'status':'not_found','finding':'Inspect exactly one available recipe or own-chat method.'}
        if request.recipe_id in definitions:
            item=library_structure(definitions[request.recipe_id],root)
            if len(json.dumps(item).encode())>8000:
                return {'status':'unavailable','finding':'Definition exceeds the bounded inspection budget. Use ordinary operation contracts.'}
            return {'status':'found','definition':item,'approval_performed':False,'execution_performed':False}
        if request.method_id and any(r['method_id']==request.method_id for r in own):
            examples,_=retrieve(root,conversation_id,'',available,use_history=use_history,selected_id=request.method_id)
            if examples:return {'status':'found','own_chat_example':examples[0],'approval_performed':False,'execution_performed':False}
        return {'status':'not_found','finding':'Unavailable, changed or outside the current chat/operation scope.'}
    for recipe in definitions.values():
        item=library_structure(recipe,root)
        rows.append({key:item[key] for key in ('id','name','description','skills','output_contract','composition_available','visibility')})
    rows.extend({'method_id':r['method_id'],'name':r['name'],'tags':r['tags'],'skills':[o['skill_id'] for o in r['operations']],
                 'visibility':'own_chat_recorded_success','composition_available':False} for r in own)
    terms=set(re.findall(r'[a-z0-9_]{2,}',request.query.casefold()))
    ranked=[]
    for row in rows:
        text=json.dumps(row).casefold()
        score=sum(word in text for word in terms)
        if not terms or score:ranked.append((score,row))
    ranked.sort(key=lambda item:(-item[0],item[1].get('id',item[1].get('method_id',''))))
    result=[]
    for _,row in ranked[:5]:
        if len(json.dumps(result+[row]).encode())<=5000:result.append(row)
    return {'status':'found' if result else 'no_matches','matches':result,'limit':5,
            'approval_performed':False,'execution_performed':False}
