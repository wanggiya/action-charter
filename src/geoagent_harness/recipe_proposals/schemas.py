"""Typed, non-executable recipe proposals."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from geoagent_harness.recipes.schemas import (
    RecipeValidation,
    WorkflowRecipe,
)


class InspectVectorProposalParameters(BaseModel):
    """Candidate parameters for vector inspection."""

    model_config = ConfigDict(extra="forbid")

    path: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )
    source_layer: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

class InspectRasterProposalParameters(BaseModel):
    """Candidate parameters for raster inspection."""

    model_config = ConfigDict(extra="forbid")

    path: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )

class ConvertVectorProposalParameters(BaseModel):
    """Candidate parameters for inspection and conversion."""

    model_config = ConfigDict(extra="forbid")

    path: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )
    source_layer: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    target_path: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )
    target_layer: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    target_format: Literal[
        "geojson",
        "geopackage",
    ] | None = None


class VectorPostGISProposalParameters(BaseModel):
    """Candidate parameters for a vector-to-PostGIS workflow."""

    model_config = ConfigDict(extra="forbid")

    path: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )
    source_layer: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    target_schema: str | None = Field(
        default=None,
        pattern=r"^[a-z_][a-z0-9_]{0,62}$",
    )
    target_table: str | None = Field(
        default=None,
        pattern=r"^[a-z_][a-z0-9_]{0,62}$",
    )


class InspectVectorTemplateSelection(BaseModel):
    """Selection of the read-only inspection template."""

    model_config = ConfigDict(extra="forbid")

    template_id: Literal[
        "inspect_vector"
    ] = "inspect_vector"

    parameters: InspectVectorProposalParameters

class InspectRasterTemplateSelection(BaseModel):
    """Selection of the read-only raster inspection template."""

    model_config = ConfigDict(extra="forbid")

    template_id: Literal[
        "inspect_raster"
    ] = "inspect_raster"

    parameters: InspectRasterProposalParameters

class ConvertVectorTemplateSelection(BaseModel):
    """Selection of the controlled conversion template."""

    model_config = ConfigDict(extra="forbid")

    template_id: Literal[
        "inspect_and_convert_vector"
    ] = "inspect_and_convert_vector"

    parameters: ConvertVectorProposalParameters


class VectorPostGISTemplateSelection(BaseModel):
    """Selection of the approved PostGIS template."""

    model_config = ConfigDict(extra="forbid")

    template_id: Literal[
        "vector_to_postgis"
    ] = "vector_to_postgis"

    parameters: VectorPostGISProposalParameters


RecipeTemplateSelection = Annotated[
    (
        InspectVectorTemplateSelection
        | InspectRasterTemplateSelection
        | ConvertVectorTemplateSelection
        | VectorPostGISTemplateSelection
    ),
    Field(discriminator="template_id"),
]


class RecipeProposal(BaseModel):
    """Model-produced intent that cannot execute."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    status: Literal[
        "proposed_not_compiled"
    ] = "proposed_not_compiled"

    original_request: str = Field(
        min_length=1,
        max_length=8000,
    )
    summary: str = Field(
        min_length=1,
        max_length=2000,
    )

    recipe_id_hint: str | None = Field(
        default=None,
        pattern=(
            r"^[a-z0-9]"
            r"[a-z0-9_-]{0,100}$"
        ),
    )

    selection: RecipeTemplateSelection

    assumptions: list[str] = Field(
        default_factory=list,
        max_length=20,
    )
    missing_information: list[str] = Field(
        default_factory=list,
        max_length=20,
    )
    warnings: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    compilation_performed: Literal[False] = False
    execution_requested: Literal[False] = False
    approval_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class RecipeProposalAssessment(BaseModel):
    """Deterministic readiness assessment."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    template_id: Literal[
        "inspect_vector",
        "inspect_raster",
        "inspect_and_convert_vector",
        "vector_to_postgis",
    ]

    ready_for_compilation: bool

    required_fields: list[str]
    missing_fields: list[str] = Field(
        default_factory=list
    )
    unavailable_skills: list[str] = Field(
        default_factory=list
    )
    policy_conflicts: list[str] = Field(
        default_factory=list
    )
    clarification_questions: list[str] = Field(
        default_factory=list
    )

    reason: str = Field(
        min_length=1,
        max_length=2000,
    )

    proposal_modified: Literal[False] = False
    compilation_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class RecipeCompilationResult(BaseModel):
    """Deterministic compilation of one ready proposal."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    proposal_assessment: (
        RecipeProposalAssessment
    )

    recipe: WorkflowRecipe
    recipe_validation: RecipeValidation

    compilation_performed: Literal[True] = True
    recipe_saved: Literal[False] = False
    approval_performed: Literal[False] = False
    execution_performed: Literal[False] = False

class RecipeProposalGenerationResult(BaseModel):
    """Validated result from the untrusted model boundary."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    model: str = Field(
        min_length=1,
        max_length=500,
    )
    proposal: RecipeProposal

    proposal_schema_validated: Literal[True] = True

    assessment_performed: Literal[False] = False
    compilation_performed: Literal[False] = False
    recipe_saved: Literal[False] = False
    approval_performed: Literal[False] = False
    execution_performed: Literal[False] = False


class RecipeProposalPipelineResult(BaseModel):
    """Proposal generation followed by safe compilation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    generation: RecipeProposalGenerationResult
    compilation: RecipeCompilationResult

    proposal_generated: Literal[True] = True
    proposal_assessed: Literal[True] = True
    compilation_performed: Literal[True] = True

    recipe_saved: Literal[False] = False
    approval_performed: Literal[False] = False
    execution_performed: Literal[False] = False
    
class RecipeOperatorReview(BaseModel):
    """Review boundary before explicit recipe storage."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    status: Literal[
        "clarification_required",
        "ready_for_operator_review",
    ]

    generation: RecipeProposalGenerationResult
    assessment: RecipeProposalAssessment
    compilation: RecipeCompilationResult | None = None

    clarification_questions: list[str] = Field(
        default_factory=list
    )

    proposal_generated: Literal[True] = True
    assessment_performed: Literal[True] = True
    compilation_performed: bool

    recipe_saved: Literal[False] = False
    approval_performed: Literal[False] = False
    execution_performed: Literal[False] = False

    @model_validator(mode="after")
    def review_state_is_consistent(
        self,
    ) -> "RecipeOperatorReview":
        if self.status == "ready_for_operator_review":
            if not self.assessment.ready_for_compilation:
                raise ValueError(
                    "ready review requires a ready "
                    "proposal assessment"
                )

            if self.compilation is None:
                raise ValueError(
                    "ready review requires compilation"
                )

            if self.compilation_performed is not True:
                raise ValueError(
                    "ready review must confirm compilation"
                )

            if self.clarification_questions:
                raise ValueError(
                    "ready review cannot contain "
                    "clarification questions"
                )

        if self.status == "clarification_required":
            if self.assessment.ready_for_compilation:
                raise ValueError(
                    "clarification state cannot contain "
                    "a ready assessment"
                )

            if self.compilation is not None:
                raise ValueError(
                    "clarification state cannot contain "
                    "a compiled recipe"
                )

            if self.compilation_performed:
                raise ValueError(
                    "clarification state cannot claim "
                    "compilation"
                )

            if not self.clarification_questions:
                raise ValueError(
                    "clarification state requires at "
                    "least one question"
                )

        return self

class RecipeOperatorSaveResult(BaseModel):
    """Result of explicitly saving one reviewed recipe."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    recipe_id: str
    recipe_sha256: str = Field(
        pattern=r"^[a-f0-9]{64}$"
    )
    recipe_filename: str = Field(
        min_length=1,
        pattern=(
            r"^[a-z0-9][a-z0-9_-]*"
            r"\.[a-f0-9]{64}\.json$"
        ),
    )

    source_review_status: Literal[
        "ready_for_operator_review"
    ] = "ready_for_operator_review"

    recipe_saved: Literal[True] = True
    approval_performed: Literal[False] = False
    execution_performed: Literal[False] = False
