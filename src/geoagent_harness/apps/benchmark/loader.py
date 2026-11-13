"""Bounded, read-only definition loading. Dataset bytes are never opened here."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat

from pydantic import ValidationError
import yaml
from yaml.events import AliasEvent

from geoagent_harness.contracts.benchmark import BenchmarkTask, GoldExpected, relative_path

MAX_TASK_BYTES = 65536
MAX_TASKS = 256
MAX_SUITE_BYTES = 8 * 1024 * 1024
MAX_YAML_NODES = 4096
MAX_YAML_DEPTH = 24


class BenchmarkLoadError(ValueError):
    """Safe definition failure; raw requests/data are not included in messages."""


class _DefinitionLoader(yaml.SafeLoader):
    def __init__(self, stream):
        super().__init__(stream)
        self.nodes = self.depth = 0

    def compose_node(self, parent, index):
        self.nodes += 1
        self.depth += 1
        try:
            if self.check_event(AliasEvent) or self.nodes > MAX_YAML_NODES or self.depth > MAX_YAML_DEPTH:
                raise BenchmarkLoadError('YAML aliases, node or depth budgets exceeded')
            return super().compose_node(parent, index)
        finally:
            self.depth -= 1

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            if key_node.tag != 'tag:yaml.org,2002:str':
                raise BenchmarkLoadError('Definition keys must be strings')
            key = self.construct_object(key_node, deep=deep)
            if key in result:
                raise BenchmarkLoadError('Duplicate definition key')
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _safe_file(root: Path, relative: str, *, optional=False) -> Path | None:
    relative_path(relative)
    path = root
    for part in relative.split('/'):
        path = path / part
        if path.is_symlink():
            raise BenchmarkLoadError('Definition resources cannot contain links')
    try:
        meta = path.stat()
    except FileNotFoundError:
        if optional:
            return None
        raise BenchmarkLoadError('Required benchmark resource is missing') from None
    if not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1:
        raise BenchmarkLoadError('Benchmark resource must be a single regular file')
    return path


@dataclass(frozen=True)
class LoadedTask:
    task: BenchmarkTask
    task_sha256: str
    definition_bytes: int
    missing_local_inputs: tuple[str, ...]

    @property
    def available(self) -> bool:
        return not self.missing_local_inputs


def load_task(project_root: Path, task_id: str) -> LoadedTask:
    """Read benchmarks/tasks/<id>/task.yaml, bind identity and inspect input presence."""
    try:
        relative_path(task_id)
        if '/' in task_id:
            raise BenchmarkLoadError('Choose one task directory name')
        root = Path(project_root).resolve(strict=True)
        path = _safe_file(root, f'benchmarks/tasks/{task_id}/task.yaml')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            meta = os.fstat(stream.fileno())
            if not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1 or meta.st_size > MAX_TASK_BYTES:
                raise BenchmarkLoadError('Task definition exceeds file budget')
            raw = stream.read(MAX_TASK_BYTES + 1)
        if len(raw) > MAX_TASK_BYTES:
            raise BenchmarkLoadError('Task definition exceeds file budget')
        task = BenchmarkTask.model_validate(yaml.load(raw.decode('utf-8'), Loader=_DefinitionLoader))
        if task.id != task_id:
            raise BenchmarkLoadError('Task ID does not match its directory')
        missing = []
        for name in task.inputs:
            local = name.startswith('data/input/')
            if _safe_file(root if local else path.parent, name, optional=local) is None:
                missing.append(name)
        if isinstance(task.expected, GoldExpected):
            _safe_file(path.parent, task.expected.path)
        return LoadedTask(task, hashlib.sha256(raw).hexdigest(), len(raw), tuple(missing))
    except BenchmarkLoadError:
        raise
    except (OSError, ValueError, yaml.YAMLError, RecursionError) as error:
        if isinstance(error, ValidationError):
            raise BenchmarkLoadError('Invalid benchmark task schema') from None
        raise BenchmarkLoadError('Benchmark definition could not be loaded safely') from None


def load_suite(project_root: Path) -> tuple[LoadedTask, ...]:
    """Load all task directories deterministically; invalid definitions fail the suite."""
    root = Path(project_root).resolve(strict=True)
    directory = root / 'benchmarks/tasks'
    if any(p.is_symlink() for p in (root / 'benchmarks', directory)) or not directory.is_dir():
        raise BenchmarkLoadError('Benchmark tasks directory is missing or unsafe')
    names = []
    # Bound iteration before sorting or reading task contents.
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                raise BenchmarkLoadError('Task inventory must contain only task directories')
            names.append(entry.name)
            if len(names) > MAX_TASKS:
                raise BenchmarkLoadError('Suite task count exceeds budget')
    if not names:
        raise BenchmarkLoadError('Benchmark suite is empty')
    tasks, total = [], 0
    for name in sorted(names):
        task = load_task(root, name)
        total += task.definition_bytes
        if total > MAX_SUITE_BYTES:
            raise BenchmarkLoadError('Suite definition bytes exceed budget')
        tasks.append(task)
    return tuple(tasks)
