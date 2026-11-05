"""Keep repository-based legacy fixtures independent of an operator's API session."""
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def isolate_repository_write_policy(tmp_path, monkeypatch):
    from geoagent_harness import write_policy
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
    def owner_fd(root, *, create=False):
        root = Path(root)
        return original_owner_fd(isolated if root.resolve() == repository else root,create=create)
    def project_owner(root):
        root = Path(root)
        if root.resolve() == repository:
            isolated.mkdir(mode=0o700,parents=True,exist_ok=True)
            root=isolated
        return original_project_owner(root)
    monkeypatch.setattr(write_policy,'_owner_fd',owner_fd)
    monkeypatch.setattr(write_policy,'_project_owner',project_owner)
