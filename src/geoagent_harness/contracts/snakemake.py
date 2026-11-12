"""Closed Snakemake graph arguments; no export or authority implementation."""
from pydantic import BaseModel, ConfigDict, Field

EXPORT = 'export_snakemake_workflow'
VERIFY = 'verify_snakemake_export'
TERMINAL = {EXPORT, VERIFY}


class ExportArguments(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_plan_filename: str = Field(pattern=r'^planner-plan\.[a-f0-9]{64}\.json$')
    source_plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')

class VerifyArguments(BaseModel):
    model_config = ConfigDict(extra='forbid')
