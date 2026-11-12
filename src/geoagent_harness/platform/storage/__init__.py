"""Workspace repositories. Storage never confers execution authority."""
from geoagent_harness.platform.storage.contracts import RepositoryError
from geoagent_harness.platform.storage.provider import repositories, using_repository_provider

__all__ = ['RepositoryError', 'repositories', 'using_repository_provider']
