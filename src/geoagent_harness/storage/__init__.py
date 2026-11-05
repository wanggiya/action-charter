"""Workspace repositories. Storage never confers execution authority."""
from .contracts import RepositoryError
from .provider import repositories, using_repository_provider

__all__ = ['RepositoryError', 'repositories', 'using_repository_provider']
