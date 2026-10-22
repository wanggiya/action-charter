"""Shared, descriptive contracts. Legacy skill bytes and IDs are unchanged."""
from __future__ import annotations
from importlib import metadata
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from .packages import installed_packages, package_sha, ProjectionArguments, configuration
from geoagent_harness.tabular.schemas import ARGUMENTS as TABLE_ARGUMENTS, LABELS

NAMES = {
 'inspect_vector':'Inspect vector dataset','inspect_raster':'Inspect raster dataset',
 'convert_vector':'Convert vector format','convert_raster':'Convert raster format',
 'load_vector_to_postgis':'Load vector into PostGIS','validate_postgis_layer':'Validate PostGIS layer',
 'generate_report':'Create workflow report','export_snakemake_workflow':'Export to Snakemake',
 'verify_snakemake_export':'Verify Snakemake package','inspect_postgis_table':'Inspect PostGIS table',
 'compare_postgis_tables':'Compare PostGIS tables','assess_spatial_data_contract':'Check spatial data requirements',
 'inspect_geoserver_layer':'Inspect GeoServer layer','plan_geoserver_publication':'Plan GeoServer publication',
 'assess_postgis_change':'Assess PostGIS changes','plan_postgis_promotion':'Plan PostGIS promotion', **LABELS,
}

class Artifact(BaseModel):
    model_config=ConfigDict(extra='forbid')
    path:str
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')

class TableSource(BaseModel):
    model_config=ConfigDict(extra='forbid')
    path:str=Field(max_length=960)
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    area:Literal['input','output']
    source_step:str|None=None

class TableMetadata(BaseModel):
    model_config=ConfigDict(extra='allow')
    row_count:int=Field(ge=0,le=1024**3)
    column_count:int=Field(ge=1,le=100)
    columns:list[str]=Field(min_length=1,max_length=100)
    preview:list[dict[str,str|None]]=Field(max_length=20)
    missing_counts:dict[str,int]
    column_types:dict[str,Literal['string']]
    preview_truncated:bool

class TableArtifact(TableMetadata):
    # Processing bounds do not grow with metadata-only inspection capability.
    row_count:int=Field(ge=0,le=10000)
    data_contract:Literal['table/csv-v1']
    output:Artifact
    sources:list[TableSource]


def builtin_argument_models():
    from geoagent_harness.recipes import schemas
    from geoagent_harness.interface_api.snakemake_workflow import ExportArguments, VerifyArguments
    return {
      'inspect_vector':schemas.InspectVectorRecipeArguments,'inspect_raster':schemas.InspectRasterRecipeArguments,
      'convert_vector':schemas.ConvertVectorRecipeArguments,'convert_raster':schemas.ConvertRasterRecipeArguments,
      'load_vector_to_postgis':schemas.LoadVectorToPostGISRecipeArguments,'validate_postgis_layer':schemas.ValidatePostGISLayerRecipeArguments,
      'generate_report':schemas.GenerateReportRecipeArguments,'export_snakemake_workflow':ExportArguments,
      'verify_snakemake_export':VerifyArguments,**TABLE_ARGUMENTS,
    }

def argument_models(root=Path('.')):
    return {**builtin_argument_models(),**{id:ProjectionArguments for id in installed_packages(root)}}

def _legacy_models():
    from geoagent_harness.postgis_inspection.schemas import PostGISInspectionRequest, PostGISInspectionResult
    from geoagent_harness.postgis_comparison.schemas import PostGISComparisonRequest, PostGISComparisonResult
    from geoagent_harness.geoserver_inspection.schemas import GeoServerInspectionRequest, GeoServerInspectionResult
    from geoagent_harness.geoserver_publication.schemas import GeoServerPublicationPlanRequest, GeoServerPublicationPlanResult
    from geoagent_harness.postgis_promotion_plan.schemas import PostGISPromotionPlanRequest, PostGISPromotionPlanResult
    from geoagent_harness.spatial_contracts.schemas import VectorSpatialDataContract, SpatialDataContractAssessment
    from geoagent_harness.postgis_change_assessment.schemas import PostGISChangeAssessment
    class SpatialAssessmentInput(BaseModel):
        model_config=ConfigDict(extra='forbid')
        path:str=Field(max_length=960)
        contract:VectorSpatialDataContract
    return {
      'inspect_postgis_table':(PostGISInspectionRequest,PostGISInspectionResult),
      'compare_postgis_tables':(PostGISComparisonRequest,PostGISComparisonResult),
      'inspect_geoserver_layer':(GeoServerInspectionRequest,GeoServerInspectionResult),
      'plan_geoserver_publication':(GeoServerPublicationPlanRequest,GeoServerPublicationPlanResult),
      'plan_postgis_promotion':(PostGISPromotionPlanRequest,PostGISPromotionPlanResult),
      'assess_spatial_data_contract':(SpatialAssessmentInput,SpatialDataContractAssessment),
      'assess_postgis_change':(PostGISComparisonResult,PostGISChangeAssessment),
    }

def _result_schema(id):
    if id=='inspect_csv':return TableMetadata.model_json_schema()
    if id in TABLE_ARGUMENTS or id.startswith('ext_'):return TableArtifact.model_json_schema()
    from geoagent_harness.schemas import InspectVectorResult
    if id=='inspect_vector':
        from pydantic import TypeAdapter
        from geoagent_harness.discovery.spatial_contracts import VectorMetadata
        return TypeAdapter(InspectVectorResult|VectorMetadata).json_schema()
    if id=='inspect_raster':
        from geoagent_harness.skill_adapters.raster_inspection import RasterInspectionResult
        from pydantic import TypeAdapter
        from geoagent_harness.discovery.spatial_contracts import RasterMetadata
        return TypeAdapter(RasterInspectionResult|RasterMetadata).json_schema()
    if id=='convert_vector':
        from geoagent_harness.skills.convert_vector.schemas import ConvertVectorResult
        return ConvertVectorResult.model_json_schema()
    if id=='convert_raster':
        from geoagent_harness.skill_adapters.raster_conversion import RasterConversionResult
        return RasterConversionResult.model_json_schema()
    if id=='load_vector_to_postgis':
        from geoagent_harness.skills.load_vector_to_postgis.service import LoadVectorResult
        return LoadVectorResult.model_json_schema()
    if id=='validate_postgis_layer':
        from geoagent_harness.verifier.postgis import PostGISValidationResult
        return PostGISValidationResult.model_json_schema()
    if id=='export_snakemake_workflow':
        from geoagent_harness.snakemake_export.schemas import SnakemakeRecipeExportResult
        return SnakemakeRecipeExportResult.model_json_schema()
    if id=='verify_snakemake_export':
        return {'type':'object','required':['passed','export_path','workflow_executed'],'properties':{'passed':{'const':True},'export_path':{'type':'string'},'workflow_executed':{'const':False}}}
    return {'type':'object','required':['status','task_id','report_written'],'properties':{'status':{'const':'report_pending_evidence_persistence'},'task_id':{'type':'string'},'report_written':{'const':False}},'description':'Authoritative report is produced through durable recipe evidence persistence.'}

def operation_catalog(root, query=''):
    from geoagent_harness.skill_registry import load_skill_registry
    models=argument_models(root);packages=installed_packages(root)
    try:legacy=_legacy_models()
    except ImportError:legacy={}
    result=[]
    for skill in load_skill_registry(root).implemented_skills():
        id=skill.id;package=packages.get(id);model=models.get(id)
        parameters=model.model_json_schema() if model else legacy[id][0].model_json_schema() if id in legacy else {'type':'object'}
        table=id in TABLE_ARGUMENTS or package is not None
        output_kind='csv_artifact' if (table and id!='inspect_csv') else 'inspection_metadata' if id.startswith('inspect_') else 'database_layer' if id=='load_vector_to_postgis' else 'vector_artifact' if id=='convert_vector' else 'raster_artifact' if id=='convert_raster' else 'evidence' if 'snakemake' in id or id=='generate_report' else 'policy_result'
        runtime_names=['pandas'] if table else ['psycopg'] if 'postgis' in id else ['geopandas','pyogrio'] if 'vector' in id or id=='assess_spatial_data_contract' else ['rasterio'] if 'raster' in id else ['httpx'] if 'geoserver' in id else []
        requirements=[]
        for name in runtime_names:
            try:version=metadata.version(name)
            except metadata.PackageNotFoundError:version=None
            requirement={'pandas':'==3.0.5','psycopg':'>=3.2,<4','geopandas':'>=1.0,<2','pyogrio':'>=0.9,<1','rasterio':'>=1.4,<2','httpx':'>=0.27,<1'}[name]
            requirements.append({'distribution':name,'requirement':requirement,'installed_version':version,'available':version is not None})
        try:
            schema=legacy[id][1].model_json_schema() if id in legacy else _result_schema(id)
            schema_available=model is not None or id in legacy
            if not schema_available:schema={'type':'object','description':'Trusted service result schema is unavailable without its optional runtime'}
        except ImportError:
            schema={'type':'object','description':'Install the declared optional runtime to expose this trusted result schema'}
            schema_available=False
        defaults={}
        if package:defaults={'path':'','target_path':'','package_sha256':package_sha(package)}
        result.append({'id':id,'name':package.name if package else NAMES.get(id,id.replace('_',' ').capitalize()),'version':skill.version,'kind':skill.kind.value,
          'workflow_supported':model is not None,'result_schema_available':schema_available,'parameters_schema':parameters,'output_schema':schema,
          'parameter_mode':'workflow_arguments' if model else 'existing_service_contract',
          'inputs':[{'parameter':key,'contract':('geojson_file' if id=='vector_attributes_to_csv' else 'csv_file' if table else 'vector_file' if 'vector' in id else 'raster_file' if 'raster' in id else 'original_input_file') if key.endswith('path') else 'validated_ancestor_csv_artifact'} for key in parameters.get('properties',{}) if key in {'path','right_path','source_step','right_step'}] or [{'parameter':'arguments','contract':'typed_structured_service_input' if model is None else 'typed_operation_input'}],
          'outputs':[{'contract':output_kind,'parameter':'target_path' if output_kind.endswith('artifact') else None}],
          'dependencies':['inspect_vector','validate_postgis_layer'] if id=='load_vector_to_postgis' else ['inspect_vector'] if id=='vector_attributes_to_csv' else ['verify_snakemake_export'] if id=='export_snakemake_workflow' else [],
          'runtime_requirements':requirements,'effects':{'access':skill.access.value,'reads':'explicit declared inputs/evidence','writes':'explicit declared targets' if skill.access.value!='read_only' else 'none'},
          'approval_required':bool(skill.approval_required) or id=='generate_report','validation_required':bool(skill.validation_required) or id=='verify_snakemake_export',
          'validation_contract':{'verifier':skill.verifier,'read_only_checks':'typed adapter/runtime policy','result_preview':'bounded metadata and evidence; CSV rows limited to 20/4KB'},
          'adapter_configuration':configuration(package) if package else None,
          'package_sha256':package_sha(package) if package else None,'default_arguments':defaults,'origin':'installed_adapter' if package else 'builtin'})
    query=query.strip().lower()
    return {'schema_version':'1.0','operations':[item for item in result if query in (item['id']+' '+item['name']).lower()],'operation_count':len(result),'approval_performed':False,'execution_performed':False}


def planning_dependencies(selected, root=Path('.')):
    """Include declared prerequisite/verification operations, never new authority."""
    models = argument_models(root)
    dependencies = {operation['id']: operation['dependencies'] for operation in operation_catalog(root)['operations']}
    result = list(dict.fromkeys(selected))
    for operation in result:
        for required in dependencies.get(operation, []):
            if required not in models:
                raise ValueError('Required planning operation dependency is unavailable: ' + required)
            if required not in result:
                result.append(required)
    return result
