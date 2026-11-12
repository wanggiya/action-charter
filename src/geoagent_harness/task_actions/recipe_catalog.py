import json,os
from pathlib import Path
from tempfile import mkstemp
from geoagent_harness.contracts.actions import EditRequest
from geoagent_harness.capabilities.workflow import validate_edit
from geoagent_harness.capabilities.recipes.catalog.composition import catalog, _builtins, compose, test_recipe, recipe_digest, operation_fingerprint
from geoagent_harness.capabilities.recipes.catalog import composition as _definitions

def __getattr__(name):
    """Preserve the former mixed catalog namespace at its coordination boundary."""
    return getattr(_definitions, name)

def recipe_action(request, *, project_root):
    from geoagent_harness.platform.project import _trusted_root
    root=_trusted_root(project_root)
    if request.action in {'search','inspect'}:
        from geoagent_harness.capabilities.recipes.catalog.discovery import DiscoveryRequest, discover
        from geoagent_harness.capabilities.registry.registry import argument_models
        return discover(DiscoveryRequest(action=request.action,query=request.query,recipe_id=request.recipe_id,method_id=request.method_id),
                        root=root,conversation_id=request.conversation_id,available=list(argument_models(root)),use_history=bool(request.conversation_id))
    if request.action=='list':
        query=request.query.casefold()
        unavailable=[]
        available=catalog(root,unavailable)
        from geoagent_harness.capabilities.recipes.catalog.successful import inventory
        successful_finding = None
        try:
            successful = inventory(root, conversation_id=request.conversation_id, query=request.query)
        except Exception:
            successful = []
            successful_finding = 'Successful-workflow index is unavailable. Existing templates and execution records are preserved.'
        return {'recipes':[{'definition':r.model_dump(mode='json',exclude={'tests'}),'recipe_sha256':recipe_digest(r),'origin':'builtin' if r.id in {b.id for b in _builtins()} else 'registered'} for r in available.values() if query in (r.id+' '+r.name+' '+r.description).casefold()], 'unavailable':unavailable, 'successful_records':successful, 'successful_records_finding':successful_finding, 'execution_performed':False}
    if request.action=='compose':
        result,receipts=compose(request.uses,root,request.base)
        return {**validate_edit(EditRequest(action='validate_plan_edit',planner_result=result),project_root=root),'recipe_groups':receipts}
    if request.action=='prepare':
        from geoagent_harness.agents.roles.planner.recipe_authoring import prepare_recipe
        if request.base is None:
            raise ValueError('Prepare a reusable recipe from a current validated workflow')
        return prepare_recipe(request.base,root)
    if request.definition is None:
        raise ValueError('A recipe definition is required')
    report=test_recipe(request.definition,root)
    digest=recipe_digest(request.definition)
    if request.action=='register':
        if not request.confirm_register or request.confirmed_recipe_sha256!=digest:
            raise ValueError('Confirm registration of the exact tested recipe; it grants no execution authority')
        from geoagent_harness.platform.workspace import runtime_store_path, ensure_state_root
        directory=runtime_store_path(root,'reusable-recipes')
        if request.definition.id in catalog(root) or (directory/(request.definition.id+'.json')).exists():
            raise ValueError('Recipe ID already registered; in-place replacement is unavailable')
        if directory.is_symlink():
            raise ValueError('Recipe storage is unsafe')
        ensure_state_root(root)
        directory.mkdir(mode=0o700,parents=True,exist_ok=True)
        if len(list(directory.glob('*.json')))>=50:
            raise ValueError('Recipe inventory limit reached')
        data=json.dumps({'definition':request.definition.model_dump(mode='json'),'recipe_sha256':digest,'test_report':report,
                         'operation_contracts_sha256':operation_fingerprint(request.definition,root)})
        fd,temporary=mkstemp(dir=directory,prefix='.recipe-',suffix='.tmp')
        try:
            with os.fdopen(fd,'w') as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.link(temporary,directory/(request.definition.id+'.json'),follow_symlinks=False)
        finally:
            Path(temporary).unlink(missing_ok=True)
    return {'definition':request.definition.model_dump(mode='json'),'recipe_sha256':digest,'test_report':report,'registered':request.action=='register','execution_performed':False}



# Trusted context kwargs stay outside transport/model request schemas.
from geoagent_harness.core.execution.actions import task_entrypoint as _task_entrypoint
recipe_action = _task_entrypoint(recipe_action, audit=lambda arguments: arguments["request"].action not in ['compose', 'inspect', 'list', 'search'])
