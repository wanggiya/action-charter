"""Keep repository-based legacy fixtures independent of an operator's API session."""
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def isolate_repository_action_audit(tmp_path_factory):
    """Default-root CLI fixtures must never append to the operator's action ledger."""
    from dataclasses import replace
    from geoagent_harness.platform.execution_services import execution_services, using_execution_services
    from geoagent_harness.platform.storage.action_ledger import LocalActionLedger
    repository = Path(__file__).resolve().parents[1]
    isolated = tmp_path_factory.mktemp('repository-action-audit')
    original = execution_services()
    def ledger(root, *, namespace='local'):
        return LocalActionLedger(isolated if Path(root).resolve() == repository else root,namespace=namespace)
    with using_execution_services(replace(original, ledger=ledger)):
        yield


@pytest.fixture(autouse=True)
def isolate_repository_write_policy(tmp_path, monkeypatch):
    from geoagent_harness.core.policy import write_policy
    repository = Path(__file__).resolve().parents[1]
    original_paths = write_policy._paths
    original_owner_fd = write_policy._owner_fd
    original_project_owner = write_policy._project_owner
    isolated = tmp_path / 'repository-policy-fixture'
    # Many older fixtures read the real registry but write only to tmp_path.
    # Their default project_root must never read/bind to the operator's live ledger.
    # Explicit temporary project sessions remain real, including subprocess tests.
    def paths(root, create=False):
        root = Path(root)
        if create and root.resolve() == repository:
            isolated.mkdir(mode=0o700,parents=True,exist_ok=True)
        return original_paths(isolated if root.resolve() == repository else root, create=create)
    monkeypatch.setattr(write_policy, '_paths', paths)
    # The independent project lease must use the same fixture identity as its
    # redirected database. Never probe the operator's real project ownership.
    def owner_fd(root, *, create=False, scope=None):
        root = Path(root)
        redirected = root.resolve() == repository
        return original_owner_fd(isolated if redirected else root,create=create,
                                 scope=None if redirected else scope)
    def project_owner(root):
        root = Path(root)
        if root.resolve() == repository:
            isolated.mkdir(mode=0o700,parents=True,exist_ok=True)
            root=isolated
        return original_project_owner(root)
    monkeypatch.setattr(write_policy,'_owner_fd',owner_fd)
    monkeypatch.setattr(write_policy,'_project_owner',project_owner)
