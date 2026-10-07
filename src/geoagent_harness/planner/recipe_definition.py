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
    unsupported = [step.skill for step in result.plan.steps if step.skill not in supported_outputs]
    if unsupported:
        raise PlannerRecipeDefinitionError("plan contains skills not supported by the governed recipe dispatcher: " + ", ".join(unsupported))
    dependencies = plan_dependencies(result.plan)
    steps = [RecipeStep(
        step_id=step.step_id,
        skill_id=step.skill,
        depends_on=dependencies[step.step_id],
        arguments=step.arguments,
        output_ids=supported_outputs[step.skill],
    ) for index, step in enumerate(result.plan.steps)]
    recipe = WorkflowRecipe(
        recipe_id=f"planner-{plan_digest[:16]}",
        summary=result.plan.summary,
        original_request=result.original_request,
        steps=steps,
    )
    return recipe

