"""Shared metadata transactions and bounded planning-record mechanics, without roles."""
from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
import json
from pathlib import Path
import re
from typing import Literal

from geoagent_harness.contracts.errors import TaskActionError
from geoagent_harness.platform.storage.contracts import RepositoryError
from geoagent_harness.platform.storage.provider import repositories
from geoagent_harness.platform.storage.sqlite import connection as sqlite_connection, adapt_legacy

MAX_RECORD_BYTES = 2_000_000
MAX_RECORDS = 128
MAX_DATABASE_BYTES = 64_000_000
IDENTITY = re.compile(r'^[a-f0-9]{32}$')
PlanningCollection = Literal['conversations', 'tasks', 'memories']


def validate_identity(value):
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        raise TaskActionError('Invalid planning task identity')
    return value


@contextmanager
def raw_database(root: Path, *, write=False):
    """Compatibility connection API; native clients use the repository transaction."""
    try:
        with sqlite_connection(root, write=write) as connection:
            yield connection
    except RepositoryError as error:
        raise TaskActionError(str(error)) from error


@contextmanager
def transaction(root: Path, *, write=False):
    try:
        with repositories(root).transaction(write=write) as unit:
            yield unit
    except RepositoryError as error:
        raise TaskActionError(str(error)) from error


def read_record(connection, table: PlanningCollection, identity: str) -> dict | None:
    """Read bounded JSON identity; role/provenance/schema rules stay in task actions."""
    validate_identity(identity)
    if connection is None:
        return None
    raw = adapt_legacy(connection).records(table).get(identity)
    if raw is None:
        return None
    if len(raw.encode()) > MAX_RECORD_BYTES:
        raise TaskActionError('Planning task record exceeds its byte bound')
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get('task_id' if table in {'tasks', 'memories'} else 'conversation_id') != identity:
        raise TaskActionError('Planning task record identity changed')
    return value


RecordReader = Callable[[object, PlanningCollection, str], dict | None]


def write_record(connection, table: PlanningCollection, identity: str, value: dict, *,
                 existing_reader: RecordReader = read_record) -> None:
    """Shared byte/count/encoding rules; a trusted service can retain its stricter read.

    The reader port is Python composition, never a model argument or installed entrypoint.
    It preserves validation of existing memory/provenance before a task-action update.
    """
    validate_identity(identity)
    content = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    if len(content.encode()) > MAX_RECORD_BYTES:
        raise TaskActionError('Planning task record exceeds its byte bound')
    if existing_reader(connection, table, identity) is None and adapt_legacy(connection).records(table).count() >= MAX_RECORDS:
        raise TaskActionError('Planning task storage limit reached')
    adapt_legacy(connection).records(table).put(identity, content)
