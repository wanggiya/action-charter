"""Completed run snapshots for retrieval; never repair, retry, assess or execute."""
import re
from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.platform.project import _trusted_root
from geoagent_harness.platform.paths import runtime_store_path
from geoagent_harness.platform.storage import repositories
from geoagent_harness.platform.storage import RepositoryError


def read_completed_run(root, identity):
    root = _trusted_root(root)
    if not isinstance(identity, str) or re.fullmatch(r'[a-f0-9]{32}', identity) is None:
        raise InterfaceApiError('Choose a workflow run')
    directory = runtime_store_path(root, 'workflow-state', 'interface-runs')
    if directory.is_symlink() or directory.parent.is_symlink():
        raise InterfaceApiError('Workflow run storage is unsafe')
    path = directory / (identity + '.json')
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 512_000:
        raise InterfaceApiError('Workflow run is unavailable or unsafe')
    try:
        record = repositories(root).runs().read(identity + '.json')
    except RepositoryError as error:
        raise InterfaceApiError(str(error)) from error
    if record.get('run_id') != identity:
        raise InterfaceApiError('Workflow run identity does not match')
    if record['status'] != 'completed':
        raise InterfaceApiError('Select a completed workflow run')
    return record
