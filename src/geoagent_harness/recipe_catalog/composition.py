"""Data-only reusable recipes, expanded into ordinary governed plans."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory, mkstemp
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from geoagent_harness.planner.schemas import PlannerResult, WorkflowPlan, PlanStep


class Closed(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class RecipePreparationError(ValueError):
    """Safe preparation finding containing no model or source values."""


class Parameter(Closed):
    type: Literal['string', 'array', 'object', 'integer', 'number', 'boolean', 'csv_source']
    description: str = Field(min_length=1, max_length=300)


class TemplateStep(Closed):
    step_id: str = Field(pattern=r'^step_[1-9][0-9]*$')
    skill: str = Field(pattern=r'^[a-z][a-z0-9_]*$')
    purpose: str = Field(min_length=1, max_length=1000)
    arguments: dict[str, Any]
    depends_on: list[str] = Field(default_factory=list, max_length=20)
    csv_source_parameter: str | None = None


class Fixture(Closed):
    files: dict[str, str] = Field(min_length=1, max_length=5)
    parameters: dict[str, Any]
    expected_csv: dict[str, str] = Field(min_length=1, max_length=5)


class ReusableRecipe(Closed):
    schema_version: Literal['1.0'] = '1.0'
    id: str = Field(pattern=r'^recipe_[a-z][a-z0-9_]{0,55}$')
    version: str = Field(pattern=r'^\d+\.\d+\.\d+$')
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    parameters: dict[str, Parameter] = Field(min_length=1, max_length=30)
    steps: list[TemplateStep] = Field(min_length=1, max_length=20)
    output_step: str = Field(pattern=r'^step_[1-9][0-9]*$')
    output_contract: Literal['table/csv-v1', 'metadata/csv-v1', 'metadata/vector-v1']
    tests: list[Fixture] = Field(default_factory=list, max_length=3)

    @model_validator(mode='after')
    def consistent(self):
        if any(re.fullmatch(r'[a-z][a-z0-9_]{0,70}', key) is None for key in self.parameters):
            raise ValueError('Recipe parameter names must be safe identifiers')
        known = set()
        for index, step in enumerate(self.steps, 1):
            if step.step_id != f'step_{index}' or not set(step.depends_on).issubset(known) or len(step.depends_on)!=len(set(step.depends_on)):
                raise ValueError('Recipe steps must be sequential with unique earlier dependencies')
            if step.csv_source_parameter and (step.csv_source_parameter not in self.parameters or self.parameters[step.csv_source_parameter].type!='csv_source'):
                raise ValueError('CSV source bindings require a declared csv_source parameter')
            for key in ('source_step','right_step'):
                if key in step.arguments:
                    reference=step.arguments[key]
                    if not isinstance(reference,dict) or set(reference)!={'$step'} or reference['$step'] not in known:
                        raise ValueError('Recipe data references must use an earlier local $step binding')
            known.add(step.step_id)
        if self.output_step not in known:
            raise ValueError('Recipe output must reference a declared step')
        if len(canonical(self)) > 60_000:
            raise ValueError('Recipe exceeds 60 KB')
        return self


class RecipeUse(Closed):
    recipe_id: str = Field(pattern=r'^recipe_[a-z][a-z0-9_]{0,55}$')
    recipe_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    alias: str = Field(pattern=r'^[a-z][a-z0-9_]{0,30}$')
    parameters: dict[str, Any] = Field(max_length=30)


class RecipeRequest(Closed):
    action: Literal['list', 'compose', 'test', 'register', 'prepare', 'search', 'inspect']
    query: str = Field(default='', max_length=200)
    conversation_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')
    recipe_id: str | None = Field(default=None, pattern=r'^recipe_[a-z][a-z0-9_]{0,55}$')
    method_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    uses: list[RecipeUse] = Field(default_factory=list, max_length=10)
    base: PlannerResult | None = None
    definition: ReusableRecipe | None = None
    confirmed_recipe_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    confirm_register: bool = False


def canonical(recipe):
    return json.dumps(recipe.model_dump(mode='json'), sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def recipe_digest(recipe):
    return hashlib.sha256(canonical(recipe)).hexdigest()


def operation_fingerprint(recipe,root):
    from geoagent_harness.operations.registry import argument_models
    from geoagent_harness.skill_registry import load_skill_registry
    models=argument_models(root)
    registry=load_skill_registry(root)
    contracts={skill:{'skill':registry.get_skill(skill).model_dump(mode='json'),
                       'arguments':models[skill].model_json_schema()} for skill in {s.skill for s in recipe.steps}}
    return hashlib.sha256(json.dumps(contracts,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _builtins():
    # Separate JSON keeps definitions inspectable; it never contains code/imports.
    path = Path(__file__).with_name('reusable_recipes.json')
    return [ReusableRecipe.model_validate(value) for value in json.loads(path.read_text())]


def catalog(root, diagnostics=None):
    from geoagent_harness.operations.registry import argument_models
    recipes = {r.id:r for r in _builtins()}
    directory = Path(root) / 'reusable-recipes'
    if directory.is_symlink():
        raise ValueError('Reusable recipe storage cannot be a symlink')
    paths = list(directory.glob('*.json'))
    if len(paths)>50:
        raise ValueError('Reusable recipe inventory exceeds 50')
    for path in paths:
        if path.is_symlink() or not path.is_file() or path.stat().st_size>65_000:
            raise ValueError('Reusable recipe record is unsafe or oversized')
        record=json.loads(path.read_text())
        if set(record)!={'definition','recipe_sha256','test_report','operation_contracts_sha256'}:
            raise ValueError('Reusable recipe record has unknown fields')
        recipe=ReusableRecipe.model_validate(record['definition'])
        if recipe.id in recipes or path.name!=recipe.id+'.json' or recipe_digest(recipe)!=record['recipe_sha256']:
            raise ValueError('Reusable recipe identity/digest conflicts')
        try:
            contracts_match=record['operation_contracts_sha256']==operation_fingerprint(recipe,root)
        except KeyError:
            contracts_match=False
        if not contracts_match:
            if diagnostics is not None:
                diagnostics.append({'id':recipe.id,'name':recipe.name,'finding':'Operation contracts changed or are unavailable; retesting and explicit migration are required'})
            continue
        recipes[recipe.id]=recipe
    available=argument_models(root)
    return {key:value for key,value in recipes.items() if all(s.skill in available for s in value.steps)}


def _parameter(value, declaration):
    expected={'string':str,'array':list,'object':dict,'integer':int,'number':(int,float),'boolean':bool}
    if declaration.type=='csv_source':
        if isinstance(value,str) and value:
            return value
        if isinstance(value,dict) and set(value)=={'recipe_output'} and isinstance(value['recipe_output'],str):
            return value
        raise ValueError('CSV source needs an original input path or an earlier recipe_output alias')
    if not isinstance(value, expected[declaration.type]) or (declaration.type in {'integer','number'} and isinstance(value,bool)):
        raise ValueError('Recipe parameter does not match declared type '+declaration.type)
    return value


def compose(uses, root, base=None, definitions=None):
    from geoagent_harness.planner.topology import plan_dependencies
    from geoagent_harness.skill_registry import load_skill_registry
    from geoagent_harness.tabular.schemas import is_table_write
    from geoagent_harness.interface_api.workflow import _check
    definitions = catalog(root) if definitions is None else definitions
    registry=load_skill_registry(root)
    steps = [s.model_copy(deep=True) for s in base.plan.steps] if base else []
    if base:
        _check(base, root)
        deps=plan_dependencies(base.plan)
        for step in steps:
            step.depends_on=deps[step.step_id]
    outputs={}
    receipts=[]
    for use in uses:
        if use.alias in outputs:
            raise ValueError('Recipe aliases must be unique')
        recipe=definitions.get(use.recipe_id)
        if recipe is None or recipe_digest(recipe)!=use.recipe_sha256:
            raise ValueError('Recipe is unavailable or its version digest changed')
        from geoagent_harness.planner.bindings import bind_recipe_parameters
        bound=bind_recipe_parameters(recipe,use.parameters)
        if set(bound)!=set(recipe.parameters):
            raise ValueError('Recipe parameters must match required names: '+', '.join(recipe.parameters))
        parameters={key:_parameter(bound[key],declaration) for key,declaration in recipe.parameters.items()}
        mapping={s.step_id:f'step_{len(steps)+i}' for i,s in enumerate(recipe.steps,1)}
        def resolve(value):
            if isinstance(value,dict):
                if set(value)=={'$parameter'}:
                    if value['$parameter'] not in parameters:
                        raise ValueError('Unknown recipe parameter reference')
                    return parameters[value['$parameter']]
                if set(value)=={'$step'}:
                    if value['$step'] not in mapping:
                        raise ValueError('Unknown local recipe step reference')
                    return mapping[value['$step']]
                return {k:resolve(v) for k,v in value.items()}
            if isinstance(value,list):
                return [resolve(v) for v in value]
            return value
        for template in recipe.steps:
            args=resolve(template.arguments)
            deps=[mapping[s] for s in template.depends_on]
            if template.csv_source_parameter:
                if any(k in args for k in ('path','source_step')):
                    raise ValueError('CSV binding must not override explicit source arguments')
                source=parameters[template.csv_source_parameter]
                if isinstance(source,str):
                    args['path']=source
                else:
                    alias=source['recipe_output']
                    if alias not in outputs or outputs[alias][1]!='table/csv-v1':
                        raise ValueError('Recipe connection requires an earlier CSV artifact, not inspection metadata')
                    args['source_step']=outputs[alias][0]
                    deps=list(dict.fromkeys([*deps,outputs[alias][0]]))
            skill=registry.get_skill(template.skill)
            steps.append(PlanStep(step_id=mapping[template.step_id],skill=template.skill,purpose=template.purpose,
                arguments=args,depends_on=deps,requires_approval=skill.approval_required,validation_required=skill.validation_required))
        producer=next(s for s in steps if s.step_id==mapping[recipe.output_step])
        actual='table/csv-v1' if is_table_write(producer.skill) else {'inspect_csv':'metadata/csv-v1','inspect_vector':'metadata/vector-v1'}.get(producer.skill)
        if actual!=recipe.output_contract:
            raise ValueError('Recipe output contract does not match its registered operation')
        outputs[use.alias]=(producer.step_id,actual)
        receipts.append({'alias':use.alias,'recipe_id':recipe.id,'version':recipe.version,'recipe_sha256':recipe_digest(recipe),'step_ids':list(mapping.values()),'output_step':producer.step_id,'output_contract':actual})
    if not uses:
        raise ValueError('Choose at least one reusable recipe')
    assumptions=list(base.plan.assumptions) if base else []
    assumptions.extend('Recipe '+r['recipe_id']+'@'+r['version']+' sha256='+r['recipe_sha256']+' alias='+r['alias']+' steps='+','.join(r['step_ids']) for r in receipts)
    result=PlannerResult(model='deterministic-recipe-composer',original_request=base.original_request if base else 'Compose registered reusable recipes',
        context_references=list(base.context_references) if base else [],warnings=list(base.warnings) if base else [],
        plan=WorkflowPlan(summary='; '.join(([base.plan.summary] if base else [])+[definitions[u.recipe_id].name for u in uses])[:2000],
                          steps=steps,assumptions=assumptions,risks=list(base.plan.risks) if base else []))
    _check(result,root)
    return result, receipts


def test_recipe(recipe, root):
    """Run declared CSV/GeoJSON fixtures in a private temporary project only."""
    from geoagent_harness.approvals import plan_sha256
    from geoagent_harness.mcp_server.settings import MCPSettings
    from geoagent_harness.planner.recipe_definition import planner_recipe_definition
    from geoagent_harness.recipes import create_recipe_approval, run_approved_recipe
    from geoagent_harness.recipes.policy import validate_recipe_policy
    from geoagent_harness.skill_registry import load_skill_registry
    allowed={'inspect_csv','inspect_vector','vector_attributes_to_csv','select_csv_columns','filter_csv_rows','handle_csv_missing','join_csv','aggregate_csv','calculate_csv_columns','export_csv'}
    if not recipe.tests or any(s.skill not in allowed for s in recipe.steps):
        raise ValueError('Registration requires fixtures and supported isolated CSV/GeoJSON operations; database, shell and arbitrary code tests are unavailable')
    reports=[]
    for fixture in recipe.tests:
        with TemporaryDirectory(prefix='actioncharter-recipe-') as temporary:
            workspace=Path(temporary)
            (workspace/'context').mkdir()
            # Copy only the declarative skill index, never secrets or project data.
            (workspace/'context/SKILLS_INDEX.yaml').write_bytes((Path(root)/'context/SKILLS_INDEX.yaml').read_bytes())
            (workspace/'data/input').mkdir(parents=True)
            (workspace/'data/output').mkdir()
            for name,content in fixture.files.items():
                path=Path(name)
                if path.parent!=Path('data/input') or path.suffix not in {'.csv','.geojson'} or len(content.encode())>16_000:
                    raise ValueError('Fixture inputs must be bounded CSV/GeoJSON files directly under data/input')
                (workspace/path).write_text(content)
            use=RecipeUse(recipe_id=recipe.id,recipe_sha256=recipe_digest(recipe),alias='test',parameters=fixture.parameters)
            result,_=compose([use],workspace,definitions={recipe.id:recipe})
            compiled=planner_recipe_definition(result,plan_sha256(result.plan))
            registry=load_skill_registry(workspace)
            policy=validate_recipe_policy(compiled,registry=registry)
            if not policy.write_step_ids:
                raise ValueError('Current fixture verifier requires an expected CSV artifact')
            approval,_=create_recipe_approval(recipe=compiled,registry=registry,step_ids=policy.approval_required_step_ids,
                decision='approved',approver='isolated-recipe-fixture',reason='Temporary fixture scope only',approval_root=workspace/'approvals')
            settings=MCPSettings(project_root=workspace,input_root=workspace/'data/input',output_root=workspace/'data/output',enable_write_tools=True)
            try:
                run=run_approved_recipe(recipe=compiled,approval=approval,registry=registry,settings=settings)
            except Exception as error:
                raise ValueError('Recipe fixture execution or verification failed in its temporary workspace') from error
            if run.final_status!='validated_success':
                raise ValueError('Recipe fixture did not pass independent validation')
            outputs={s.arguments['target_path'] for s in result.plan.steps if 'target_path' in s.arguments}
            if not set(fixture.expected_csv).issubset(outputs):
                raise ValueError('Expected fixture outputs must name generated CSV artifacts')
            for path,expected in fixture.expected_csv.items():
                if (workspace/path).read_text()!=expected:
                    raise ValueError('Recipe fixture output differs from its declared expectation')
            reports.append({'passed':True,'steps':len(run.step_results),'expected_outputs':len(fixture.expected_csv)})
    return {'status':'fixture_verified','tests':reports,'live_data_used':False,'execution_authority_granted':False}


def recipe_action(request, *, project_root):
    from geoagent_harness.interface_api.workflow import EditRequest,validate_edit
    from geoagent_harness.interface_api.server import _trusted_root
    root=_trusted_root(project_root)
    if request.action in {'search','inspect'}:
        from .discovery import DiscoveryRequest,discover
        from geoagent_harness.operations.registry import argument_models
        return discover(DiscoveryRequest(action=request.action,query=request.query,recipe_id=request.recipe_id,method_id=request.method_id),
                        root=root,conversation_id=request.conversation_id,available=list(argument_models(root)),use_history=bool(request.conversation_id))
    if request.action=='list':
        query=request.query.casefold()
        unavailable=[]
        available=catalog(root,unavailable)
        from .successful import inventory
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
        from geoagent_harness.planner.recipe_authoring import prepare_recipe
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
        if request.definition.id in catalog(root) or (root/'reusable-recipes'/(request.definition.id+'.json')).exists():
            raise ValueError('Recipe ID already registered; in-place replacement is unavailable')
        directory=root/'reusable-recipes'
        if directory.is_symlink():
            raise ValueError('Recipe storage is unsafe')
        directory.mkdir(exist_ok=True)
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
