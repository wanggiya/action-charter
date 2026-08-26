"""Typed schemas for the data-only recipe catalog."""

from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


_SAFE_IDENTIFIER = (
    r"^[a-z][a-z0-9_]*$"
)

_STEP_ID = (
    r"^step_[1-9][0-9]*$"
)

RecipeParameterProfile = Literal[
    "vector_inspection",
    "raster_inspection",
    "raster_conversion",
    "vector_conversion",
    "vector_postgis",
]

RecipeAssessmentPolicy = Literal[
    "none",
    "vector_conversion",
    "raster_conversion",
]

class RecipeTemplateArgument(BaseModel):
    """One safe source for a compiled argument."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    source: Literal[
        "parameter",
        "literal",
    ]

    value: str = Field(
        min_length=1,
        max_length=2000,
    )

    omit_if_none: bool = False


class RecipeTemplateStep(BaseModel):
    """One non-executable declarative recipe step."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    step_id: str = Field(
        pattern=_STEP_ID,
    )

    skill_id: str = Field(
        pattern=_SAFE_IDENTIFIER,
    )

    depends_on: tuple[str, ...] = (
        Field(default_factory=tuple)
    )

    arguments: dict[
        str,
        RecipeTemplateArgument,
    ] = Field(default_factory=dict)

    output_ids: tuple[str, ...] = Field(
        min_length=1
    )

    @field_validator("depends_on")
    @classmethod
    def dependencies_are_unique_and_safe(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError(
                "template step dependencies "
                "must be unique"
            )

        for value in values:
            if not value.startswith("step_"):
                raise ValueError(
                    "template contains an invalid "
                    "dependency step ID"
                )

        return values

    @field_validator("arguments")
    @classmethod
    def argument_names_are_safe(
        cls,
        values: dict[
            str,
            RecipeTemplateArgument,
        ],
    ) -> dict[
        str,
        RecipeTemplateArgument,
    ]:
        for name in values:
            if (
                not name
                or not name[0].isalpha()
                or not all(
                    character.islower()
                    or character.isdigit()
                    or character == "_"
                    for character in name
                )
            ):
                raise ValueError(
                    "template contains an invalid "
                    "argument name"
                )

        return values

    @field_validator("output_ids")
    @classmethod
    def output_ids_are_unique_and_safe(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError(
                "template step output IDs "
                "must be unique"
            )

        for value in values:
            if (
                not value
                or not value[0].isalpha()
                or not all(
                    character.islower()
                    or character.isdigit()
                    or character == "_"
                    for character in value
                )
            ):
                raise ValueError(
                    "template contains an invalid "
                    "output ID"
                )

        return values


class RecipeTemplateCatalogEntry(BaseModel):
    """One non-executable recipe-template declaration."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    template_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=_SAFE_IDENTIFIER,
    )
    
    parameter_profile: (
        RecipeParameterProfile
    )

    assessment_policy: (
        RecipeAssessmentPolicy
    ) = "none"

    skill_ids: tuple[str, ...] = Field(
        min_length=1
    )

    required_parameters: tuple[
        str,
        ...
    ] = Field(min_length=1)

    steps: tuple[
        RecipeTemplateStep,
        ...
    ] = Field(min_length=1)

    @field_validator("skill_ids")
    @classmethod
    def skill_ids_are_valid(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError(
                "template skill IDs must be unique"
            )

        for value in values:
            if (
                not value
                or not value[0].isalpha()
                or not all(
                    character.islower()
                    or character.isdigit()
                    or character == "_"
                    for character in value
                )
            ):
                raise ValueError(
                    "template contains an invalid "
                    "skill ID"
                )

        return values

    @field_validator("required_parameters")
    @classmethod
    def parameters_are_valid(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError(
                "template required parameters "
                "must be unique"
            )

        for value in values:
            if (
                not value
                or not value[0].isalpha()
                or not all(
                    character.islower()
                    or character.isdigit()
                    or character == "_"
                    for character in value
                )
            ):
                raise ValueError(
                    "template contains an invalid "
                    "parameter name"
                )

        return values

    @model_validator(mode="after")
    def graph_is_consistent(
        self,
    ) -> "RecipeTemplateCatalogEntry":
        step_ids = [
            step.step_id
            for step in self.steps
        ]

        if len(step_ids) != len(set(step_ids)):
            raise ValueError(
                "template step IDs must be unique"
            )

        expected_step_ids = [
            f"step_{index}"
            for index in range(
                1,
                len(self.steps) + 1,
            )
        ]

        if step_ids != expected_step_ids:
            raise ValueError(
                "template steps must use contiguous "
                "IDs in execution order"
            )

        available_steps: set[str] = set()
        output_ids: list[str] = []

        for step in self.steps:
            if not set(
                step.depends_on
            ).issubset(available_steps):
                raise ValueError(
                    "template step depends on an "
                    "unknown or later step"
                )

            available_steps.add(
                step.step_id
            )
            output_ids.extend(
                step.output_ids
            )

        if len(output_ids) != len(
            set(output_ids)
        ):
            raise ValueError(
                "template output IDs must be unique"
            )

        graph_skill_ids = tuple(
            step.skill_id
            for step in self.steps
        )

        if graph_skill_ids != self.skill_ids:
            raise ValueError(
                "template skill IDs must match "
                "the declared step graph"
            )

        parameter_references = {
            argument.value
            for step in self.steps
            for argument in step.arguments.values()
            if argument.source == "parameter"
        }

        unknown_required = (
            set(self.required_parameters)
            - parameter_references
        )

        if unknown_required:
            raise ValueError(
                "required parameters must be used "
                "by the step graph"
            )

        return self


class RecipeTemplateCatalog(BaseModel):
    """Strict collection of data-only templates."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    schema_version: Literal["1.0"] = "1.0"

    templates: tuple[
        RecipeTemplateCatalogEntry,
        ...
    ] = Field(min_length=1)

    @field_validator("templates")
    @classmethod
    def template_ids_are_unique(
        cls,
        templates: tuple[
            RecipeTemplateCatalogEntry,
            ...
        ],
    ) -> tuple[
        RecipeTemplateCatalogEntry,
        ...
    ]:
        identifiers = [
            template.template_id
            for template in templates
        ]

        if len(identifiers) != len(
            set(identifiers)
        ):
            raise ValueError(
                "recipe catalog contains duplicate "
                "template IDs"
            )

        return templates

    def get_template(
        self,
        template_id: str,
    ) -> RecipeTemplateCatalogEntry:
        """Return one template or fail closed."""

        for template in self.templates:
            if (
                template.template_id
                == template_id
            ):
                return template

        raise KeyError(
            f"recipe template "
            f"{template_id!r} is not registered"
        )
        
