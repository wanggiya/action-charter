from geoagent_harness.core.policy.recipe_definition import PlannerRecipeDefinitionError, planner_recipe_definition
"""Single deterministic mapping from reviewed Planner results to recipes."""
from pathlib import Path
from geoagent_harness.contracts.planning import PlannerResult
from geoagent_harness.contracts.graph import plan_dependencies
from geoagent_harness.contracts.recipes import RecipeStep, WorkflowRecipe



from geoagent_harness.contracts.actions import EditRequest
from geoagent_harness.contracts.snakemake import TERMINAL


def has_export(result):
    return any(step.skill in TERMINAL for step in result.plan.steps)

def _check(result, root):
    from geoagent_harness.platform.skill_registry import load_skill_registry
    from geoagent_harness.core.policy.plan import validate_plan_policy
    from geoagent_harness.capabilities.registry.registry import argument_models
    from geoagent_harness.core.policy.approvals import plan_sha256
    from geoagent_harness.core.policy.recipe import validate_recipe_policy
    from geoagent_harness.contracts.errors import InterfaceApiError
    from geoagent_harness.capabilities.recipes.execution.dispatcher import _validate_registered_skill, RecipeDispatchError
    from geoagent_harness.data.discovery.input import check_task_input
    from geoagent_harness.contracts.intent import IntentError
    if has_export(result):
        return validate_export_plan(result, root)
    registry = load_skill_registry(root)
    validate_plan_policy(result.plan, available_skills={s.id for s in registry.implemented_skills()})
    models = argument_models(root)
    for step in result.plan.steps:
        if step.skill not in models:
            raise InterfaceApiError('This operation is not supported by current workflow execution: ' + step.skill)
        try:
            _validate_registered_skill(skill_id=step.skill, registry=registry)
        except RecipeDispatchError as error:
            raise InterfaceApiError('Registered operation does not match the trusted dispatcher') from error
        typed = models[step.skill].model_validate(step.arguments)
        if step.skill.startswith('ext_'):
            from geoagent_harness.platform.storage.operation_packages import installed_packages
            from geoagent_harness.contracts.operation_packages import package_sha
            if typed.package_sha256 != package_sha(installed_packages(root)[step.skill]):
                raise InterfaceApiError('Installed package digest does not match this proposal')
        for input_key in ('path', 'right_path', 'codebook_path'):
            if step.arguments.get(input_key) is None:
                continue
            try:
                check_task_input(project_root=root, input_path=step.arguments[input_key])
            except IntentError as error:
                raise InterfaceApiError('Input must be an available regular file under data/input') from error
        if 'target_path' in step.arguments and not step.arguments['target_path'].startswith('data/output/'):
            raise InterfaceApiError('Output paths must remain under data/output')
    if any(step.skill == 'calculate_csv_columns' for step in result.plan.steps):
        from geoagent_harness.data.tabular.policy import preflight_calculations
        preflight_calculations(result.plan.steps, root)
    recipe = planner_recipe_definition(result, plan_sha256(result.plan))
    policy = validate_recipe_policy(recipe, registry=registry)
    return registry, recipe, policy

def validate_export_plan(result, root):
    from geoagent_harness.platform.storage import repositories
    from geoagent_harness.platform.paths import runtime_store_path
    from geoagent_harness.core.policy.approvals import plan_sha256
    from geoagent_harness.core.policy.plan import validate_plan_policy
    from geoagent_harness.contracts.graph import plan_dependencies, plan_topological_order, ancestors
    from geoagent_harness.contracts.snakemake import EXPORT, VERIFY, TERMINAL, ExportArguments, VerifyArguments
    from geoagent_harness.contracts.errors import InterfaceApiError
    from geoagent_harness.platform.skill_registry import load_skill_registry
    registry = load_skill_registry(root)
    validate_plan_policy(result.plan, available_skills={s.id for s in registry.implemented_skills()})
    export = [s for s in result.plan.steps if s.skill == EXPORT]
    verify = [s for s in result.plan.steps if s.skill == VERIFY]
    if len(export) != 1 or len(verify) != 1:
        raise InterfaceApiError('Use exactly one Snakemake export and one verification block')
    args = ExportArguments.model_validate(export[0].arguments)
    VerifyArguments.model_validate(verify[0].arguments)
    if not export[0].requires_approval or not export[0].validation_required or not verify[0].validation_required:
        raise InterfaceApiError('Snakemake export requires approval and package verification')
    path = runtime_store_path(root, 'plans') / args.source_plan_filename
    if path.is_symlink() or (runtime_store_path(root, 'plans')).is_symlink():
        raise InterfaceApiError('Source plan artifact is unsafe')
    source = repositories(root).documents('plans', directory=runtime_store_path(root, 'plans')).load((path).name)
    if plan_sha256(source.plan) != args.source_plan_sha256:
        raise InterfaceApiError('Snakemake source plan digest no longer matches')
    if has_export(source):
        raise InterfaceApiError('Snakemake export must reference an original operation plan, not another export plan')
    source_registry, recipe, policy = _check(source, root)
    prefix = [s for s in result.plan.steps if s.skill not in TERMINAL]
    deps = plan_dependencies(result.plan)
    source_deps = plan_dependencies(source.plan)
    def scope(steps):
        values = []
        for step in steps:
            value = step.model_dump(mode='json')
            value.pop('depends_on', None)
            values.append(value)
        return values
    if prefix and (scope(prefix) != scope(source.plan.steps) or any(deps.get(step.step_id) != source_deps[step.step_id] for step in prefix)):
        raise InterfaceApiError('Retained operations must exactly match the saved Snakemake source plan')
    ordered = plan_topological_order(result.plan)
    if not set(s.step_id for s in prefix).issubset(ancestors(export[0].step_id, deps)):
        raise InterfaceApiError('Snakemake export must follow every retained source operation')
    if export[0].step_id not in ancestors(verify[0].step_id, deps) or ordered[-2:] != [export[0].step_id, verify[0].step_id]:
        raise InterfaceApiError('Snakemake verification must follow export at the end of the workflow')
    return source_registry, recipe, policy

def validate_edit(request: EditRequest, *, project_root: Path):
    from geoagent_harness.core.policy.plan import normalize_plan_input_filenames
    from geoagent_harness.core.policy.approvals import plan_sha256
    from geoagent_harness.platform.project import _trusted_root
    result = request.planner_result
    normalize_plan_input_filenames(result.plan)
    from geoagent_harness.data.tabular.bindings import bind_streaming_preparation
    bind_streaming_preparation(result.plan,project_root)
    _check(result, _trusted_root(project_root))
    return dict(schema_version='1.0', status='planned_not_saved',
                **result.model_dump(mode='json'), allowed_skill_ids=list(dict.fromkeys(s.skill for s in result.plan.steps)),
                plan_sha256=plan_sha256(result.plan), plan_saved=False, approval_performed=False, execution_performed=False)
