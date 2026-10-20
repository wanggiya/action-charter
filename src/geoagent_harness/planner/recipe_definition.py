"""Single deterministic mapping from reviewed Planner results to recipes."""
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.planner.topology import plan_dependencies
from geoagent_harness.recipes.schemas import RecipeStep, WorkflowRecipe

class PlannerRecipeDefinitionError(ValueError):
    """A plan contains capabilities unsupported by the recipe dispatcher."""

def planner_recipe_definition(result: PlannerResult, plan_digest: str) -> WorkflowRecipe:
    """Reconstruct the exact deterministic recipe definition without granting authority."""

    supported_outputs = {
        "inspect_vector": ["source_metadata"],
        "convert_vector": ["converted_vector"],
        "inspect_raster": ["raster_metadata"],
        "convert_raster": ["converted_raster"],
        "load_vector_to_postgis": ["postgis_load_result"],
        "validate_postgis_layer": ["postgis_validation"],
        "generate_report": ["workflow_report"],
    }
    from geoagent_harness.tabular.schemas import ARGUMENTS, is_extension, is_table_write
    supported_outputs.update({step.skill: ["table_output"] for step in result.plan.steps if is_extension(step.skill)})
    supported_outputs.update({id: ['table_metadata' if id == 'inspect_csv' else 'table_output'] for id in ARGUMENTS})
    unsupported = [step.skill for step in result.plan.steps if step.skill not in supported_outputs]
    if unsupported:
        raise PlannerRecipeDefinitionError("plan contains skills not supported by the governed recipe dispatcher: " + ", ".join(unsupported))
    dependencies = plan_dependencies(result.plan)
    # The normal writer gate already binds the entire recipe; the plan service
    # separately verifies any stricter plan scope. Preserve those legacy recipes.
    # Evidence-only workflows have no such gate, so retain their plan gates here.
    has_writer_gate = any(is_table_write(step.skill) or step.skill in {
        'convert_vector', 'convert_raster', 'load_vector_to_postgis',
    } for step in result.plan.steps)
    steps = [RecipeStep(
        step_id=step.step_id,
        skill_id=step.skill,
        depends_on=dependencies[step.step_id],
        arguments=step.arguments,
        # Preserve stricter plan gates for operations that normally need none.
        # Existing transformation recipes retain their canonical bytes/digests.
        additional_approval_required=not has_writer_gate and step.requires_approval and step.skill in {
            'inspect_vector', 'inspect_raster', 'inspect_csv',
            'validate_postgis_layer', 'generate_report',
        },
        output_ids=[f"table_{step.step_id}"] if is_table_write(step.skill) else supported_outputs[step.skill],
    ) for index, step in enumerate(result.plan.steps)]
    recipe = WorkflowRecipe(
        recipe_id=f"planner-{plan_digest[:16]}",
        summary=result.plan.summary,
        original_request=result.original_request,
        steps=steps,
    )
    return recipe

