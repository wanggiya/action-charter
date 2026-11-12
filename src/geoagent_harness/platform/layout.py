"""One immutable layout; legacy environment names are compatibility inputs only."""
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# Fields retain the public tool/replay setting names and their historical defaults.
ROOT_ENVIRONMENT = {
    'input_root': ('GEOAGENT_INPUT_ROOT', 'data/input'),
    'output_root': ('GEOAGENT_OUTPUT_ROOT', 'data/output'),
    'contract_root': ('GEOAGENT_SPATIAL_CONTRACT_ROOT', 'spatial-contracts'),
    'trace_root': ('GEOAGENT_TRACE_ROOT', 'traces'),
    'report_root': ('GEOAGENT_REPORT_ROOT', 'reports'),
    'plan_root': ('GEOAGENT_PLAN_ROOT', 'plans'),
    'approval_root': ('GEOAGENT_APPROVAL_ROOT', 'approvals'),
    'state_root': ('GEOAGENT_STATE_ROOT', 'workflow-state'),
    'project_root': ('GEOAGENT_PROJECT_ROOT', '.'),
    'recipe_root': ('GEOAGENT_RECIPE_ROOT', 'workflow-recipes'),
    'recipe_run_root': ('GEOAGENT_RECIPE_RUN_ROOT', 'recipe-runs'),
    'recipe_evidence_root': ('GEOAGENT_RECIPE_EVIDENCE_ROOT', 'recipe-evidence'),
    'agents_root': ('GEOAGENT_AGENTS_ROOT', 'agents'),
    'export_root': ('GEOAGENT_SNAKEMAKE_EXPORT_ROOT', 'snakemake-exports'),
}
RUNTIME_DEFAULTS = {
    key: default for key, (_, default) in ROOT_ENVIRONMENT.items()
    if key not in {'input_root', 'output_root', 'project_root', 'agents_root'}
}


@dataclass(frozen=True)
class LayoutConfiguration:
    input_root: Path = Path('data/input')
    output_root: Path = Path('data/output')
    contract_root: Path = Path('spatial-contracts')
    trace_root: Path = Path('traces')
    report_root: Path = Path('reports')
    plan_root: Path = Path('plans')
    approval_root: Path = Path('approvals')
    state_root: Path = Path('workflow-state')
    project_root: Path = Path('.')
    recipe_root: Path = Path('workflow-recipes')
    recipe_run_root: Path = Path('recipe-runs')
    recipe_evidence_root: Path = Path('recipe-evidence')
    agents_root: Path = Path('agents')
    export_root: Path = Path('snakemake-exports')

    @classmethod
    def from_environment(cls, values: Mapping[str, str]) -> 'LayoutConfiguration':
        return cls(**{field: Path(values.get(name, default))
                      for field, (name, default) in ROOT_ENVIRONMENT.items()})

    def workspace(self):
        """Explicitly resolve existing workspace ownership; never create/migrate it."""
        from geoagent_harness.platform.workspace import WorkspaceLayout
        return WorkspaceLayout.load(self.project_root)
