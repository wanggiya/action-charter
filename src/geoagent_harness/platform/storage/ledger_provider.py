"""Trusted specialized ledger composition, scoped across existing worker contexts."""
from contextlib import contextmanager
from contextvars import ContextVar

from geoagent_harness.platform.storage.ledger_files import LocalImmutableRecords, LocalAttemptLedger
from geoagent_harness.platform.storage.ledger_sqlite import write_policy, SQLiteSuccessfulMethods
from geoagent_harness.platform.storage.ledger_contracts import LedgerRepositories


class LocalLedgerRepositories:
    def immutable(self, directory): return LocalImmutableRecords(directory)
    def attempts(self, directory): return LocalAttemptLedger(directory)
    def write_policy(self, database): return write_policy(database)
    def successes(self, project_root): return SQLiteSuccessfulMethods(project_root)


_provider: ContextVar[LedgerRepositories] = ContextVar('specialized_ledger_provider', default=LocalLedgerRepositories())


def ledger_repositories() -> LedgerRepositories:
    return _provider.get()


@contextmanager
def using_ledger_provider(provider: LedgerRepositories):
    """First-party composition/test hook, never selected by model or request text."""
    token = _provider.set(provider)
    try: yield
    finally: _provider.reset(token)
