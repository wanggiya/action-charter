"""Existing spatial CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
import typer


def inspect_vector_command(
    path: Annotated[Path, typer.Argument(help="Dataset beneath data/input.")],
    input_root: Annotated[
        Path,
        typer.Option(
            "--input-root",
            help="Trusted input root; intended for deployment configuration/tests.",
        ),
    ] = Path("data/input"),
    pretty: Annotated[
        bool, typer.Option("--pretty", help="Indent the JSON response.")
    ] = False,
) -> None:
    """Inspect an approved vector dataset without executing a shell."""
    from geoagent_harness.data.spatial.skills.inspect_vector.service import InspectVectorError
    from geoagent_harness.task_actions.command_actions import skills_inspect_vector_service__inspect_vector as inspect_vector
    try:
        result = inspect_vector(path=path, input_root=input_root)
    except InspectVectorError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )


def assess_spatial_data_contract_command(
    path: Annotated[
        Path,
        typer.Argument(help="Vector dataset beneath the approved input root."),
    ],
    contract_file: Annotated[
        Path,
        typer.Argument(help="JSON or YAML spatial-data contract."),
    ],
    input_root: Annotated[
        Path,
        typer.Option("--input-root"),
    ] = Path("data/input"),
    contract_root: Annotated[
        Path,
        typer.Option("--contract-root"),
    ] = Path("spatial-contracts"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Deterministically assess a vector dataset without mutation."""

    from geoagent_harness.contracts.spatial import SpatialDataContractAssessmentError
    from geoagent_harness.contracts.spatial import SpatialDataContractStorageError
    from geoagent_harness.task_actions.command_actions import spatial_contracts__assess_spatial_data_contract as assess_spatial_data_contract, spatial_contracts__load_spatial_data_contract as load_spatial_data_contract

    try:
        contract = load_spatial_data_contract(
            contract_file,
            contract_root=contract_root,
        )
        result = assess_spatial_data_contract(
            path=path,
            contract=contract,
            input_root=input_root,
        )
    except (
        SpatialDataContractAssessmentError,
        SpatialDataContractStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

    if not result.passed:
        raise typer.Exit(code=1)


def assess_pilot_demo_readiness_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help="Pilot demonstration definition beneath the project root."
        ),
    ] = Path("demonstrations/checkpoint14f/DEMO.json"),
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help="Trusted clean-checkout project root.",
        ),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Verify the fixed pilot story without taking any action."""

    from geoagent_harness.apps.pilot_demo import PilotDemoError, assess_pilot_demo_readiness
    from geoagent_harness.contracts.spatial import SpatialDataContractAssessmentError
    from geoagent_harness.contracts.spatial import SpatialDataContractStorageError

    try:
        result = assess_pilot_demo_readiness(
            definition_file,
            project_root=project_root,
        )
    except (
        PilotDemoError,
        SpatialDataContractAssessmentError,
        SpatialDataContractStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

    if not result.repository_ready:
        raise typer.Exit(code=1)


def plan_convert_vector_command(
    path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Vector dataset beneath the "
                "approved input root."
            ),
        ),
    ],
    target_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "New .geojson or .gpkg file beneath "
                "the approved output root."
            ),
        ),
    ],
    source_layer: Annotated[
        str | None,
        typer.Option("--source-layer"),
    ] = None,
    target_layer: Annotated[
        str | None,
        typer.Option("--target-layer"),
    ] = None,
    input_root: Annotated[
        Path,
        typer.Option("--input-root"),
    ] = Path("data/input"),
    output_root: Annotated[
        Path,
        typer.Option("--output-root"),
    ] = Path("data/output"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Plan a controlled vector conversion without writing."""

    from geoagent_harness.data.spatial.skills.convert_vector import ConvertVectorPolicyError
    from geoagent_harness.task_actions.command_actions import skills_convert_vector__plan_vector_conversion as plan_vector_conversion

    try:
        plan = plan_vector_conversion(
            path=path,
            target_path=target_path,
            input_root=input_root,
            output_root=output_root,
            source_layer=source_layer,
            target_layer=target_layer,
        )
    except ConvertVectorPolicyError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            plan.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def convert_vector_command(
    path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Vector dataset beneath the "
                "approved input root."
            ),
        ),
    ],
    target_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "New .geojson or .gpkg file beneath "
                "the approved output root."
            ),
        ),
    ],
    source_layer: Annotated[
        str | None,
        typer.Option("--source-layer"),
    ] = None,
    target_layer: Annotated[
        str | None,
        typer.Option("--target-layer"),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Execute a controlled conversion pending validation."""

    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.data.spatial.skills.convert_vector import ConvertVectorError
    from geoagent_harness.task_actions.command_actions import skills_convert_vector__convert_vector as convert_vector

    try:
        result = convert_vector(
            path=path,
            target_path=target_path,
            settings=load_settings(),
            source_layer=source_layer,
            target_layer=target_layer,
        )
    except (
        ConvertVectorError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def validate_vector_conversion_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Original vector dataset.",
        ),
    ],
    target_path: Annotated[
        Path,
        typer.Argument(
            help="Converted vector dataset.",
        ),
    ],
    source_layer: Annotated[
        str | None,
        typer.Option("--source-layer"),
    ] = None,
    target_layer: Annotated[
        str | None,
        typer.Option("--target-layer"),
    ] = None,
    input_root: Annotated[
        Path,
        typer.Option("--input-root"),
    ] = Path("data/input"),
    output_root: Annotated[
        Path,
        typer.Option("--output-root"),
    ] = Path("data/output"),
    extent_tolerance: Annotated[
        float,
        typer.Option("--extent-tolerance"),
    ] = 1e-8,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Deterministically validate a vector conversion."""

    from geoagent_harness.data.spatial.skills.convert_vector import ConvertVectorValidationError
    from geoagent_harness.task_actions.command_actions import skills_convert_vector__validate_vector_conversion as validate_vector_conversion

    try:
        result = validate_vector_conversion(
            path=path,
            target_path=target_path,
            input_root=input_root,
            output_root=output_root,
            source_layer=source_layer,
            target_layer=target_layer,
            extent_tolerance=extent_tolerance,
        )
    except ConvertVectorValidationError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if not result.passed:
        raise typer.Exit(code=1)


def load_vector_to_postgis_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Vector dataset beneath the approved input root."
        ),
    ],
    target_schema: Annotated[
        str,
        typer.Option("--schema", help="Approved target schema."),
    ] = "agent_sandbox",
    target_table: Annotated[
        str,
        typer.Option("--table", help="New target table name."),
    ] = "loaded_vector",
    source_layer: Annotated[
        str | None,
        typer.Option(
            "--layer",
            help="Required when the source has multiple layers.",
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Load one approved vector layer into a new PostGIS table."""
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.data.spatial.skills.load_vector_to_postgis.service import LoadVectorError
    from geoagent_harness.task_actions.command_actions import skills_load_vector_to_postgis_service__load_vector_to_postgis as load_vector_to_postgis

    try:
        result = load_vector_to_postgis(
            path=path,
            target_schema=target_schema,
            target_table=target_table,
            source_layer=source_layer,
            settings=load_settings(),
        )
    except (LoadVectorError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )


def validate_postgis_layer_command(
    target_schema: Annotated[
        str,
        typer.Option("--schema", help="Approved PostGIS schema."),
    ] = "agent_sandbox",
    target_table: Annotated[
        str,
        typer.Option("--table", help="PostGIS table to validate."),
    ] = "checkpoint3b_sample_points",
    expected_row_count: Annotated[
        int | None,
        typer.Option("--expected-row-count"),
    ] = None,
    expected_srid: Annotated[
        int | None,
        typer.Option("--expected-srid"),
    ] = None,
    expected_geometry_type: Annotated[
        str | None,
        typer.Option("--expected-geometry-type"),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Deterministically validate one approved PostGIS layer."""
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.core.verification.postgis import PostGISVerificationError
    from geoagent_harness.task_actions.command_actions import verifier_postgis__validate_postgis_layer as validate_postgis_layer

    try:
        result = validate_postgis_layer(
            target_schema=target_schema,
            target_table=target_table,
            expected_row_count=expected_row_count,
            expected_srid=expected_srid,
            expected_geometry_type=expected_geometry_type,
            settings=load_settings(),
        )
    except (PostGISVerificationError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

    if not result.passed:
        raise typer.Exit(code=1)
