"""Typer command-line interface."""

import json
from pathlib import Path
from typing import Annotated, NoReturn

from datetime import datetime

import typer

from geoagent_harness.agent_manifest import load_agent_manifest

from geoagent_harness.failures import (
    FailureStage,
    failure_from_exception,
)
from geoagent_harness.recipe_proposals import (
    RecipeCompilationError,
    RecipeProposalAgentError,
    render_recipe_operator_review,
    review_recipe_request,
)


app = typer.Typer(
    name="geoagent",
    help="Run allowlisted ActionCharter operations.",
    no_args_is_help=True,
)

def _raise_typed_failure(
    exception: BaseException,
    *,
    stage: FailureStage,
) -> NoReturn:
    """Render one redacted typed failure and exit."""

    failure = failure_from_exception(
        exception,
        stage=stage,
    )

    typer.echo(
        (
            f"Error [{failure.code}]: "
            f"{failure.message}"
        ),
        err=True,
    )

    raise typer.Exit(
        code=failure.exit_code
    ) from exception

@app.command("agent-info")
def agent_info_command(
    role: Annotated[
        str, typer.Argument(help="Logical role: planner, executor, critic, or builder.")
    ],
    agents_root: Annotated[
        Path, typer.Option("--agents-root", help="Trusted agent manifest root.")
    ] = Path("/app/agents"),
) -> None:
    """Validate and display a redacted static agent manifest.

    Checkpoint 1 intentionally exits after validation; it does not call Ollama
    or start an agent loop.
    """
    try:
        manifest = load_agent_manifest(role, agents_root)
    except (OSError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            {
                "id": manifest.id,
                "model_ref": manifest.model_ref,
                "purpose": manifest.purpose,
                "allowed_tools": manifest.permissions.tools,
                "checkpoint_status": "manifest-valid; role-runtime-implemented",
            },
            separators=(",", ":"),
        )
    )


@app.command("inspect-vector")
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
    from geoagent_harness.skills.inspect_vector.service import (
        InspectVectorError,
        inspect_vector,
    )
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


@app.command("assess-spatial-data-contract")
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

    from geoagent_harness.spatial_contracts import (
        SpatialDataContractAssessmentError,
        SpatialDataContractStorageError,
        assess_spatial_data_contract,
        load_spatial_data_contract,
    )

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


@app.command("assess-pilot-demo-readiness")
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

    from geoagent_harness.pilot_demo import (
        PilotDemoError,
        assess_pilot_demo_readiness,
    )
    from geoagent_harness.spatial_contracts import (
        SpatialDataContractAssessmentError,
        SpatialDataContractStorageError,
    )

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


@app.command("plan-convert-vector")
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

    from geoagent_harness.skills.convert_vector import (
        ConvertVectorPolicyError,
        plan_vector_conversion,
    )

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

@app.command("convert-vector")
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

    from geoagent_harness.mcp_server.settings import (
        load_settings,
    )
    from geoagent_harness.skills.convert_vector import (
        ConvertVectorError,
        convert_vector,
    )

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

@app.command("inspect-builder-candidate")
def inspect_builder_candidate_command(
    candidate_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Materialized Builder candidate directory "
                "to inspect."
            ),
        ),
    ],
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help=(
                "Approved root containing isolated "
                "Builder candidates."
            ),
        ),
    ] = Path("builder-candidates"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Statically inspect one untrusted Builder candidate."""

    from geoagent_harness.builder import (
        BuilderCandidateInspectionError,
        inspect_builder_candidate,
    )

    try:
        result = inspect_builder_candidate(
            candidate_path=candidate_path,
            candidate_root=candidate_root,
        )
    except BuilderCandidateInspectionError as exc:
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

@app.command("assess-builder-candidate-tests")
def assess_builder_candidate_tests_command(
    candidate_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Materialized Builder candidate "
                "directory."
            ),
        ),
    ],
    test_record_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Isolated Builder candidate-test "
                "JSON record."
            ),
        ),
    ],
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help="Approved Builder candidate root.",
        ),
    ] = Path("builder-candidates"),
    evidence_root: Annotated[
        Path,
        typer.Option(
            "--evidence-root",
            help="Approved Builder test-evidence root.",
        ),
    ] = Path("builder-test-results"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Assess digest-bound isolated Builder tests."""

    from geoagent_harness.builder import (
        BuilderCandidateTestingError,
        assess_builder_candidate_tests,
    )

    try:
        result = assess_builder_candidate_tests(
            candidate_path=candidate_path,
            candidate_root=candidate_root,
            test_record_path=test_record_file,
            evidence_root=evidence_root,
        )
    except (
        BuilderCandidateTestingError,
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

@app.command("validate-vector-conversion")
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

    from geoagent_harness.skills.convert_vector import (
        ConvertVectorValidationError,
        validate_vector_conversion,
    )

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

@app.command("load-vector-to-postgis")
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
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.skills.load_vector_to_postgis.service import (
        LoadVectorError,
        load_vector_to_postgis,
    )

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

@app.command("validate-postgis-layer")
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
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.verifier.postgis import (
        PostGISVerificationError,
        validate_postgis_layer,
    )

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


@app.command("inspect-postgis-table")
def inspect_postgis_table_command(
    target_schema: Annotated[
        str,
        typer.Option("--schema", help="Approved PostGIS schema."),
    ] = "agent_sandbox",
    target_table: Annotated[
        str,
        typer.Option("--table", help="Exact PostGIS table to inspect."),
    ] = "sample_points",
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Inspect bounded metadata for one approved PostGIS table."""
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.postgis_inspection import (
        PostGISInspectionError,
        PostGISInspectionRequest,
        inspect_postgis_table,
    )

    try:
        result = inspect_postgis_table(
            request=PostGISInspectionRequest(
                target_schema=target_schema,
                target_table=target_table,
            ),
            settings=load_settings(),
        )
    except (PostGISInspectionError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ))

    if not result.table_exists:
        raise typer.Exit(code=1)


@app.command("compare-postgis-tables")
def compare_postgis_tables_command(
    reference_schema: Annotated[
        str,
        typer.Option(
            "--reference-schema",
            help="Approved reference PostGIS schema.",
        ),
    ] = "agent_sandbox",
    reference_table: Annotated[
        str,
        typer.Option(
            "--reference-table",
            help="Exact reference table.",
        ),
    ] = "reference_layer",
    candidate_schema: Annotated[
        str,
        typer.Option(
            "--candidate-schema",
            help="Approved candidate PostGIS schema.",
        ),
    ] = "agent_sandbox",
    candidate_table: Annotated[
        str,
        typer.Option(
            "--candidate-table",
            help="Exact candidate table.",
        ),
    ] = "candidate_layer",
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Compare two approved PostGIS tables without modification."""
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.postgis_comparison import (
        PostGISComparisonError,
        PostGISComparisonRequest,
        compare_postgis_tables,
    )
    from geoagent_harness.postgis_inspection import (
        PostGISInspectionError,
        PostGISInspectionRequest,
    )

    try:
        result = compare_postgis_tables(
            request=PostGISComparisonRequest(
                reference=PostGISInspectionRequest(
                    target_schema=reference_schema,
                    target_table=reference_table,
                ),
                candidate=PostGISInspectionRequest(
                    target_schema=candidate_schema,
                    target_table=candidate_table,
                ),
            ),
            settings=load_settings(),
        )
    except (
        PostGISComparisonError,
        PostGISInspectionError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ))

    if not result.matches:
        raise typer.Exit(code=1)

@app.command("run-vector-postgis-workflow")
def run_vector_postgis_workflow_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Vector dataset beneath the approved input root."
        ),
    ],
    target_table: Annotated[
        str,
        typer.Option(
            "--table",
            help="New PostGIS target table.",
        ),
    ],
    target_schema: Annotated[
        str,
        typer.Option(
            "--schema",
            help="Approved PostGIS schema.",
        ),
    ] = "agent_sandbox",
    source_layer: Annotated[
        str | None,
        typer.Option(
            "--layer",
            help="Required for multi-layer datasets.",
        ),
    ] = None,
    original_request: Annotated[
        str,
        typer.Option(
            "--request",
            help="Original task request stored in redacted form.",
        ),
    ] = "Load and validate an approved vector dataset.",
    task_id: Annotated[
        str | None,
        typer.Option(
            "--task-id",
            help="Optional lowercase reproducible task ID.",
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Run the complete validated vector-to-PostGIS workflow."""
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.orchestrator.workflow import (
        WorkflowError,
        run_vector_postgis_workflow,
    )

    try:
        result = run_vector_postgis_workflow(
            path=path,
            source_layer=source_layer,
            target_schema=target_schema,
            target_table=target_table,
            original_request=original_request,
            task_id=task_id,
            settings=load_settings(),
        )
    except (WorkflowError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

    if result.final_status != "validated_success":
        raise typer.Exit(code=1)


@app.command("plan-task")
def plan_task_command(
    original_request: Annotated[
        str,
        typer.Option(
            "--request",
            help="Task request to plan without executing.",
        ),
    ],
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help="Root containing trusted context files.",
        ),
    ] = Path("."),
    agents_root: Annotated[
        Path,
        typer.Option(
            "--agents-root",
            help="Root containing trusted agent manifests.",
        ),
    ] = Path("agents"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Create and validate a plan without executing it."""

    from geoagent_harness.context_pack import (
        ContextPackError,
    )
    from geoagent_harness.model import (
        ModelClientError,
        ModelSettingsError,
    )
    from geoagent_harness.planner import (
        PlannerAgentError,
        plan_task,
    )

    try:
        result = plan_task(
            original_request=original_request,
            project_root=project_root,
            agents_root=agents_root,
        )
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.PLANNING,
        )
    except ModelClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MODEL,
        )
    except (
        ContextPackError,
        ModelSettingsError,
        PlannerAgentError,
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

@app.command("plan-digest")
def plan_digest_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Planner result JSON beneath the plan root.",
        ),
    ],
    plan_root: Annotated[
        Path,
        typer.Option(
            "--plan-root",
            help="Approved root containing saved plans.",
        ),
    ] = Path("plans"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Calculate the canonical digest of a validated plan."""

    from geoagent_harness.approvals import (
        ApprovalError,
        load_planner_result,
        plan_sha256,
    )

    try:
        planner_result = load_planner_result(
            path=plan_file,
            plan_root=plan_root,
        )

        payload = {
            "status": "ok",
            "plan_sha256": plan_sha256(
                planner_result.plan
            ),
            "plan_file": plan_file.as_posix(),
        }
    except ApprovalError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            payload,
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

@app.command("approve-plan")
def approve_plan_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Planner result JSON beneath the plan root.",
        ),
    ],
    step_ids: Annotated[
        list[str],
        typer.Option(
            "--step",
            help=(
                "Plan step to approve or deny; "
                "repeat for multiple steps."
            ),
        ),
    ],
    approver: Annotated[
        str,
        typer.Option(
            "--approver",
            help="Human or local operator recording the decision.",
        ),
    ],
    reason: Annotated[
        str,
        typer.Option(
            "--reason",
            help="Reason for the approval decision.",
        ),
    ],
    decision: Annotated[
        str,
        typer.Option(
            "--decision",
            help="Either approved or denied.",
        ),
    ] = "approved",
    plan_root: Annotated[
        Path,
        typer.Option("--plan-root"),
    ] = Path("plans"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    valid_for_minutes: Annotated[
        int | None,
        typer.Option(
            "--valid-for-minutes",
            help=(
                "Optional approval lifetime. "
                "Omit for no expiration."
            ),
        ),
    ] = None,
    corrections: Annotated[
        list[str] | None,
        typer.Option(
            "--correction",
            help=(
                "Human correction; repeat for multiple "
                "corrections."
            ),
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Record an append-only decision for an exact plan."""

    from datetime import (
        datetime,
        timedelta,
        timezone,
    )

    from geoagent_harness.approvals import (
        ApprovalError,
        create_approval,
        load_planner_result,
    )

    if decision not in {"approved", "denied"}:
        typer.echo(
            "Error: decision must be approved or denied",
            err=True,
        )
        raise typer.Exit(code=2)

    if (
        valid_for_minutes is not None
        and valid_for_minutes <= 0
    ):
        typer.echo(
            "Error: valid-for-minutes must be positive",
            err=True,
        )
        raise typer.Exit(code=2)

    active_now = datetime.now(timezone.utc)

    expires_at = (
        active_now
        + timedelta(minutes=valid_for_minutes)
        if valid_for_minutes is not None
        else None
    )

    try:
        planner_result = load_planner_result(
            path=plan_file,
            plan_root=plan_root,
        )

        record, path = create_approval(
            planner_result=planner_result,
            step_ids=step_ids,
            decision=decision,
            approver=approver,
            reason=reason,
            approval_root=approval_root,
            project_root=project_root,
            human_corrections=corrections,
            expires_at=expires_at,
            now=active_now,
        )
    except (ApprovalError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            {
                "status": "recorded",
                "approval_path": path.as_posix(),
                "approval": record.model_dump(
                    mode="json"
                ),
            },
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )
    
@app.command("verify-plan-approval")
def verify_plan_approval_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Planner result JSON beneath the plan root.",
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Approval JSON beneath the approval root.",
        ),
    ],
    plan_root: Annotated[
        Path,
        typer.Option("--plan-root"),
    ] = Path("plans"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Verify approval for every approval-required plan step."""

    from geoagent_harness.approvals import (
        ApprovalError,
        load_approval,
        load_planner_result,
        verify_approval,
    )

    try:
        planner_result = load_planner_result(
            path=plan_file,
            plan_root=plan_root,
        )

        approval = load_approval(
            path=approval_file,
            approval_root=approval_root,
        )

        required_steps = [
            step.step_id
            for step in planner_result.plan.steps
            if step.requires_approval
        ]

        verification = verify_approval(
            approval=approval,
            plan=planner_result.plan,
            required_step_ids=required_steps,
        )
    except ApprovalError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            verification.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if not verification.approved:
        raise typer.Exit(code=1)

@app.command("build-execution-envelope")
def build_execution_envelope_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Planner result JSON beneath the plan root.",
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Approval JSON beneath the approval root.",
        ),
    ],
    plan_root: Annotated[
        Path,
        typer.Option("--plan-root"),
    ] = Path("plans"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    allowed_schemas: Annotated[
        str,
        typer.Option(
            "--allowed-schemas",
            help="Comma-separated approved PostGIS schemas.",
        ),
    ] = "agent_sandbox",
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Build an approved envelope without executing it."""

    from geoagent_harness.approvals import (
        ApprovalError,
        load_approval,
        load_planner_result,
    )
    from geoagent_harness.executor import (
        ExecutorPolicyError,
        build_execution_envelope,
    )

    schemas = {
        value.strip()
        for value in allowed_schemas.split(",")
        if value.strip()
    }

    if not schemas:
        typer.echo(
            "Error: at least one allowed schema is required",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        planner_result = load_planner_result(
            path=plan_file,
            plan_root=plan_root,
        )

        approval = load_approval(
            path=approval_file,
            approval_root=approval_root,
        )

        envelope = build_execution_envelope(
            planner_result=planner_result,
            approval=approval,
            allowed_schemas=schemas,
        )
    except (
        ApprovalError,
        ExecutorPolicyError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            envelope.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

@app.command("mcp-http-smoke")
def mcp_http_smoke_command(
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Test internal MCP using only health_check."""

    import asyncio

    from geoagent_harness.mcp_client import (
        MCPClientError,
        MCPClientSettingsError,
        MCPReadOnlyClient,
        load_mcp_client_settings,
    )

    async def run_smoke() -> dict:
        client = MCPReadOnlyClient(
            load_mcp_client_settings()
        )

        available_tools = await client.list_tools()

        health = await client.call_tool(
            "health_check"
        )

        return {
            "status": "ok",
            "transport": "streamable-http",
            "available_tools": available_tools,
            "called_tool": health.tool_name,
            "health": health.result,
        }

    try:
        payload = asyncio.run(run_smoke())
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MCP,
        )
    except MCPClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MCP,
        )
    except MCPClientSettingsError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            payload,
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )
    
@app.command("execute-approved-plan")
def execute_approved_plan_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Planner result JSON beneath the plan root.",
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Approval JSON beneath the approval root.",
        ),
    ],
    plan_root: Annotated[
        Path,
        typer.Option("--plan-root"),
    ] = Path("plans"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    allowed_schemas: Annotated[
        str,
        typer.Option("--allowed-schemas"),
    ] = "agent_sandbox",
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Execute one exact approved plan through MCP."""

    import asyncio

    from geoagent_harness.approvals import (
        ApprovalError,
    )
    from geoagent_harness.executor import (
        ExecutorPolicyError,
    )
    from geoagent_harness.executor.service import (
        ExecutorServiceError,
        execute_approved_plan,
    )
    from geoagent_harness.mcp_client import (
        MCPClientError,
        MCPClientSettingsError,
    )

    schemas = {
        value.strip()
        for value in allowed_schemas.split(",")
        if value.strip()
    }

    if not schemas:
        typer.echo(
            "Error: at least one allowed schema is required",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        result = asyncio.run(
            execute_approved_plan(
                plan_file=plan_file,
                approval_file=approval_file,
                plan_root=plan_root,
                approval_root=approval_root,
                agents_root=agents_root,
                allowed_schemas=schemas,
            )
        )
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.EXECUTION,
        )
    except MCPClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MCP,
        )
    except (
        ApprovalError,
        ExecutorPolicyError,
        ExecutorServiceError,
        MCPClientSettingsError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
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

    if (
        result.workflow.final_status
        != "validated_success"
    ):
        raise typer.Exit(code=1)

@app.command("inspect-workflow-state")
def inspect_workflow_state_command(
    state_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "State JSON file beneath the trusted "
                "workflow-state root."
            ),
        ),
    ],
    state_root: Annotated[
        Path | None,
        typer.Option(
            "--state-root",
            help=(
                "Trusted workflow-state directory. "
                "Defaults to GEOAGENT_STATE_ROOT."
            ),
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Load and display validated workflow state."""

    from geoagent_harness.mcp_server.settings import (
        load_settings,
    )
    from geoagent_harness.workflow_state import (
        WorkflowStateError,
        load_state,
    )

    active_root = (
        state_root
        if state_root is not None
        else load_settings().state_root
    )

    try:
        state = load_state(
            state_file,
            state_root=active_root,
        )
    except (
        WorkflowStateError,
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
            state.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


@app.command("assess-workflow-resume")
def assess_workflow_resume_command(
    state_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "State JSON file beneath the trusted "
                "workflow-state root."
            ),
        ),
    ],
    state_root: Annotated[
        Path | None,
        typer.Option(
            "--state-root",
            help=(
                "Trusted workflow-state directory. "
                "Defaults to GEOAGENT_STATE_ROOT."
            ),
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess safe continuation without modifying state."""

    from geoagent_harness.mcp_server.settings import (
        load_settings,
    )
    from geoagent_harness.workflow_state import (
        WorkflowStateError,
        assess_resume,
        load_state,
    )

    active_root = (
        state_root
        if state_root is not None
        else load_settings().state_root
    )

    try:
        state = load_state(
            state_file,
            state_root=active_root,
        )

        assessment = assess_resume(state)
    except (
        WorkflowStateError,
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
            assessment.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

@app.command("build-critic-evidence")
def build_critic_evidence_command(
    trace_path: Annotated[
        Path,
        typer.Argument(
            help="JSON trace beneath the approved trace root.",
        ),
    ],
    report_path: Annotated[
        Path,
        typer.Argument(
            help="Markdown report beneath the approved report root.",
        ),
    ],
    trace_root: Annotated[
        Path,
        typer.Option(
            "--trace-root",
            help="Trusted trace directory.",
        ),
    ] = Path("traces"),
    report_root: Annotated[
        Path,
        typer.Option(
            "--report-root",
            help="Trusted report directory.",
        ),
    ] = Path("reports"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Build redacted deterministic evidence for the Critic Agent."""

    from geoagent_harness.critic.evidence import (
        CriticEvidenceError,
        build_critic_evidence,
    )

    try:
        evidence = build_critic_evidence(
            trace_path=trace_path,
            report_path=report_path,
            trace_root=trace_root,
            report_root=report_root,
        )
    except CriticEvidenceError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            evidence.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

@app.command("critique-task")
def critique_task_command(
    trace_path: Annotated[
        Path,
        typer.Argument(
            help="JSON trace beneath the approved trace root.",
        ),
    ],
    report_path: Annotated[
        Path,
        typer.Argument(
            help="Markdown report beneath the approved report root.",
        ),
    ],
    trace_root: Annotated[
        Path,
        typer.Option("--trace-root"),
    ] = Path("traces"),
    report_root: Annotated[
        Path,
        typer.Option("--report-root"),
    ] = Path("reports"),
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Critique deterministic workflow evidence using Ollama."""

    from geoagent_harness.critic import (
        CriticAgentError,
        CriticEvidenceError,
        critique_task,
    )
    from geoagent_harness.model import (
        ModelClientError,
        ModelSettingsError,
    )

    try:
        result = critique_task(
            trace_path=trace_path,
            report_path=report_path,
            trace_root=trace_root,
            report_root=report_root,
            agents_root=agents_root,
        )
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.CRITIQUE,
        )
    except ModelClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MODEL,
        )
    except (
        CriticAgentError,
        CriticEvidenceError,
        ModelSettingsError,
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

    if result.deterministic_status != "validated_success":
        raise typer.Exit(code=1)


@app.command("record-critic-result")
def record_critic_result_command(
    trace_path: Annotated[
        Path,
        typer.Argument(
            help="JSON trace beneath the approved trace root.",
        ),
    ],
    report_path: Annotated[
        Path,
        typer.Argument(
            help="Markdown report beneath the approved report root.",
        ),
    ],
    trace_root: Annotated[
        Path,
        typer.Option("--trace-root"),
    ] = Path("traces"),
    report_root: Annotated[
        Path,
        typer.Option("--report-root"),
    ] = Path("reports"),
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    record_root: Annotated[
        Path,
        typer.Option(
            "--record-root",
            help="Immutable Critic-result package root.",
        ),
    ] = Path("critic-results"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Critique verified evidence and persist a separate result."""

    from datetime import timezone

    from geoagent_harness.critic import (
        CriticAgentError,
        CriticEvidenceError,
        CriticResultRecordError,
        CriticResultStorageError,
        build_critic_result_record,
        critique_task,
        persist_critic_result_record,
    )
    from geoagent_harness.model import (
        ModelClientError,
        ModelSettingsError,
    )

    try:
        result = critique_task(
            trace_path=trace_path,
            report_path=report_path,
            trace_root=trace_root,
            report_root=report_root,
            agents_root=agents_root,
        )
        record = build_critic_result_record(
            result=result,
            recorded_at=datetime.now(timezone.utc),
        )
        stored = persist_critic_result_record(
            record,
            record_root=record_root,
        )
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.CRITIQUE,
        )
    except ModelClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MODEL,
        )
    except (
        CriticAgentError,
        CriticEvidenceError,
        CriticResultRecordError,
        CriticResultStorageError,
        ModelSettingsError,
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
            stored.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None if pretty else (",", ":")
            ),
        )
    )


@app.command("assess-workflow-release")
def assess_workflow_release_command(
    release_id: Annotated[
        str,
        typer.Argument(help="Stable release-candidate ID."),
    ],
    trace_file: Annotated[
        Path,
        typer.Argument(help="Workflow trace beneath its approved root."),
    ],
    report_file: Annotated[
        Path,
        typer.Argument(help="Workflow report beneath its approved root."),
    ],
    critic_record_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable CRITIC_RESULT.json beneath its root."
        ),
    ],
    history_file: Annotated[
        Path,
        typer.Argument(help="Operational JSONL beneath its approved root."),
    ],
    trace_root: Annotated[
        Path,
        typer.Option("--trace-root"),
    ] = Path("traces"),
    report_root: Annotated[
        Path,
        typer.Option("--report-root"),
    ] = Path("reports"),
    critic_root: Annotated[
        Path,
        typer.Option("--critic-root"),
    ] = Path("critic-results"),
    history_root: Annotated[
        Path,
        typer.Option("--history-root"),
    ] = Path("operational-history"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    plan_file: Annotated[
        Path | None,
        typer.Option("--plan-file"),
    ] = None,
    plan_root: Annotated[
        Path,
        typer.Option("--plan-root"),
    ] = Path("plans"),
    approval_file: Annotated[
        Path | None,
        typer.Option("--approval-file"),
    ] = None,
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess exact workflow evidence without creating a release."""

    from datetime import timezone

    from geoagent_harness.releases import (
        ReleaseAssessmentError,
        assess_workflow_release_candidate,
        authoritative_release_candidate_sha256,
    )

    try:
        candidate = assess_workflow_release_candidate(
            release_id=release_id,
            trace_file=trace_file,
            report_file=report_file,
            critic_record_file=critic_record_file,
            history_file=history_file,
            trace_root=trace_root,
            report_root=report_root,
            critic_root=critic_root,
            history_root=history_root,
            project_root=project_root,
            assessed_at=datetime.now(timezone.utc),
            plan_file=plan_file,
            plan_root=plan_root,
            approval_file=approval_file,
            approval_root=approval_root,
        )
        payload = {
            "candidate_sha256": (
                authoritative_release_candidate_sha256(candidate)
            ),
            "candidate": candidate.model_dump(mode="json"),
        }
    except (
        ReleaseAssessmentError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            payload,
            indent=2 if pretty else None,
            separators=(None if pretty else (",", ":")),
        )
    )


@app.command("create-workflow-release")
def create_workflow_release_command(
    release_id: Annotated[
        str,
        typer.Argument(help="Stable authoritative release ID."),
    ],
    trace_file: Annotated[Path, typer.Argument()],
    report_file: Annotated[Path, typer.Argument()],
    critic_record_file: Annotated[Path, typer.Argument()],
    history_file: Annotated[Path, typer.Argument()],
    trace_root: Annotated[
        Path, typer.Option("--trace-root")
    ] = Path("traces"),
    report_root: Annotated[
        Path, typer.Option("--report-root")
    ] = Path("reports"),
    critic_root: Annotated[
        Path, typer.Option("--critic-root")
    ] = Path("critic-results"),
    history_root: Annotated[
        Path, typer.Option("--history-root")
    ] = Path("operational-history"),
    project_root: Annotated[
        Path, typer.Option("--project-root")
    ] = Path("."),
    plan_file: Annotated[
        Path | None, typer.Option("--plan-file")
    ] = None,
    plan_root: Annotated[
        Path, typer.Option("--plan-root")
    ] = Path("plans"),
    approval_file: Annotated[
        Path | None, typer.Option("--approval-file")
    ] = None,
    approval_root: Annotated[
        Path, typer.Option("--approval-root")
    ] = Path("approvals"),
    release_root: Annotated[
        Path, typer.Option("--release-root")
    ] = Path("releases"),
    pretty: Annotated[
        bool, typer.Option("--pretty")
    ] = False,
) -> None:
    """Create one immutable release from reverified workflow evidence."""

    from datetime import timezone

    from geoagent_harness.releases import (
        AuthoritativeReleaseStorageError,
        ReleaseAssessmentError,
        assess_workflow_release_candidate,
        persist_authoritative_release,
    )

    now = datetime.now(timezone.utc)
    try:
        candidate = assess_workflow_release_candidate(
            release_id=release_id,
            trace_file=trace_file,
            report_file=report_file,
            critic_record_file=critic_record_file,
            history_file=history_file,
            trace_root=trace_root,
            report_root=report_root,
            critic_root=critic_root,
            history_root=history_root,
            project_root=project_root,
            assessed_at=now,
            plan_file=plan_file,
            plan_root=plan_root,
            approval_file=approval_file,
            approval_root=approval_root,
        )
        result = persist_authoritative_release(
            candidate,
            project_root=project_root,
            release_root=release_root,
            released_at=now,
        )
    except (
        ReleaseAssessmentError,
        AuthoritativeReleaseStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(None if pretty else (",", ":")),
        )
    )


@app.command("inspect-authoritative-release")
def inspect_authoritative_release_command(
    manifest_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable RELEASE.json beneath its approved root."
        ),
    ],
    release_root: Annotated[
        Path,
        typer.Option(
            "--release-root",
            help="Approved immutable release-package root.",
        ),
    ] = Path("releases"),
    pretty: Annotated[
        bool, typer.Option("--pretty")
    ] = False,
) -> None:
    """Independently verify one immutable authoritative release."""

    from geoagent_harness.releases import (
        AuthoritativeReleaseStorageError,
        inspect_authoritative_release,
    )

    try:
        result = inspect_authoritative_release(
            manifest_file,
            release_root=release_root,
        )
    except (
        AuthoritativeReleaseStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(None if pretty else (",", ":")),
        )
    )


@app.command("recipe-template-catalog")
def recipe_template_catalog_command(
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help=(
                "Trusted project root containing "
                "context/RECIPE_TEMPLATES.yaml."
            ),
        ),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Validate and display the recipe-template catalog."""

    from geoagent_harness.recipe_catalog import (
        RecipeTemplateCatalogError,
        load_recipe_template_catalog,
    )

    try:
        catalog = load_recipe_template_catalog(
            project_root
        )
    except RecipeTemplateCatalogError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    payload = {
        "schema_version": (
            catalog.schema_version
        ),
        "templates": [
            template.model_dump(
                mode="json"
            )
            for template in catalog.templates
        ],
        "catalog_validated": True,
        "files_modified": False,
        "execution_performed": False,
    }

    typer.echo(
        json.dumps(
            payload,
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

@app.command("schema-policies")
def schema_policies_command(
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Display the read-only artifact schema registry."""

    from geoagent_harness.schema_registry import (
        list_schema_policies,
    )

    payload = {
        "schema_version": "1.0",
        "policies": [
            policy.model_dump(mode="json")
            for policy in list_schema_policies()
        ],
        "registry_modified": False,
    }

    typer.echo(
        json.dumps(
            payload,
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


@app.command("assess-schema-compatibility")
def assess_schema_compatibility_command(
    artifact_type: Annotated[
        str,
        typer.Argument(
            help=(
                "Registered artifact type, such as "
                "workflow_trace or workflow_state."
            ),
        ),
    ],
    artifact_version: Annotated[
        str,
        typer.Argument(
            help="Artifact schema version to assess.",
        ),
    ],
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess schema compatibility without mutation."""

    from geoagent_harness.schema_registry import (
        SchemaRegistryError,
        assess_schema_compatibility,
    )

    try:
        assessment = assess_schema_compatibility(
            artifact_type=artifact_type,
            artifact_version=artifact_version,
        )
    except SchemaRegistryError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            assessment.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if not assessment.readable:
        raise typer.Exit(code=1)


@app.command("assess-schema-migration")
def assess_schema_migration_command(
    artifact_type: Annotated[
        str,
        typer.Argument(
            help="Registered artifact type.",
        ),
    ],
    artifact_version: Annotated[
        str,
        typer.Argument(
            help="Source schema version to assess.",
        ),
    ],
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess migration needs without modifying artifacts."""

    from geoagent_harness.schema_registry import (
        SchemaRegistryError,
        assess_migration,
    )

    try:
        assessment = assess_migration(
            artifact_type=artifact_type,
            artifact_version=artifact_version,
        )
    except SchemaRegistryError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            assessment.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if assessment.manual_review_required:
        raise typer.Exit(code=1)

@app.command("save-recipe")
def save_recipe_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="JSON recipe draft to validate and store.",
        ),
    ],
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Validate and immutably persist a reusable recipe."""

    from geoagent_harness.recipes import (
        RecipePolicyError,
        RecipeStorageError,
        load_recipe_draft,
        recipe_sha256,
        save_recipe,
        validate_recipe_policy,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )

    try:
        draft = load_recipe_draft(
            recipe_file
        )
        registry = load_skill_registry(
            project_root
        )
        validation = validate_recipe_policy(
            draft,
            registry=registry,
        )
        stored, path = save_recipe(
            draft,
            recipe_root=recipe_root,
        )
    except (
        RecipePolicyError,
        RecipeStorageError,
        SkillRegistryError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    payload = {
        "status": "stored",
        "recipe_id": stored.recipe_id,
        "recipe_sha256": recipe_sha256(
            stored
        ),
        "recipe_path": path.as_posix(),
        "policy": validation.model_dump(
            mode="json"
        ),
    }

    typer.echo(
        json.dumps(
            payload,
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

@app.command("approve-recipe")
def approve_recipe_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="Canonical recipe beneath the recipe root.",
        ),
    ],
    step_ids: Annotated[
        list[str],
        typer.Option(
            "--step",
            help=(
                "Approval-required recipe step; "
                "repeat for multiple steps."
            ),
        ),
    ],
    approver: Annotated[
        str,
        typer.Option("--approver"),
    ],
    reason: Annotated[
        str,
        typer.Option("--reason"),
    ],
    decision: Annotated[
        str,
        typer.Option("--decision"),
    ] = "approved",
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    valid_for_minutes: Annotated[
        int | None,
        typer.Option("--valid-for-minutes"),
    ] = None,
    corrections: Annotated[
        list[str] | None,
        typer.Option("--correction"),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Approve explicit write steps in one exact recipe."""

    from datetime import (
        datetime,
        timedelta,
        timezone,
    )

    from geoagent_harness.recipes import (
        RecipeApprovalError,
        RecipeStorageError,
        create_recipe_approval,
        load_recipe,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )

    if decision not in {
        "approved",
        "denied",
    }:
        typer.echo(
            "Error: decision must be approved or denied",
            err=True,
        )
        raise typer.Exit(code=2)

    if (
        valid_for_minutes is not None
        and valid_for_minutes <= 0
    ):
        typer.echo(
            "Error: valid-for-minutes must be positive",
            err=True,
        )
        raise typer.Exit(code=2)

    active_now = datetime.now(
        timezone.utc
    )

    expires_at = (
        active_now
        + timedelta(
            minutes=valid_for_minutes
        )
        if valid_for_minutes is not None
        else None
    )

    try:
        recipe = load_recipe(
            recipe_file,
            recipe_root=recipe_root,
        )
        registry = load_skill_registry(
            project_root
        )
        record, path = create_recipe_approval(
            recipe=recipe,
            registry=registry,
            step_ids=step_ids,
            decision=decision,
            approver=approver,
            reason=reason,
            approval_root=approval_root,
            human_corrections=corrections,
            expires_at=expires_at,
            now=active_now,
        )
    except (
        RecipeApprovalError,
        RecipeStorageError,
        SkillRegistryError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    payload = {
        "status": "recorded",
        "approval_path": path.as_posix(),
        "approval": record.model_dump(
            mode="json"
        ),
    }

    typer.echo(
        json.dumps(
            payload,
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )
    
@app.command("verify-recipe-approval")
def verify_recipe_approval_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="Canonical recipe beneath the recipe root.",
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Recipe approval beneath the approval root.",
        ),
    ],
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Verify approval against an exact stored recipe."""

    from geoagent_harness.recipes import (
        RecipeApprovalError,
        RecipeStorageError,
        load_recipe,
        load_recipe_approval,
        verify_recipe_approval,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )

    try:
        recipe = load_recipe(
            recipe_file,
            recipe_root=recipe_root,
        )
        approval = load_recipe_approval(
            approval_file,
            approval_root=approval_root,
        )
        registry = load_skill_registry(
            project_root
        )
        result = verify_recipe_approval(
            approval=approval,
            recipe=recipe,
            registry=registry,
        )
    except (
        RecipeApprovalError,
        RecipeStorageError,
        SkillRegistryError,
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

    if not result.approved:
        raise typer.Exit(code=1)

@app.command("run-approved-recipe")
def run_approved_recipe_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="Canonical recipe beneath the recipe root.",
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Recipe approval beneath the approval root.",
        ),
    ],
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Run and validate one exact approved recipe."""

    from geoagent_harness.mcp_server.settings import (
        load_settings,
    )
    from geoagent_harness.recipes import (
        RecipeApprovalError,
        RecipeRunError,
        RecipeStorageError,
        load_recipe,
        load_recipe_approval,
        run_approved_recipe,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )

    try:
        recipe = load_recipe(
            recipe_file,
            recipe_root=recipe_root,
        )
        approval = load_recipe_approval(
            approval_file,
            approval_root=approval_root,
        )
        registry = load_skill_registry(
            project_root
        )

        result = run_approved_recipe(
            recipe=recipe,
            approval=approval,
            registry=registry,
            settings=load_settings(),
        )
    except (
        RecipeApprovalError,
        RecipeRunError,
        RecipeStorageError,
        SkillRegistryError,
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

    if (
        result.final_status
        != "validated_success"
    ):
        raise typer.Exit(code=1)

@app.command("execute-approved-recipe")
def execute_approved_recipe_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical recipe JSON beneath "
                "the recipe root."
            ),
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Recipe approval JSON beneath "
                "the approval root."
            ),
        ),
    ],
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Execute one exact approved recipe through MCP."""

    import asyncio

    from geoagent_harness.executor.service import (
        ExecutorServiceError,
        execute_approved_recipe_via_mcp,
    )
    from geoagent_harness.mcp_client import (
        MCPClientError,
        MCPClientSettingsError,
    )
    from geoagent_harness.recipes import (
        RecipeApprovalError,
        RecipeExecutionPolicyError,
        RecipeStorageError,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
    )

    try:
        result = asyncio.run(
            execute_approved_recipe_via_mcp(
                recipe_file=recipe_file,
                approval_file=approval_file,
                recipe_root=recipe_root,
                approval_root=approval_root,
                project_root=project_root,
                agents_root=agents_root,
            )
        )
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.EXECUTION,
        )
    except MCPClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MCP,
        )
    except (
        ExecutorServiceError,
        MCPClientSettingsError,
        RecipeApprovalError,
        RecipeExecutionPolicyError,
        RecipeStorageError,
        SkillRegistryError,
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

    if (
        result.recipe.final_status
        != "validated_success"
    ):
        raise typer.Exit(code=1)


@app.command("build-recipe-evidence")
def build_recipe_evidence_command(
    result_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Raw RecipeRunResult JSON beneath "
                "the trusted result root."
            ),
        ),
    ],
    result_root: Annotated[
        Path,
        typer.Option("--result-root"),
    ] = Path("recipe-runs"),
    evidence_root: Annotated[
        Path,
        typer.Option("--evidence-root"),
    ] = Path("recipe-evidence"),
    input_root: Annotated[
        Path,
        typer.Option("--input-root"),
    ] = Path("data/input"),
    output_root: Annotated[
        Path,
        typer.Option("--output-root"),
    ] = Path("data/output"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Build and immutably store recipe lineage evidence."""

    from geoagent_harness.recipes import (
        RecipeEvidenceError,
        RecipeEvidenceStorageError,
        build_recipe_run_evidence,
        load_recipe_run_result,
        recipe_evidence_sha256,
        write_recipe_evidence,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )

    try:
        run_result = load_recipe_run_result(
            result_file,
            result_root=result_root,
        )

        registry = load_skill_registry(
            project_root
        )

        evidence = build_recipe_run_evidence(
            run_result=run_result,
            registry=registry,
            input_root=input_root,
            output_root=output_root,
        )

        written_path = write_recipe_evidence(
            evidence,
            evidence_root=evidence_root,
        )

        response = {
            "status": "stored",
            "recipe_id": evidence.recipe_id,
            "recipe_sha256": (
                evidence.recipe_sha256
            ),
            "evidence_sha256": (
                recipe_evidence_sha256(
                    evidence
                )
            ),
            "evidence_path": (
                written_path.as_posix()
            ),
            "final_status": (
                evidence.final_status
            ),
            "artifact_count": len(
                evidence.artifacts
            ),
            "lineage_edge_count": len(
                evidence.lineage
            ),
            "secrets_redacted": True,
        }

    except (
        RecipeEvidenceError,
        RecipeEvidenceStorageError,
        SkillRegistryError,
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
            response,
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

@app.command("compile-recipe-proposal")
def compile_recipe_proposal_command(
    proposal_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Recipe proposal JSON beneath the "
                "approved proposal root."
            ),
        ),
    ],
    proposal_root: Annotated[
        Path,
        typer.Option("--proposal-root"),
    ] = Path("recipe-proposals"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Compile a safe proposal without saving or executing."""

    from geoagent_harness.recipe_proposals import (
        RecipeCompilationError,
        RecipeProposalStorageError,
        compile_recipe_proposal,
        load_recipe_proposal,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )

    try:
        proposal = load_recipe_proposal(
            proposal_file,
            proposal_root=proposal_root,
        )

        registry = load_skill_registry(
            project_root
        )

        result = compile_recipe_proposal(
            proposal,
            registry=registry,
        )
    except (
        RecipeCompilationError,
        RecipeProposalStorageError,
        SkillRegistryError,
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
    
@app.command("propose-recipe")
def propose_recipe_command(
    original_request: Annotated[
        str,
        typer.Argument(
            help=(
                "Natural-language GIS request. "
                "Quote requests containing spaces."
            ),
        ),
    ],
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Generate a non-executable recipe proposal."""

    from geoagent_harness.model import (
        ModelClientError,
        ModelSettingsError,
    )
    from geoagent_harness.recipe_proposals import (
        RecipeProposalAgentError,
        propose_recipe_with_shared_model,
    )

    try:
        result = (
            propose_recipe_with_shared_model(
                original_request=(
                    original_request
                ),
                agents_root=agents_root,
            )
        )
    except (
        ModelClientError,
        ModelSettingsError,
        RecipeProposalAgentError,
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
    
@app.command("propose-and-compile-recipe")
def propose_and_compile_recipe_command(
    original_request: Annotated[
        str,
        typer.Argument(
            help=(
                "Natural-language GIS request. "
                "Quote requests containing spaces."
            ),
        ),
    ],
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Generate and compile without saving or executing."""

    from geoagent_harness.model import (
        ModelClientError,
        ModelSettingsError,
    )
    from geoagent_harness.recipe_proposals import (
        RecipeCompilationError,
        RecipeProposalAgentError,
        propose_and_compile_recipe,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
    )

    try:
        result = propose_and_compile_recipe(
            original_request=original_request,
            project_root=project_root,
            agents_root=agents_root,
        )
    except (
        ModelClientError,
        ModelSettingsError,
        RecipeCompilationError,
        RecipeProposalAgentError,
        SkillRegistryError,
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

@app.command("review-recipe-request")
def review_recipe_request_command(
    original_request: Annotated[
        str,
        typer.Argument(
            help=(
                "Natural-language GIS request to "
                "prepare for operator review."
            ),
        ),
    ],
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            help="Output format: json or summary.",
        ),
    ] = "json",
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Prepare a recipe review without saving or executing."""

    from geoagent_harness.model import (
        ModelClientError,
        ModelSettingsError,
    )
    from geoagent_harness.recipe_proposals import (
        RecipeCompilationError,
        RecipeProposalAgentError,
        review_recipe_request,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
    )

    try:
        result = review_recipe_request(
            original_request=original_request,
            project_root=project_root,
            agents_root=agents_root,
        )
    except (
        ModelClientError,
        ModelSettingsError,
        RecipeCompilationError,
        RecipeProposalAgentError,
        SkillRegistryError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    if output_format not in {
        "json",
        "summary",
    }:
        typer.echo(
            "Error: output format must be "
            "'json' or 'summary'",
            err=True,
        )
        raise typer.Exit(code=2)

    if output_format == "summary":
        typer.echo(
            render_recipe_operator_review(
                result
            )
        )
        return

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

@app.command("save-reviewed-recipe")
def save_reviewed_recipe_command(
    review_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Ready operator-review JSON beneath "
                "the approved review root."
            ),
        ),
    ],
    review_root: Annotated[
        Path,
        typer.Option("--review-root"),
    ] = Path("recipe-reviews"),
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Explicitly save one exact reviewed recipe."""

    from geoagent_harness.recipe_proposals import (
        RecipeOperatorSaveError,
        RecipeReviewStorageError,
        load_recipe_operator_review,
        save_reviewed_recipe,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )

    try:
        review = load_recipe_operator_review(
            review_file,
            review_root=review_root,
        )

        registry = load_skill_registry(
            project_root
        )

        result = save_reviewed_recipe(
            review=review,
            registry=registry,
            recipe_root=recipe_root,
        )
    except (
        RecipeOperatorSaveError,
        RecipeReviewStorageError,
        SkillRegistryError,
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

@app.command("plan-skill-scaffold")
def plan_skill_scaffold_command(
    request_file: Annotated[
        Path,
        typer.Argument(
            help="Versioned skill scaffold request JSON."
        ),
    ],
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Plan a new GIS skill scaffold without writing files."""

    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )
    from geoagent_harness.skill_scaffolding import (
        SkillScaffoldPolicyError,
        SkillScaffoldStorageError,
        load_skill_scaffold_request,
        plan_skill_scaffold,
    )

    try:
        request = load_skill_scaffold_request(
            request_file
        )
        registry = load_skill_registry(
            project_root
        )
        result = plan_skill_scaffold(
            request,
            registry=registry,
        )
    except (
        SkillRegistryError,
        SkillScaffoldPolicyError,
        SkillScaffoldStorageError,
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


@app.command("generate-skill-scaffold")
def generate_skill_scaffold_command(
    request_file: Annotated[
        Path,
        typer.Argument(
            help="Versioned skill scaffold request JSON."
        ),
    ],
    scaffold_root: Annotated[
        Path,
        typer.Option("--scaffold-root"),
    ] = Path("skill-scaffolds"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Generate one isolated, untrusted skill scaffold."""

    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )
    from geoagent_harness.skill_scaffolding import (
        SkillScaffoldGenerationError,
        SkillScaffoldPolicyError,
        SkillScaffoldStorageError,
        generate_skill_scaffold,
        load_skill_scaffold_request,
        plan_skill_scaffold,
    )

    try:
        request = load_skill_scaffold_request(
            request_file
        )
        registry = load_skill_registry(
            project_root
        )
        plan = plan_skill_scaffold(
            request,
            registry=registry,
        )
        result = generate_skill_scaffold(
            plan,
            scaffold_root=scaffold_root,
        )
    except (
        SkillRegistryError,
        SkillScaffoldGenerationError,
        SkillScaffoldPolicyError,
        SkillScaffoldStorageError,
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


@app.command("validate-skill-scaffold")
def validate_skill_scaffold_command(
    scaffold_path: Annotated[
        Path,
        typer.Argument(
            help="Generated skill scaffold bundle."
        ),
    ],
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Validate a scaffold without importing or executing it."""

    from geoagent_harness.skill_scaffolding import (
        SkillScaffoldContractError,
        validate_skill_scaffold_contract,
    )

    try:
        result = validate_skill_scaffold_contract(
            scaffold_path
        )
    except (
        SkillScaffoldContractError,
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

    if not result.passed:
        raise typer.Exit(code=1)

@app.command("plan-snakemake-export")
def plan_snakemake_export_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="Canonical recipe beneath the recipe root."
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Recipe approval beneath the approval root."
        ),
    ],
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Plan a non-executing Snakemake recipe export."""

    from geoagent_harness.recipes import (
        RecipeApprovalError,
        RecipeStorageError,
        load_recipe,
        load_recipe_approval,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )
    from geoagent_harness.snakemake_export import (
        SnakemakeExportPolicyError,
        plan_snakemake_recipe_export,
    )

    try:
        recipe = load_recipe(
            recipe_file,
            recipe_root=recipe_root,
        )
        approval = load_recipe_approval(
            approval_file,
            approval_root=approval_root,
        )
        registry = load_skill_registry(
            project_root
        )

        result = plan_snakemake_recipe_export(
            recipe=recipe,
            approval=approval,
            registry=registry,
            recipe_path=recipe_file,
            approval_path=approval_file,
        )
    except (
        RecipeApprovalError,
        RecipeStorageError,
        SkillRegistryError,
        SnakemakeExportPolicyError,
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


@app.command("export-approved-recipe-snakemake")
def export_approved_recipe_snakemake_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="Canonical recipe beneath the recipe root."
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Recipe approval beneath the approval root."
        ),
    ],
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    export_root: Annotated[
        Path,
        typer.Option("--export-root"),
    ] = Path("snakemake-exports"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Export one exact approved recipe for Snakemake replay."""

    from geoagent_harness.recipes import (
        RecipeApprovalError,
        RecipeStorageError,
        load_recipe,
        load_recipe_approval,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )
    from geoagent_harness.snakemake_export import (
        SnakemakeExportGenerationError,
        SnakemakeExportPolicyError,
        generate_snakemake_recipe_export,
        plan_snakemake_recipe_export,
    )

    try:
        recipe = load_recipe(
            recipe_file,
            recipe_root=recipe_root,
        )
        approval = load_recipe_approval(
            approval_file,
            approval_root=approval_root,
        )
        registry = load_skill_registry(
            project_root
        )

        plan = plan_snakemake_recipe_export(
            recipe=recipe,
            approval=approval,
            registry=registry,
            recipe_path=recipe_file,
            approval_path=approval_file,
        )

        result = generate_snakemake_recipe_export(
            plan,
            export_root=export_root,
        )
    except (
        RecipeApprovalError,
        RecipeStorageError,
        SkillRegistryError,
        SnakemakeExportGenerationError,
        SnakemakeExportPolicyError,
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


@app.command("validate-snakemake-export")
def validate_snakemake_export_command(
    export_path: Annotated[
        Path,
        typer.Argument(
            help="Generated Snakemake replay package."
        ),
    ],
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Statically validate a Snakemake replay package."""

    from geoagent_harness.snakemake_export import (
        SnakemakeExportContractError,
        validate_snakemake_export_contract,
    )

    try:
        result = validate_snakemake_export_contract(
            export_path
        )
    except (
        SnakemakeExportContractError,
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

    if not result.passed:
        raise typer.Exit(code=1)

@app.command("list-approved-recipes")
def list_approved_recipes_command(
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """List deterministic recipe and approval matches."""

    from geoagent_harness.recipes import (
        RecipeInventoryError,
        build_recipe_approval_inventory,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )

    try:
        registry = load_skill_registry(
            project_root
        )

        result = build_recipe_approval_inventory(
            recipe_root=recipe_root,
            approval_root=approval_root,
            registry=registry,
        )
    except (
        RecipeInventoryError,
        SkillRegistryError,
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

@app.command("assess-skill-definition")
def assess_skill_definition_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess a declarative skill without generating code."""

    from geoagent_harness.skill_definitions import (
        SkillDefinitionStorageError,
        assess_declarative_skill,
        load_skill_definition,
    )

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )
        result = assess_declarative_skill(
            definition
        )
    except (
        SkillDefinitionStorageError,
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

    if not result.ready_for_generation:
        raise typer.Exit(code=1)

@app.command("generate-skill-contract")
def generate_skill_contract_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    contract_root: Annotated[
        Path,
        typer.Option("--contract-root"),
    ] = Path("skill-contracts"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Generate one isolated immutable skill contract."""

    from geoagent_harness.skill_definitions import (
        SkillContractGenerationError,
        SkillDefinitionStorageError,
        generate_skill_contract_bundle,
        load_skill_definition,
    )

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )
        result = generate_skill_contract_bundle(
            definition,
            contract_root=contract_root,
        )
    except (
        SkillContractGenerationError,
        SkillDefinitionStorageError,
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

@app.command("validate-skill-contract")
def validate_skill_contract_command(
    bundle_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Generated immutable skill "
                "contract bundle."
            )
        ),
    ],
    contract_root: Annotated[
        Path,
        typer.Option("--contract-root"),
    ] = Path("skill-contracts"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Validate a contract without importing or executing code."""

    from geoagent_harness.skill_definitions import (
        SkillContractGenerationError,
        SkillContractValidationError,
        validate_skill_contract_bundle,
    )

    try:
        result = validate_skill_contract_bundle(
            bundle_path,
            contract_root=contract_root,
        )
    except (
        SkillContractGenerationError,
        SkillContractValidationError,
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

@app.command("generate-skill-candidate")
def generate_skill_candidate_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    scaffold_root: Annotated[
        Path,
        typer.Option("--scaffold-root"),
    ] = Path("skill-scaffolds"),
    candidate_root: Annotated[
        Path,
        typer.Option("--candidate-root"),
    ] = Path("skill-candidates"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Generate one isolated untrusted skill candidate."""

    from geoagent_harness.skill_definitions import (
        DeclarativeSkillScaffoldError,
        SkillDefinitionStorageError,
        TrustedAdapterMaterializationError,
        generate_declarative_skill_scaffold,
        load_skill_definition,
        materialize_trusted_adapter_candidate,
    )
    from geoagent_harness.skill_registry import (
        SkillRegistryError,
        load_skill_registry,
    )

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )

        registry = load_skill_registry(
            project_root
        )

        generated = (
            generate_declarative_skill_scaffold(
                definition,
                registry=registry,
                scaffold_root=scaffold_root,
            )
        )

        result = (
            materialize_trusted_adapter_candidate(
                definition=definition,
                scaffold=generated.scaffold,
                candidate_root=candidate_root,
            )
        )
    except (
        DeclarativeSkillScaffoldError,
        SkillDefinitionStorageError,
        SkillRegistryError,
        TrustedAdapterMaterializationError,
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

@app.command("assess-skill-candidate")
def assess_skill_candidate_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    candidate_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Materialized skill candidate "
                "directory."
            )
        ),
    ],
    test_record_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Isolated candidate-test JSON "
                "record."
            )
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    candidate_root: Annotated[
        Path,
        typer.Option("--candidate-root"),
    ] = Path("skill-candidates"),
    evidence_root: Annotated[
        Path,
        typer.Option("--evidence-root"),
    ] = Path("skill-test-results"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess exact candidate evidence before promotion."""

    from geoagent_harness.skill_definitions import (
        SkillCandidatePromotionError,
        SkillCandidateTestEvidenceError,
        SkillDefinitionStorageError,
        assess_skill_candidate_for_promotion,
        load_skill_candidate_test_record,
        load_skill_definition,
    )

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )

        test_record = (
            load_skill_candidate_test_record(
                test_record_file,
                evidence_root=evidence_root,
            )
        )

        result = (
            assess_skill_candidate_for_promotion(
                definition=definition,
                candidate_path=candidate_path,
                candidate_root=candidate_root,
                test_record=test_record,
            )
        )
    except (
        SkillCandidatePromotionError,
        SkillCandidateTestEvidenceError,
        SkillDefinitionStorageError,
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

    if not result.ready_for_promotion_review:
        raise typer.Exit(code=1)

@app.command("plan-skill-promotion")
def plan_skill_promotion_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    candidate_path: Annotated[
        Path,
        typer.Argument(
            help="Materialized candidate directory."
        ),
    ],
    test_record_file: Annotated[
        Path,
        typer.Argument(
            help="Isolated candidate-test JSON record."
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    candidate_root: Annotated[
        Path,
        typer.Option("--candidate-root"),
    ] = Path("skill-candidates"),
    evidence_root: Annotated[
        Path,
        typer.Option("--evidence-root"),
    ] = Path("skill-test-results"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Plan exact trusted writes without performing them."""

    from geoagent_harness.skill_definitions import (
        SkillCandidateTestEvidenceError,
        SkillDefinitionStorageError,
        SkillPromotionPlanError,
        load_skill_candidate_test_record,
        load_skill_definition,
        plan_skill_candidate_promotion,
    )

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )

        test_record = (
            load_skill_candidate_test_record(
                test_record_file,
                evidence_root=evidence_root,
            )
        )

        result = plan_skill_candidate_promotion(
            definition=definition,
            candidate_path=candidate_path,
            candidate_root=candidate_root,
            test_record=test_record,
            project_root=project_root,
        )
    except (
        SkillCandidateTestEvidenceError,
        SkillDefinitionStorageError,
        SkillPromotionPlanError,
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

@app.command("promote-skill-candidate")
def promote_skill_candidate_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    candidate_path: Annotated[
        Path,
        typer.Argument(
            help="Materialized candidate directory."
        ),
    ],
    test_record_file: Annotated[
        Path,
        typer.Argument(
            help="Isolated candidate-test JSON record."
        ),
    ],
    confirmed_skill_id: Annotated[
        str,
        typer.Option(
            "--confirm-skill-id",
            help=(
                "Exact skill ID explicitly approved "
                "for trusted promotion."
            ),
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    candidate_root: Annotated[
        Path,
        typer.Option("--candidate-root"),
    ] = Path("skill-candidates"),
    evidence_root: Annotated[
        Path,
        typer.Option("--evidence-root"),
    ] = Path("skill-test-results"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Explicitly promote one exact verified candidate."""

    from geoagent_harness.skill_definitions import (
        SkillCandidatePromotionExecutionError,
        SkillCandidateTestEvidenceError,
        SkillDefinitionStorageError,
        load_skill_candidate_test_record,
        load_skill_definition,
        promote_skill_candidate,
    )

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )

        test_record = (
            load_skill_candidate_test_record(
                test_record_file,
                evidence_root=evidence_root,
            )
        )

        result = promote_skill_candidate(
            definition=definition,
            candidate_path=candidate_path,
            candidate_root=candidate_root,
            test_record=test_record,
            project_root=project_root,
            confirmed_skill_id=(
                confirmed_skill_id
            ),
        )
    except (
        SkillCandidatePromotionExecutionError,
        SkillCandidateTestEvidenceError,
        SkillDefinitionStorageError,
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

@app.command("inspect-raster")
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

    from geoagent_harness.skill_adapters.raster_inspection import (
        RasterInspectionError,
    )
    from geoagent_harness.skills.inspect_raster.policy import (
        InspectRasterPolicyError,
    )
    from geoagent_harness.skills.inspect_raster.schemas import (
        InspectRasterArguments,
    )
    from geoagent_harness.skills.inspect_raster.service import (
        inspect_raster,
    )

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


@app.command("plan-convert-raster")
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

    from geoagent_harness.mcp_server.settings import (
        MCPSettings,
    )
    from geoagent_harness.skills.convert_raster.policy import (
        ConvertRasterPolicyError,
        validate_convert_raster_request,
    )
    from geoagent_harness.skills.convert_raster.schemas import (
        ConvertRasterArguments,
    )

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


@app.command("convert-raster")
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

    from geoagent_harness.mcp_server.settings import (
        load_settings,
    )
    from geoagent_harness.skills.convert_raster.schemas import (
        ConvertRasterArguments,
    )
    from geoagent_harness.skills.convert_raster.service import (
        ConvertRasterError,
        convert_raster,
    )

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


@app.command("validate-raster-conversion")
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

    from geoagent_harness.mcp_server.settings import (
        MCPSettings,
    )
    from geoagent_harness.skills.convert_raster.schemas import (
        ConvertRasterArguments,
    )
    from geoagent_harness.skills.convert_raster.validation import (
        ConvertRasterValidationError,
        validate_raster_conversion,
    )

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

@app.command("builder-propose")
def builder_propose_command(
    request_file: Annotated[
        Path,
        typer.Option(
            "--request-file",
            help="Read-only Builder request JSON file.",
        ),
    ],
    request_root: Annotated[
        Path,
        typer.Option(
            "--request-root",
            help="Approved Builder request root.",
        ),
    ] = Path("builder-requests"),
    agents_root: Annotated[
        Path,
        typer.Option(
            "--agents-root",
            help="Trusted agent manifest root.",
        ),
    ] = Path("agents"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Generate one validated proposal without writing files."""

    from geoagent_harness.builder import (
        BuilderAgentError,
        BuilderRequestLoadError,
        load_builder_request,
        propose_builder_candidate,
    )
    from geoagent_harness.model import (
        ModelClientError,
        ModelSettingsError,
    )

    try:
        request = load_builder_request(
            request_file,
            request_root=request_root,
        )
        result = propose_builder_candidate(
            request=request,
            agents_root=agents_root,
        )
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MODEL,
        )
    except ModelClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MODEL,
        )
    except (
        BuilderAgentError,
        BuilderRequestLoadError,
        ModelSettingsError,
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

@app.command("materialize-builder-proposal")
def materialize_builder_proposal_command(
    generation_file: Annotated[
        Path,
        typer.Option(
            "--generation-file",
            help=(
                "Operator-saved Builder generation "
                "result JSON."
            ),
        ),
    ],
    generation_root: Annotated[
        Path,
        typer.Option(
            "--generation-root",
            help="Approved Builder generation root.",
        ),
    ] = Path("builder-generations"),
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help=(
                "Root for isolated untrusted "
                "Builder candidates."
            ),
        ),
    ] = Path("builder-candidates"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Materialize one proposal outside the Builder container."""

    from geoagent_harness.builder import (
        BuilderMaterializationError,
        materialize_builder_proposal,
    )

    try:
        result = materialize_builder_proposal(
            generation_file=generation_file,
            generation_root=generation_root,
            candidate_root=candidate_root,
        )
    except (
        BuilderMaterializationError,
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

@app.command("create-builder-review-package")
def create_builder_review_package_command(
    generation_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Operator-saved Builder generation "
                "result JSON."
            ),
        ),
    ],
    candidate_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Materialized Builder candidate "
                "directory."
            ),
        ),
    ],
    test_record_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Isolated Builder candidate-test "
                "JSON record."
            ),
        ),
    ],
    generation_root: Annotated[
        Path,
        typer.Option(
            "--generation-root",
            help="Approved Builder generation root.",
        ),
    ] = Path("builder-generations"),
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help="Approved Builder candidate root.",
        ),
    ] = Path("builder-candidates"),
    evidence_root: Annotated[
        Path,
        typer.Option(
            "--evidence-root",
            help="Approved Builder test-evidence root.",
        ),
    ] = Path("builder-test-results"),
    review_root: Annotated[
        Path,
        typer.Option(
            "--review-root",
            help=(
                "Root for immutable Builder "
                "human-review packages."
            ),
        ),
    ] = Path("builder-reviews"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Assemble and persist one immutable review package."""

    from geoagent_harness.builder import (
        BuilderReviewError,
        BuilderReviewStorageError,
        assemble_builder_review_package,
        persist_builder_review_package,
    )

    try:
        review = assemble_builder_review_package(
            generation_file=generation_file,
            generation_root=generation_root,
            candidate_path=candidate_path,
            candidate_root=candidate_root,
            test_record_path=test_record_file,
            evidence_root=evidence_root,
        )
        result = persist_builder_review_package(
            review,
            review_root=review_root,
        )
    except (
        BuilderReviewError,
        BuilderReviewStorageError,
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

@app.command("record-builder-review-decision")
def record_builder_review_decision_command(
    review_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder REVIEW.json file.",
        ),
    ],
    decision_id: Annotated[
        str,
        typer.Option(
            "--decision-id",
            help="Unique human decision identifier.",
        ),
    ],
    reviewer_id: Annotated[
        str,
        typer.Option(
            "--reviewer-id",
            help="Identity of the human reviewer.",
        ),
    ],
    decided_at: Annotated[
        str,
        typer.Option(
            "--decided-at",
            help=(
                "Timezone-aware ISO-8601 decision "
                "timestamp."
            ),
        ),
    ],
    decision: Annotated[
        str,
        typer.Option(
            "--decision",
            help="Either approved or rejected.",
        ),
    ],
    rationale: Annotated[
        str,
        typer.Option(
            "--rationale",
            help="Human explanation for the decision.",
        ),
    ],
    approved_paths: Annotated[
        list[str] | None,
        typer.Option(
            "--approved-path",
            help=(
                "Exact reviewed path approved for later "
                "promotion planning; repeat as needed."
            ),
        ),
    ] = None,
    review_root: Annotated[
        Path,
        typer.Option(
            "--review-root",
            help="Approved Builder review-package root.",
        ),
    ] = Path("builder-reviews"),
    decision_root: Annotated[
        Path,
        typer.Option(
            "--decision-root",
            help=(
                "Root for immutable Builder "
                "human-decision records."
            ),
        ),
    ] = Path("builder-decisions"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Record one human decision without promoting files."""

    from datetime import datetime

    from geoagent_harness.builder import (
        BuilderReviewDecisionError,
        BuilderReviewDecisionStorageError,
        create_builder_review_decision,
        persist_builder_review_decision,
    )

    try:
        normalized_timestamp = (
            decided_at[:-1] + "+00:00"
            if decided_at.endswith("Z")
            else decided_at
        )
        parsed_timestamp = datetime.fromisoformat(
            normalized_timestamp
        )

        if decision not in {
            "approved",
            "rejected",
        }:
            raise ValueError(
                "decision must be approved or rejected"
            )

        review_decision = (
            create_builder_review_decision(
                review_file=review_file,
                review_root=review_root,
                decision_id=decision_id,
                reviewer_id=reviewer_id,
                decided_at=parsed_timestamp,
                decision=decision,
                approved_paths=(
                    []
                    if approved_paths is None
                    else approved_paths
                ),
                rationale=rationale,
            )
        )

        result = persist_builder_review_decision(
            review_decision,
            decision_root=decision_root,
            review_root=review_root,
        )
    except (
        BuilderReviewDecisionError,
        BuilderReviewDecisionStorageError,
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

@app.command("plan-builder-promotion")
def plan_builder_promotion_command(
    decision_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder DECISION.json file.",
        ),
    ],
    decision_root: Annotated[
        Path,
        typer.Option(
            "--decision-root",
            help="Approved Builder decision root.",
        ),
    ] = Path("builder-decisions"),
    review_root: Annotated[
        Path,
        typer.Option(
            "--review-root",
            help="Approved Builder review-package root.",
        ),
    ] = Path("builder-reviews"),
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help="Approved Builder candidate root.",
        ),
    ] = Path("builder-candidates"),
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help=(
                "Trusted project root used only for "
                "non-writing destination assessment."
            ),
        ),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Plan exact approved Builder writes without performing them."""

    from geoagent_harness.builder import (
        BuilderPromotionPlanError,
        plan_builder_promotion,
    )

    try:
        result = plan_builder_promotion(
            decision_file=decision_file,
            decision_root=decision_root,
            review_root=review_root,
            candidate_root=candidate_root,
            project_root=project_root,
        )
    except (
        BuilderPromotionPlanError,
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


@app.command("create-builder-promotion-plan")
def create_builder_promotion_plan_command(
    decision_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder DECISION.json file.",
        ),
    ],
    decision_root: Annotated[
        Path,
        typer.Option(
            "--decision-root",
            help="Approved Builder decision root.",
        ),
    ] = Path("builder-decisions"),
    review_root: Annotated[
        Path,
        typer.Option(
            "--review-root",
            help="Approved Builder review-package root.",
        ),
    ] = Path("builder-reviews"),
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help="Approved Builder candidate root.",
        ),
    ] = Path("builder-candidates"),
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help=(
                "Trusted project root used only for "
                "non-writing destination assessment."
            ),
        ),
    ] = Path("."),
    plan_root: Annotated[
        Path,
        typer.Option(
            "--plan-root",
            help="Immutable Builder promotion-plan root.",
        ),
    ] = Path("builder-promotion-plans"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Create an immutable, reverified Builder promotion plan."""

    from geoagent_harness.builder import (
        BuilderPromotionPlanError,
        BuilderPromotionPlanStorageError,
        persist_builder_promotion_plan,
        plan_builder_promotion,
    )

    try:
        plan = plan_builder_promotion(
            decision_file=decision_file,
            decision_root=decision_root,
            review_root=review_root,
            candidate_root=candidate_root,
            project_root=project_root,
        )

        result = persist_builder_promotion_plan(
            plan,
            plan_root=plan_root,
            decision_root=decision_root,
            review_root=review_root,
            candidate_root=candidate_root,
            project_root=project_root,
        )
    except (
        BuilderPromotionPlanError,
        BuilderPromotionPlanStorageError,
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

@app.command("promote-builder-candidate")
def promote_builder_candidate_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder PLAN.json file.",
        ),
    ],
    plan_root: Annotated[
        Path,
        typer.Option(
            "--plan-root",
            help="Approved Builder promotion-plan root.",
        ),
    ] = Path("builder-promotion-plans"),
    decision_root: Annotated[
        Path,
        typer.Option(
            "--decision-root",
            help="Approved Builder decision root.",
        ),
    ] = Path("builder-decisions"),
    review_root: Annotated[
        Path,
        typer.Option(
            "--review-root",
            help="Approved Builder review-package root.",
        ),
    ] = Path("builder-reviews"),
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help="Approved Builder candidate root.",
        ),
    ] = Path("builder-candidates"),
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help=(
                "Trusted project root used only for "
                "destination-state reverification."
            ),
        ),
    ] = Path("."),
    promotion_root: Annotated[
        Path,
        typer.Option(
            "--promotion-root",
            help="Immutable promoted Builder-bundle root.",
        ),
    ] = Path("builder-promotions"),
    confirm_decision_id: Annotated[
        str,
        typer.Option(
            "--confirm-decision-id",
            help=(
                "Exact approved decision ID that the "
                "operator authorizes for promotion."
            ),
        ),
    ] = "",
    confirm_plan_sha256: Annotated[
        str,
        typer.Option(
            "--confirm-plan-sha256",
            help=(
                "Exact persisted promotion-plan SHA-256 "
                "that the operator authorizes."
            ),
        ),
    ] = "",
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Atomically promote approved files into an immutable bundle."""

    from geoagent_harness.builder import (
        BuilderPromotionError,
        promote_builder_candidate,
    )

    if not confirm_decision_id:
        typer.echo(
            "Error: --confirm-decision-id is required",
            err=True,
        )
        raise typer.Exit(code=2)

    if not confirm_plan_sha256:
        typer.echo(
            "Error: --confirm-plan-sha256 is required",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        result = promote_builder_candidate(
            plan_file=plan_file,
            plan_root=plan_root,
            decision_root=decision_root,
            review_root=review_root,
            candidate_root=candidate_root,
            project_root=project_root,
            promotion_root=promotion_root,
            confirm_decision_id=(
                confirm_decision_id
            ),
            confirm_plan_sha256=(
                confirm_plan_sha256
            ),
        )
    except (
        BuilderPromotionError,
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

@app.command("verify-builder-promotion")
def verify_builder_promotion_command(
    promotion_directory: Annotated[
        Path,
        typer.Argument(
            help=(
                "Promoted Builder bundle directory."
            ),
        ),
    ],
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder PLAN.json file.",
        ),
    ],
    promotion_root: Annotated[
        Path,
        typer.Option(
            "--promotion-root",
            help="Approved promoted Builder-bundle root.",
        ),
    ] = Path("builder-promotions"),
    plan_root: Annotated[
        Path,
        typer.Option(
            "--plan-root",
            help="Approved Builder promotion-plan root.",
        ),
    ] = Path("builder-promotion-plans"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Independently verify one promoted bundle read-only."""

    from geoagent_harness.builder import (
        BuilderPromotionVerificationError,
        verify_builder_promotion_bundle,
    )

    try:
        result = verify_builder_promotion_bundle(
            promotion_directory,
            promotion_root=promotion_root,
            plan_file=plan_file,
            plan_root=plan_root,
        )
    except (
        BuilderPromotionVerificationError,
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

@app.command(
    "create-builder-promotion-verification"
)
def create_builder_promotion_verification_command(
    promotion_directory: Annotated[
        Path,
        typer.Argument(
            help="Immutable promoted Builder bundle.",
        ),
    ],
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder PLAN.json file.",
        ),
    ],
    promotion_root: Annotated[
        Path,
        typer.Option(
            "--promotion-root",
            help="Approved Builder promotion root.",
        ),
    ] = Path("builder-promotions"),
    plan_root: Annotated[
        Path,
        typer.Option(
            "--plan-root",
            help="Approved Builder promotion-plan root.",
        ),
    ] = Path("builder-promotion-plans"),
    verification_root: Annotated[
        Path,
        typer.Option(
            "--verification-root",
            help=(
                "Root for immutable Builder "
                "verification evidence."
            ),
        ),
    ] = Path("builder-promotion-verifications"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Verify a promoted bundle and persist exact evidence."""

    from geoagent_harness.builder import (
        BuilderPromotionVerificationError,
        BuilderPromotionVerificationStorageError,
        persist_builder_promotion_verification,
        verify_builder_promotion_bundle,
    )

    try:
        verification = (
            verify_builder_promotion_bundle(
                promotion_directory=(
                    promotion_directory
                ),
                promotion_root=promotion_root,
                plan_file=plan_file,
                plan_root=plan_root,
            )
        )

        result = (
            persist_builder_promotion_verification(
                verification,
                verification_root=(
                    verification_root
                ),
                promotion_root=promotion_root,
                plan_root=plan_root,
            )
        )
    except (
        BuilderPromotionVerificationError,
        BuilderPromotionVerificationStorageError,
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

@app.command("create-builder-activation-review")
def create_builder_activation_review_command(
    verification_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder VERIFICATION.json.",
        ),
    ],
    verification_root: Annotated[
        Path,
        typer.Option(
            "--verification-root",
            help="Approved verification-evidence root.",
        ),
    ] = Path("builder-promotion-verifications"),
    promotion_root: Annotated[
        Path,
        typer.Option(
            "--promotion-root",
            help="Approved Builder promotion root.",
        ),
    ] = Path("builder-promotions"),
    plan_root: Annotated[
        Path,
        typer.Option(
            "--plan-root",
            help="Approved Builder promotion-plan root.",
        ),
    ] = Path("builder-promotion-plans"),
    decision_root: Annotated[
        Path,
        typer.Option(
            "--decision-root",
            help=(
                "Root for immutable activation-review "
                "decisions."
            ),
        ),
    ] = Path("builder-activation-decisions"),
    decision_id: Annotated[
        str,
        typer.Option(
            "--decision-id",
            help="Unique activation-review decision ID.",
        ),
    ] = "",
    reviewer_id: Annotated[
        str,
        typer.Option(
            "--reviewer-id",
            help="Human reviewer identity.",
        ),
    ] = "",
    decided_at: Annotated[
        str,
        typer.Option(
            "--decided-at",
            help=(
                "Timezone-aware ISO-8601 decision "
                "timestamp."
            ),
        ),
    ] = "",
    decision: Annotated[
        str,
        typer.Option(
            "--decision",
            help="Either approved or rejected.",
        ),
    ] = "rejected",
    rationale: Annotated[
        str,
        typer.Option(
            "--rationale",
            help="Human activation-review rationale.",
        ),
    ] = "",
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Review and persist one verified Builder bundle."""

    from geoagent_harness.builder import (
        BuilderActivationReviewDecisionStorageError,
        BuilderActivationReviewError,
        create_builder_activation_review_decision,
        persist_builder_activation_review_decision,
    )

    if not decision_id:
        typer.echo(
            "Error: --decision-id is required",
            err=True,
        )
        raise typer.Exit(code=2)

    if not reviewer_id:
        typer.echo(
            "Error: --reviewer-id is required",
            err=True,
        )
        raise typer.Exit(code=2)

    if not decided_at:
        typer.echo(
            "Error: --decided-at is required",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        decision_timestamp = (
            datetime.fromisoformat(decided_at)
        )
    except ValueError as exc:
        typer.echo(
            "Error: --decided-at must be a valid "
            "ISO-8601 timestamp",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    if (
        decision_timestamp.tzinfo is None
        or decision_timestamp.utcoffset() is None
    ):
        typer.echo(
            "Error: --decided-at must include "
            "a timezone",
            err=True,
        )
        raise typer.Exit(code=2)

    if not rationale:
        typer.echo(
            "Error: --rationale is required",
            err=True,
        )
        raise typer.Exit(code=2)

    if decision not in {
        "approved",
        "rejected",
    }:
        typer.echo(
            "Error: --decision must be approved "
            "or rejected",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        review_decision = (
            create_builder_activation_review_decision(
                verification_file=verification_file,
                verification_root=verification_root,
                promotion_root=promotion_root,
                plan_root=plan_root,
                decision_id=decision_id,
                reviewer_id=reviewer_id,
                decided_at=decision_timestamp,
                decision=decision,
                rationale=rationale,
            )
        )

        result = (
            persist_builder_activation_review_decision(
                review_decision,
                decision_root=decision_root,
                verification_root=verification_root,
                promotion_root=promotion_root,
                plan_root=plan_root,
            )
        )
    except (
        BuilderActivationReviewError,
        BuilderActivationReviewDecisionStorageError,
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

@app.command("plan-builder-activation")
def plan_builder_activation_command(
    activation_decision_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Immutable Builder "
                "ACTIVATION_DECISION.json."
            ),
        ),
    ],
    activation_decision_root: Annotated[
        Path,
        typer.Option(
            "--activation-decision-root",
            help="Approved activation-decision root.",
        ),
    ] = Path("builder-activation-decisions"),
    verification_root: Annotated[
        Path,
        typer.Option(
            "--verification-root",
            help="Approved verification-evidence root.",
        ),
    ] = Path("builder-promotion-verifications"),
    promotion_root: Annotated[
        Path,
        typer.Option(
            "--promotion-root",
            help="Approved Builder promotion root.",
        ),
    ] = Path("builder-promotions"),
    promotion_plan_root: Annotated[
        Path,
        typer.Option(
            "--promotion-plan-root",
            help="Approved promotion-plan root.",
        ),
    ] = Path("builder-promotion-plans"),
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help=(
                "Trusted project root used only for "
                "destination assessment."
            ),
        ),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Plan exact Builder activation writes without writing."""

    from geoagent_harness.builder import (
        BuilderActivationPlanError,
        plan_builder_activation,
    )

    try:
        result = plan_builder_activation(
            activation_decision_file=(
                activation_decision_file
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )
    except (
        BuilderActivationPlanError,
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


@app.command("create-builder-activation-plan")
def create_builder_activation_plan_command(
    activation_decision_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Immutable Builder "
                "ACTIVATION_DECISION.json."
            ),
        ),
    ],
    activation_decision_root: Annotated[
        Path,
        typer.Option(
            "--activation-decision-root",
        ),
    ] = Path("builder-activation-decisions"),
    verification_root: Annotated[
        Path,
        typer.Option("--verification-root"),
    ] = Path("builder-promotion-verifications"),
    promotion_root: Annotated[
        Path,
        typer.Option("--promotion-root"),
    ] = Path("builder-promotions"),
    promotion_plan_root: Annotated[
        Path,
        typer.Option("--promotion-plan-root"),
    ] = Path("builder-promotion-plans"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    activation_plan_root: Annotated[
        Path,
        typer.Option(
            "--activation-plan-root",
            help=(
                "Root for immutable Builder "
                "activation plans."
            ),
        ),
    ] = Path("builder-activation-plans"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Create one immutable reverified activation plan."""

    from geoagent_harness.builder import (
        BuilderActivationPlanError,
        BuilderActivationPlanStorageError,
        persist_builder_activation_plan,
        plan_builder_activation,
    )

    try:
        plan = plan_builder_activation(
            activation_decision_file=(
                activation_decision_file
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )

        result = persist_builder_activation_plan(
            plan,
            plan_root=activation_plan_root,
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )
    except (
        BuilderActivationPlanError,
        BuilderActivationPlanStorageError,
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

@app.command("activate-builder-bundle")
def activate_builder_bundle_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder ACTIVATION_PLAN.json.",
        ),
    ],
    activation_plan_root: Annotated[
        Path,
        typer.Option(
            "--activation-plan-root",
            help="Approved Builder activation-plan root.",
        ),
    ] = Path("builder-activation-plans"),
    activation_decision_root: Annotated[
        Path,
        typer.Option(
            "--activation-decision-root",
            help=(
                "Approved Builder activation-decision "
                "root."
            ),
        ),
    ] = Path("builder-activation-decisions"),
    verification_root: Annotated[
        Path,
        typer.Option("--verification-root"),
    ] = Path("builder-promotion-verifications"),
    promotion_root: Annotated[
        Path,
        typer.Option("--promotion-root"),
    ] = Path("builder-promotions"),
    promotion_plan_root: Annotated[
        Path,
        typer.Option("--promotion-plan-root"),
    ] = Path("builder-promotion-plans"),
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help="Trusted project destination root.",
        ),
    ] = Path("."),
    activation_root: Annotated[
        Path,
        typer.Option(
            "--activation-root",
            help="Immutable Builder activation-evidence root.",
        ),
    ] = Path("builder-activations"),
    confirm_activation_decision_id: Annotated[
        str,
        typer.Option(
            "--confirm-activation-decision-id",
            help=(
                "Exact approved activation-decision ID "
                "authorized by the operator."
            ),
        ),
    ] = "",
    confirm_activation_plan_sha256: Annotated[
        str,
        typer.Option(
            "--confirm-activation-plan-sha256",
            help=(
                "Exact persisted activation-plan SHA-256 "
                "authorized by the operator."
            ),
        ),
    ] = "",
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Install exact approved Builder files transactionally."""

    from geoagent_harness.builder import (
        BuilderActivationError,
        activate_builder_bundle,
    )

    if not confirm_activation_decision_id:
        typer.echo(
            "Error: "
            "--confirm-activation-decision-id "
            "is required",
            err=True,
        )
        raise typer.Exit(code=2)

    if not confirm_activation_plan_sha256:
        typer.echo(
            "Error: "
            "--confirm-activation-plan-sha256 "
            "is required",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        result = activate_builder_bundle(
            plan_file=plan_file,
            activation_plan_root=(
                activation_plan_root
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
            activation_root=activation_root,
            confirm_activation_decision_id=(
                confirm_activation_decision_id
            ),
            confirm_activation_plan_sha256=(
                confirm_activation_plan_sha256
            ),
        )
    except (
        BuilderActivationError,
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

@app.command("verify-builder-activation")
def verify_builder_activation_command(
    activation_directory: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder activation directory.",
        ),
    ],
    activation_plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder ACTIVATION_PLAN.json.",
        ),
    ],
    activation_root: Annotated[
        Path,
        typer.Option("--activation-root"),
    ] = Path("builder-activations"),
    activation_plan_root: Annotated[
        Path,
        typer.Option("--activation-plan-root"),
    ] = Path("builder-activation-plans"),
    activation_decision_root: Annotated[
        Path,
        typer.Option("--activation-decision-root"),
    ] = Path("builder-activation-decisions"),
    verification_root: Annotated[
        Path,
        typer.Option("--verification-root"),
    ] = Path("builder-promotion-verifications"),
    promotion_root: Annotated[
        Path,
        typer.Option("--promotion-root"),
    ] = Path("builder-promotions"),
    promotion_plan_root: Annotated[
        Path,
        typer.Option("--promotion-plan-root"),
    ] = Path("builder-promotion-plans"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Verify exact activated Builder files without execution."""

    from geoagent_harness.builder import (
        BuilderPostActivationVerificationError,
        verify_builder_activation,
    )

    try:
        result = verify_builder_activation(
            activation_directory=(
                activation_directory
            ),
            activation_root=activation_root,
            activation_plan_file=(
                activation_plan_file
            ),
            activation_plan_root=(
                activation_plan_root
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )
    except (
        BuilderPostActivationVerificationError,
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


@app.command("create-builder-trust-evidence")
def create_builder_trust_evidence_command(
    activation_directory: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder activation directory.",
        ),
    ],
    activation_plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder ACTIVATION_PLAN.json.",
        ),
    ],
    activation_root: Annotated[
        Path,
        typer.Option("--activation-root"),
    ] = Path("builder-activations"),
    activation_plan_root: Annotated[
        Path,
        typer.Option("--activation-plan-root"),
    ] = Path("builder-activation-plans"),
    activation_decision_root: Annotated[
        Path,
        typer.Option("--activation-decision-root"),
    ] = Path("builder-activation-decisions"),
    verification_root: Annotated[
        Path,
        typer.Option("--verification-root"),
    ] = Path("builder-promotion-verifications"),
    promotion_root: Annotated[
        Path,
        typer.Option("--promotion-root"),
    ] = Path("builder-promotions"),
    promotion_plan_root: Annotated[
        Path,
        typer.Option("--promotion-plan-root"),
    ] = Path("builder-promotion-plans"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    trust_evidence_root: Annotated[
        Path,
        typer.Option(
            "--trust-evidence-root",
            help=(
                "Root for immutable post-activation "
                "trust evidence."
            ),
        ),
    ] = Path(
        "builder-post-activation-verifications"
    ),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Verify activation and persist immutable trust evidence."""

    from geoagent_harness.builder import (
        BuilderPostActivationVerificationError,
        BuilderPostActivationVerificationStorageError,
        persist_builder_trust_evidence,
        verify_builder_activation,
    )

    try:
        verification = verify_builder_activation(
            activation_directory=(
                activation_directory
            ),
            activation_root=activation_root,
            activation_plan_file=(
                activation_plan_file
            ),
            activation_plan_root=(
                activation_plan_root
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )

        result = persist_builder_trust_evidence(
            verification,
            evidence_root=trust_evidence_root,
            activation_root=activation_root,
            activation_plan_root=(
                activation_plan_root
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )
    except (
        BuilderPostActivationVerificationError,
        BuilderPostActivationVerificationStorageError,
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

@app.command("record-gis-operational-history")
def record_gis_operational_history_command(
    trace_path: Annotated[
        Path,
        typer.Argument(
            help="Validated workflow trace JSON file.",
        ),
    ],
    report_path: Annotated[
        Path,
        typer.Argument(
            help="Validated workflow Markdown report.",
        ),
    ],
    task_id: Annotated[
        str,
        typer.Option(
            "--task-id",
            help="Exact task identity observed by the caller.",
        ),
    ],
    correlation_id: Annotated[
        str,
        typer.Option(
            "--correlation-id",
            help="Correlation identity shared across agent runs.",
        ),
    ],
    agent_instance_id: Annotated[
        str,
        typer.Option(
            "--agent-instance-id",
            help="Identity of the observed GIS service instance.",
        ),
    ],
    agent_run_id: Annotated[
        str,
        typer.Option(
            "--agent-run-id",
            help="Unique identity of the observed GIS invocation.",
        ),
    ],
    parent_run_id: Annotated[
        str | None,
        typer.Option(
            "--parent-run-id",
            help="Optional parent Executor run identity.",
        ),
    ] = None,
    trace_root: Annotated[
        Path,
        typer.Option("--trace-root"),
    ] = Path("traces"),
    report_root: Annotated[
        Path,
        typer.Option("--report-root"),
    ] = Path("reports"),
    event_root: Annotated[
        Path,
        typer.Option("--event-root"),
    ] = Path("operational-history"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Derive one GIS run history from verified evidence."""

    from geoagent_harness.operational_history import (
        AgentRole,
        OperationalHistoryError,
        OperationalIdentity,
        build_operational_timeline,
        load_operational_events,
        operational_event_log_path,
        record_gis_workflow_history,
    )

    try:
        identity = OperationalIdentity(
            agent_id=AgentRole.GIS,
            agent_instance_id=agent_instance_id,
            agent_run_id=agent_run_id,
            task_id=task_id,
            correlation_id=correlation_id,
            parent_run_id=parent_run_id,
        )
        recorded = record_gis_workflow_history(
            trace_path=trace_path,
            report_path=report_path,
            trace_root=trace_root,
            report_root=report_root,
            event_root=event_root,
            identity=identity,
        )
        event_file = operational_event_log_path(
            event_root=event_root,
            correlation_id=correlation_id,
        )
        all_events = load_operational_events(
            event_file,
            event_root=event_root,
        )
        timeline = build_operational_timeline(
            all_events
        )
    except (
        OperationalHistoryError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            {
                "status": "recorded",
                "event_file": event_file.as_posix(),
                "recorded_event_count": len(recorded),
                "timeline": timeline.model_dump(mode="json"),
            },
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )


@app.command("inspect-operational-history")
def inspect_operational_history_command(
    event_file: Annotated[
        Path,
        typer.Argument(
            help="Correlation-scoped operational event JSONL file.",
        ),
    ],
    event_root: Annotated[
        Path,
        typer.Option(
            "--event-root",
            help="Approved operational-history root.",
        ),
    ] = Path("operational-history"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Validate and display one correlated event timeline."""

    from geoagent_harness.operational_history import (
        OperationalHistoryError,
        build_operational_timeline,
        load_operational_events,
    )

    try:
        events = load_operational_events(
            event_file,
            event_root=event_root,
        )
        timeline = build_operational_timeline(events)
    except (
        OperationalHistoryError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            timeline.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )


if __name__ == "__main__":
    app()
