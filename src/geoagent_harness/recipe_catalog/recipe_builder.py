"""Compatibility import for the former recipe Builder role.

New callers use Planner-owned authoring. Historical imports remain available;
this module no longer loads or invokes the Builder agent.
"""
from geoagent_harness.planner.recipe_authoring import (
    RecipeAssessment, prepare_recipe,
)

__all__ = ['RecipeAssessment', 'prepare_recipe']
