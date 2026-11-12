"""Existing raster CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
import typer


def inspect_raster_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Raster dataset beneath the input root."
        ),
    ],
    input_root: Annotated[
        Path,
        typer.Option("--input-root"),
    ] = Path("data/input"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Inspect one raster dataset without modifying it."""

    from geoagent_harness.data.spatial.adapters.raster_inspection import RasterInspectionError
    from geoagent_harness.data.spatial.skills.inspect_raster.policy import InspectRasterPolicyError
    from geoagent_harness.data.spatial.skills.inspect_raster.schemas import InspectRasterArguments
    from geoagent_harness.task_actions.command_actions import skills_inspect_raster_service__inspect_raster as inspect_raster

    try:
        result = inspect_raster(
            InspectRasterArguments(
                path=path,
                input_root=input_root,
            )
        )
    except (
        InspectRasterPolicyError,
        RasterInspectionError,
        OSError,
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


def plan_convert_raster_command(
    path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Raster dataset beneath the "
                "approved input root."
            )
        ),
    ],
    target_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "New .tif file beneath the "
                "approved output root."
            )
        ),
    ],
    target_crs: Annotated[
        str,
        typer.Option(
            "--target-crs",
            help="Required target CRS.",
        ),
    ],
    resampling: Annotated[
        str,
        typer.Option(
            "--resampling",
            help=(
                "Allowlisted method: nearest, "
                "bilinear, or cubic."
            ),
        ),
    ] = "nearest",
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
    """Plan raster conversion without writing output."""

    from geoagent_harness.platform.settings import MCPSettings
    from geoagent_harness.data.spatial.skills.convert_raster.policy import ConvertRasterPolicyError
    from geoagent_harness.task_actions.command_actions import skills_convert_raster_policy__validate_convert_raster_request as validate_convert_raster_request
    from geoagent_harness.data.spatial.skills.convert_raster.schemas import ConvertRasterArguments

    try:
        plan = validate_convert_raster_request(
            arguments=ConvertRasterArguments(
                path=path,
                target_path=target_path,
                target_crs=target_crs,
                resampling=resampling,
            ),
            settings=MCPSettings(
                input_root=input_root,
                output_root=output_root,
            ),
        )
    except (
        ConvertRasterPolicyError,
        ValueError,
    ) as exc:
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


def convert_raster_command(
    path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Raster dataset beneath the "
                "configured input root."
            )
        ),
    ],
    target_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "New .tif file beneath the "
                "configured output root."
            )
        ),
    ],
    target_crs: Annotated[
        str,
        typer.Option(
            "--target-crs",
            help="Required target CRS.",
        ),
    ],
    resampling: Annotated[
        str,
        typer.Option(
            "--resampling",
            help=(
                "Allowlisted method: nearest, "
                "bilinear, or cubic."
            ),
        ),
    ] = "nearest",
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Convert one raster pending validation."""

    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.data.spatial.skills.convert_raster.schemas import ConvertRasterArguments
    from geoagent_harness.data.spatial.skills.convert_raster.service import ConvertRasterError
    from geoagent_harness.task_actions.command_actions import skills_convert_raster_service__convert_raster as convert_raster

    try:
        result = convert_raster(
            ConvertRasterArguments(
                path=path,
                target_path=target_path,
                target_crs=target_crs,
                resampling=resampling,
            ),
            settings=load_settings(),
        )
    except (
        ConvertRasterError,
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


def validate_raster_conversion_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Original raster dataset.",
        ),
    ],
    target_path: Annotated[
        Path,
        typer.Argument(
            help="Converted raster dataset.",
        ),
    ],
    target_crs: Annotated[
        str,
        typer.Option(
            "--target-crs",
            help="Expected target CRS.",
        ),
    ],
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
    """Independently validate raster conversion."""

    from geoagent_harness.platform.settings import MCPSettings
    from geoagent_harness.data.spatial.skills.convert_raster.schemas import ConvertRasterArguments
    from geoagent_harness.data.spatial.skills.convert_raster.validation import ConvertRasterValidationError
    from geoagent_harness.task_actions.command_actions import skills_convert_raster_validation__validate_raster_conversion as validate_raster_conversion

    try:
        result = validate_raster_conversion(
            ConvertRasterArguments(
                path=path,
                target_path=target_path,
                target_crs=target_crs,
            ),
            settings=MCPSettings(
                input_root=input_root,
                output_root=output_root,
            ),
        )
    except (
        ConvertRasterValidationError,
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

    if not result.passed:
        raise typer.Exit(code=1)
