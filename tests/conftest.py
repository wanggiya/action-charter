"""Keep repository-based legacy fixtures independent of an operator's API session."""
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def isolate_repository_write_policy(tmp_path, monkeypatch):
    from geoagent_harness import write_policy
    repository = Path(__file__).resolve().parents[1]
    original_paths = write_policy._paths
    isolated = tmp_path / 'repository-policy-fixture'
    # Many older fixtures read the real registry but write only to tmp_path.
    # Their default project_root must never read/bind to the operator's live ledger.
    # Explicit temporary project sessions remain real, including subprocess tests.
    def paths(root, create=False):
        root = Path(root)
        return original_paths(isolated if root.resolve() == repository else root, create=create)
    monkeypatch.setattr(write_policy, '_paths', paths)
