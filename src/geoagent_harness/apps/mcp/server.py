"""MCP server exposing a fixed GIS tool allowlist."""

from __future__ import annotations
from geoagent_harness.contracts.postgres import ImportCSV
from geoagent_harness.workspaces.sandbox.contracts import DatasetOptions
from geoagent_harness.data.tabular.dataset_views import DatasetViewRequest
from typing import Any, Literal
from geoagent_harness.contracts.analysis_options import AnalysisOptions, TableSourceOptions

from mcp.server.fastmcp import FastMCP
from functools import wraps
from dataclasses import replace
from geoagent_harness.core.execution.actions import task_entrypoint
from geoagent_harness.platform.execution_services import execution_services, using_execution_services
from geoagent_harness.contracts.statistics import StatisticsSpec, RegressionSpec
from mcp.server.transport_security import (
    TransportSecuritySettings,
)
from geoagent_harness.task_actions.approved_workflow import run_approved_vector_postgis_workflow

from geoagent_harness.task_actions import data_tools as tools
from geoagent_harness.apps.mcp.transport import MCPTransportSettings, load_transport_settings

from geoagent_harness.task_actions.approved_recipe import run_approved_recipe


class _ContextMCP(FastMCP):
    """Bind every fixed MCP ingress, including legacy operation aliases."""
    def tool(self, *args, **kwargs):
        register=super().tool(*args, **kwargs)
        # MCP already has a writable trace mount in the read-only tools image.
        # Keep this ledger separate from host/controller source-path identities.
        profile=replace(execution_services(),audit_namespace='mcp')
        def decorate(function):
            admitted=task_entrypoint(function, trigger='mcp',
                audit=function.__name__ not in {'health_check','list_operation_contracts','workflow_report'})
            @wraps(admitted)
            def invoke(*values, **options):
                with using_execution_services(profile):
                    return admitted(*values, **options)
            return register(invoke)
        return decorate


def create_mcp_server(
    settings: MCPTransportSettings | None = None,
) -> FastMCP:
    """Create the server with fixed tools and transport policy."""

    active = settings or MCPTransportSettings()

    server = _ContextMCP(
        "GeoAgent GIS MCP",
        host=active.host,
        port=active.port,
        streamable_http_path=active.path,
        json_response=True,
        stateless_http=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[
                "mcp-gis:*",
                "localhost:*",
                "127.0.0.1:*",
            ],
            allowed_origins=[
                "http://mcp-gis:*",
                "http://localhost:*",
                "http://127.0.0.1:*",
            ],
        ),
    )

    @server.tool()
    def health_check() -> dict:
        """Return redacted readiness and security state."""

        return tools.health_check().model_dump(
            mode="json"
        )

    @server.tool()
    def discover_postgres_tables(target_schema:str='agent_sandbox')->dict:
        """Read ordinary table names in an allowed schema. Never writes or authorizes."""
        return tools.discover_postgres_tables(target_schema)

    @server.tool()
    def inspect_postgres_table(target_schema:str,target_table:str,preview_rows:int=5)->dict:
        """Bounded exact all-row snapshot/count/nulls and preview, including soft-deleted records."""
        return tools.inspect_postgres_table(target_schema,target_table,preview_rows)

    @server.tool()
    def validate_postgres_import(arguments:ImportCSV)->dict:
        """Read-only full-source cast/null/key mapping validation; no database write or authority."""
        return tools.validate_postgres_import(arguments.model_dump(mode='json'))

    @server.tool()
    def discover_inputs(directory:str)->dict:
        """Discover supported files and bounded CSV headers in one input folder; no raw rows, recursion or writes."""
        return tools.discover_inputs(directory)

    @server.tool()
    def assess_table(path:str,operation:Literal['profile','quality','group','select_csv_columns','join_csv','calculate_csv_columns','statistical_model']='profile')->dict:
        """Assess this operation's byte/row strategy; runtime limits remain authoritative, no execution approval."""
        return tools.assess_table(path,operation)

    @server.tool()
    def explore_dataset_view(request:DatasetViewRequest)->dict:
        """Read or calculate a chat-bound selected-column/group view, with exact count percentages. No LLM, writes or workflow dispatch."""
        return tools.explore_dataset_view(request.model_dump(mode='json'))

    @server.tool()
    def profile_dataset(path:str,options:DatasetOptions|None=None)->dict:
        """All-field observed types, candidate roles, numeric distributions and codebook categories; isolated read-only job."""
        return tools.profile_dataset(path,options.model_dump(mode='json') if options else None)

    @server.tool()
    def workflow_report(run_id:str)->dict:
        """Read analytical/technical handoff from recorded workflow evidence; no source scan, model call or execution."""
        return tools.workflow_report(run_id)

    @server.tool()
    def list_operation_contracts(query:str='')->dict:
        """Search registered operations, typed arguments/results, source readers, effects and requirements. Discovery grants no execution authority."""
        return tools.list_operation_contracts(query)

    @server.tool()
    def profile_table(path: str, options: AnalysisOptions | None = None) -> dict:
        """Full-file CSV/TSV/XLSX/flat JSON/JSONL profiles, quality/duplicate checks and grouped distinct counts; optional codebook, no dataset writes."""
        return tools.profile_table(path, options.model_dump(mode="json") if options is not None else None)

    @server.tool()
    def table_statistics(path:str,specification:StatisticsSpec,missing_values:dict[str,list[str]]|None=None,source_options:TableSourceOptions|None=None)->dict:
        """Describe numeric fields, Pearson/Spearman/covariance matrices or OLS coefficients/P-values/R-squared. Read-only; explicit variables and missing policy."""
        return tools.table_statistics(path,specification.model_dump(mode='json'),missing_values,source_options=source_options.model_dump(mode='json') if source_options else None)

    @server.tool()
    def recommend_table_fields(path:str,source_options:TableSourceOptions|None=None)->dict:
        """Inspect a full supported table source and suggest measurement/grouping/identifier candidates with evidence and cautions. Advisory, no statistics execution or write authority."""
        return tools.recommend_table_fields(path,source_options=source_options.model_dump(mode='json') if source_options else None)

    @server.tool()
    def linear_regression(path:str,specification:RegressionSpec,source_options:TableSourceOptions|None=None,missing_policy:Literal['error','complete_cases']='error',missing_values:dict[str,list[str]]|None=None)->dict:
        """Numeric OLS with coefficients, standard errors, P-values, confidence intervals, R-squared and diagnostics; optional HC3/cluster covariance. Not causal inference."""
        return tools.table_statistics(path,{'methods':['linear_regression'],'regression':specification.model_dump(mode='json'),'missing_policy':missing_policy},missing_values,source_options=source_options.model_dump(mode='json') if source_options else None)

    @server.tool()
    def discover_dataset(path:str,delimiter:str|None=None)->dict:
        """Read bounded local dataset characteristics and hash; never writes data."""
        return tools.discover_dataset(path,delimiter)

    @server.tool()
    def inspect_vector_dataset(
        path: str,
    ) -> dict:
        """Inspect an approved vector input dataset."""

        return tools.inspect_vector_dataset(
            path
        ).model_dump(mode="json")

    @server.tool()
    def inspect_postgis_table(
        target_schema: str,
        target_table: str,
    ) -> dict:
        """Inspect bounded metadata for one approved PostGIS table."""
        return tools.inspect_postgis_table(
            target_schema=target_schema,
            target_table=target_table,
        ).model_dump(mode="json")

    @server.tool()
    def inspect_geoserver_layer(
        workspace: str,
        datastore: str,
        layer: str,
    ) -> dict:
        """Inspect one approved GeoServer publication target read-only."""
        return tools.inspect_geoserver_layer(
            workspace=workspace, datastore=datastore, layer=layer,
        ).model_dump(mode="json")

    @server.tool()
    def plan_geoserver_publication(
        plan_id: str, workspace: str, datastore: str, layer: str,
    ) -> dict:
        """Plan, but do not execute, one exact GeoServer publication."""
        return tools.plan_geoserver_publication(
            plan_id=plan_id, workspace=workspace, datastore=datastore, layer=layer,
        ).model_dump(mode="json")

    @server.tool()
    def compare_postgis_tables(
        reference_schema: str,
        reference_table: str,
        candidate_schema: str,
        candidate_table: str,
    ) -> dict:
        """Compare two approved PostGIS relations without mutation."""
        return tools.compare_postgis_tables(
            reference_schema=reference_schema,
            reference_table=reference_table,
            candidate_schema=candidate_schema,
            candidate_table=candidate_table,
        ).model_dump(mode="json")

    @server.tool()
    def assess_postgis_change(
        reference_schema: str,
        reference_table: str,
        candidate_schema: str,
        candidate_table: str,
    ) -> dict:
        """Classify deterministic PostGIS comparison evidence."""
        return tools.assess_postgis_change(
            reference_schema=reference_schema,
            reference_table=reference_table,
            candidate_schema=candidate_schema,
            candidate_table=candidate_table,
        ).model_dump(mode="json")

    @server.tool()
    def plan_postgis_promotion(
        plan_id: str,
        reference_schema: str,
        reference_table: str,
        candidate_schema: str,
        candidate_table: str,
        archive_schema: str,
        archive_table: str,
    ) -> dict:
        """Plan an exact approved PostGIS relation promotion."""
        return tools.plan_postgis_promotion(
            plan_id=plan_id,
            reference_schema=reference_schema,
            reference_table=reference_table,
            candidate_schema=candidate_schema,
            candidate_table=candidate_table,
            archive_schema=archive_schema,
            archive_table=archive_table,
        ).model_dump(mode="json")


    @server.tool()
    def assess_spatial_data_contract(
        path: str,
        contract_file: str,
    ) -> dict:
        """Assess an approved vector input against a contract."""

        return tools.assess_spatial_data_contract(
            path=path,
            contract_file=contract_file,
        ).model_dump(mode="json")

    @server.tool()
    def plan_load_vector_to_postgis(
        path: str,
        target_schema: str,
        target_table: str,
    ) -> dict:
        """Create a non-executing PostGIS load plan."""

        return tools.plan_load_vector_to_postgis(
            path=path,
            target_schema=target_schema,
            target_table=target_table,
        ).model_dump(mode="json")

    @server.tool(
        name="run_approved_vector_postgis_workflow"
    )
    def run_approved_vector_postgis_workflow_tool(
        execution_envelope: dict[str, Any],
        plan_filename: str,
        approval_filename: str,
    ) -> dict:
        """Run only an exact server-verified approved workflow."""

        return run_approved_vector_postgis_workflow(
            execution_envelope=execution_envelope,
            plan_filename=plan_filename,
            approval_filename=approval_filename,
        ).model_dump(mode="json")

    @server.tool()
    def validate_postgis_layer(
        target_schema: str,
        target_table: str,
        expected_row_count: int | None = None,
        expected_srid: int | None = None,
        expected_geometry_type: str | None = None,
    ) -> dict:
        """Deterministically validate one PostGIS layer."""

        return tools.validate_postgis_layer(
            target_schema=target_schema,
            target_table=target_table,
            expected_row_count=expected_row_count,
            expected_srid=expected_srid,
            expected_geometry_type=(
                expected_geometry_type
            ),
        ).model_dump(mode="json")
    
    @server.tool(
        name="run_approved_recipe"
    )
    def run_approved_recipe_tool(
        execution_envelope: dict[str, Any],
        recipe_filename: str,
        approval_filename: str,
    ) -> dict:
        """Run one exact server-verified approved recipe."""

        return run_approved_recipe(
            execution_envelope=execution_envelope,
            recipe_filename=recipe_filename,
            approval_filename=approval_filename,
        ).model_dump(mode="json")

    return server


# Used by existing in-process and STDIO tests.
mcp = create_mcp_server()


def main() -> None:
    """Run the configured MCP transport."""

    settings = load_transport_settings()
    server = create_mcp_server(settings)
    server.run(transport=settings.transport)


if __name__ == "__main__":
    main()
