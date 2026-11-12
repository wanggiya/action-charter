"""Project-bound runtime locations. Resolving a location never creates or moves data."""
from dataclasses import dataclass
import json
from pathlib import Path

CONFIG_NAME = 'actioncharter.workspace.json'
OWNER_NAME = '.actioncharter-owner.json'
RUNTIME_FILES = frozenset({'approved-recipes.local.json'})
LIFECYCLE_STORES = frozenset({
    'reviewed-contexts', 'reviewed-intents', 'snakemake-exports',
    'builder-requests', 'builder-generations', 'builder-candidates', 'builder-test-results',
    'builder-reviews', 'builder-decisions', 'builder-promotion-plans', 'builder-promotions',
    'builder-promotion-verifications', 'builder-activation-decisions', 'builder-activation-plans',
    'builder-activations', 'builder-post-activation-verifications',
    'skill-contracts', 'skill-definitions', 'skill-scaffolds', 'skill-candidates', 'skill-test-results',
    'recipe-proposals', 'recipe-proposals.local', 'recipe-reviews',
    'postgis-promotion-plans', 'postgis-promotion-approvals', 'postgis-promotion-executions',
    'postgis-promotion-verifications', 'postgis-rollback-plans', 'postgis-rollback-approvals',
    'postgis-rollback-executions', 'postgis-rollback-verifications',
    'geoserver-publication-evidence', '.local',
})
# State stores only. Source, input data, output data and secrets are not state stores.
RUNTIME_STORES = frozenset({
    'planner-workspace', 'planner-conversations', 'plans', 'approvals',
    'workflow-state', 'workflow-recipes', 'recipe-runs', 'recipe-evidence',
    'inspection-runs', 'traces', 'reports', 'spatial-contracts', 'task-history',
    'critic-results', 'releases', 'operational-history',
    'library-discovery', 'operation-packages', 'reusable-recipes',
}) | LIFECYCLE_STORES
ADOPTED_ARTIFACT_STORES = frozenset({
    'plans', 'approvals', 'workflow-recipes', 'recipe-runs', 'recipe-evidence', 'inspection-runs', 'task-history',
    'traces', 'reports', 'critic-results', 'releases', 'operational-history',
    'library-discovery', 'operation-packages', 'reusable-recipes',
}) | LIFECYCLE_STORES | {'spatial-contracts'}


class WorkspaceError(ValueError):
    """Invalid workspace configuration or an incomplete explicit migration."""


def _no_links(path: Path) -> None:
    for item in (path, *path.parents):
        if item.is_symlink():
            raise WorkspaceError('Workspace storage is unsafe: symlink/symbolic links are not allowed')


@dataclass(frozen=True)
class WorkspaceLayout:
    project_root: Path
    state_root: Path

    @classmethod
    def load(cls, project_root: Path):
        project = Path(project_root).resolve(strict=True)
        config = project / CONFIG_NAME
        if config.is_symlink():
            raise WorkspaceError('Workspace configuration must not be a symbolic link')
        if not config.exists():
            from geoagent_harness.platform.project_identity import resolve_identity, ProjectIdentityError
            try: resolve_identity(project, project)
            except ProjectIdentityError as error: raise WorkspaceError(str(error)) from error
            return cls(project, project)
        if not config.is_file() or config.stat().st_size > 4096 or config.stat().st_nlink != 1:
            raise WorkspaceError('Workspace configuration exceeds its file contract')
        try:
            value = json.loads(config.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError) as error:
            raise WorkspaceError('Workspace configuration is not valid JSON') from error
        if (not isinstance(value, dict) or set(value) != {'version', 'state_root'}
                or type(value['version']) is not int or value['version'] != 1
                or not isinstance(value['state_root'], str) or not value['state_root'].strip() or '\x00' in value['state_root']):
            raise WorkspaceError('Workspace configuration requires version=1 and a nonempty state_root')
        configured = Path(value['state_root'])
        if '..' in configured.parts:
            raise WorkspaceError('Workspace state_root must not contain parent traversal')
        target = configured if configured.is_absolute() else project / configured
        _no_links(target)
        target = target.resolve()
        if target != project:
            # Relocating state over source/data/secrets would mix trust boundaries.
            if target in project.parents:
                raise WorkspaceError('Workspace state_root must not contain the project')
            if target.is_relative_to(project) and target.relative_to(project).parts[0] in ({
                'src', 'interface', 'agents', 'skills', 'context', 'docs', 'scripts',
                'tests', 'data', '.git', '.secrets', '.venv', 'examples', 'docker',
            } | RUNTIME_STORES | RUNTIME_FILES):
                raise WorkspaceError('Workspace state_root overlaps source, data, secrets or a runtime store')
        if target.exists() and not target.is_dir():
            raise WorkspaceError('Workspace state_root must be a directory')
        from geoagent_harness.platform.project_identity import resolve_identity, ProjectIdentityError, owner_record
        try: identity = resolve_identity(project, target)
        except ProjectIdentityError as error: raise WorkspaceError(str(error)) from error
        owner = target / OWNER_NAME
        if identity and target != project and not owner.exists():
            raise WorkspaceError('Stable workspace ownership record is missing; inspect the offline transition')
        if target != project and (owner.exists() or owner.is_symlink()):
            _no_links(owner)
            if not owner.is_file() or owner.stat().st_size > 4096 or owner.stat().st_nlink != 1:
                raise WorkspaceError('Workspace ownership record is unsafe')
            try: binding = json.loads(owner.read_text())
            except (ValueError, UnicodeError) as error:
                raise WorkspaceError('Workspace ownership record is invalid') from error
            expected = owner_record(project, target)
            if binding != expected:
                raise WorkspaceError('Workspace belongs to another source project')
        return cls(project, target)

    def runtime_path(self, store: str) -> Path:
        if store not in RUNTIME_STORES:
            raise WorkspaceError('Unknown runtime state store')
        path = self.state_root / store
        _no_links(path)
        return path

    def planning_directory(self) -> Path:
        destination = self.runtime_path('planner-workspace')
        legacy = self.project_root / 'planner-workspace' / 'tasks.sqlite3'
        if self.state_root != self.project_root and legacy.exists() and not (destination / 'tasks.sqlite3').exists():
            raise WorkspaceError('Planning state has not been migrated to the configured workspace; '
                                 'preserve the legacy database and complete an offline verified copy before switching')
        return destination


def runtime_store_path(project_root: Path, store: str, *parts: str) -> Path:
    """Resolve an adopted store, refusing a missing destination with legacy records.

    No copying/merging or directory creation is performed. Adoption is per store;
    unconverted services retain their explicit legacy roots until migrated together.
    """
    layout = WorkspaceLayout.load(project_root)
    for part in parts:
        if not part or Path(part).is_absolute() or len(Path(part).parts) != 1 or part in {'.','..'}:
            raise WorkspaceError('Unsafe runtime store suffix')
    destination = layout.runtime_path(store).joinpath(*parts)
    _no_links(destination)
    legacy = layout.project_root.joinpath(store, *parts)
    if layout.state_root != layout.project_root:
        _no_links(legacy)
        if legacy.is_dir() and any(p.name != '.gitkeep' for p in legacy.iterdir()):
            if not destination.is_dir() or not any(p.name != '.gitkeep' for p in destination.iterdir()):
                raise WorkspaceError(f'Workspace migration required for {store}; legacy records are preserved, not hidden or moved')
    return destination


def ensure_state_root(project_root: Path) -> None:
    """Writer-only helper: create the configured root privately, leaving reads pure."""
    layout = WorkspaceLayout.load(project_root)
    layout.state_root.mkdir(mode=0o700, parents=True, exist_ok=True)


def runtime_reference(project_root: Path, path: Path) -> str:
    """Keep logical artifact references stable when physical state is relocated.

    Custom project-local paths retain their old spelling. Paths outside both the
    configured state and project remain invalid; resolving never creates storage.
    """
    layout = WorkspaceLayout.load(project_root)
    _no_links(path)
    resolved = path.resolve()
    if layout.state_root != layout.project_root and resolved.is_relative_to(layout.state_root):
        relative = resolved.relative_to(layout.state_root)
        if (len(relative.parts) < 2 or (relative.parts[0] not in ADOPTED_ARTIFACT_STORES
                and relative.parts[:2] not in {('workflow-state','interface-runs'),('workflow-state','interface-executions')})):
            raise WorkspaceError('Artifact is outside adopted runtime stores')
        return relative.as_posix()
    try:
        return resolved.relative_to(layout.project_root).as_posix()
    except ValueError as error:
        raise WorkspaceError('Artifact is outside the project and configured workspace') from error


def runtime_reference_path(project_root: Path, reference: str) -> Path:
    """Resolve a logical reference, keeping unadopted stores project-relative."""
    path = Path(reference)
    if (path.is_absolute() or len(path.parts)<2 or path.as_posix()!=reference
            or '..' in path.parts or '\\' in reference or any(ord(c)<32 for c in reference)):
        raise WorkspaceError('Unsafe runtime artifact reference')
    if path.parts[0] in ADOPTED_ARTIFACT_STORES:
        destination=runtime_store_path(project_root,path.parts[0]).joinpath(*path.parts[1:])
    elif path.parts[:2] in {('workflow-state','interface-runs'),('workflow-state','interface-executions')}:
        destination=runtime_store_path(project_root,*path.parts[:2]).joinpath(*path.parts[2:])
    else:
        destination=WorkspaceLayout.load(project_root).project_root / path
    _no_links(destination)
    return destination
