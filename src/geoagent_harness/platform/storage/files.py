"""Existing bounded JSON formats behind file repository contracts."""
from __future__ import annotations
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Literal

from geoagent_harness.platform.storage.contracts import RepositoryError


class FileJsonRecords:
    def __init__(self, directory: Path, *, max_bytes: int, immutable=False):
        self.directory = Path(directory)
        self.max_bytes, self.immutable = max_bytes, immutable

    def _check(self):
        if any(part.is_symlink() for part in (self.directory, *self.directory.parents)):
            raise RepositoryError('Record storage cannot contain symlinks')
        if self.directory.exists() and not self.directory.is_dir():
            raise RepositoryError('Record storage must be a directory')

    def _path(self, name):
        self._check()
        if not isinstance(name, str) or Path(name).name != name or not name.endswith('.json') or '\\' in name:
            raise RepositoryError('Choose a plain JSON record filename')
        path = self.directory / name
        if path.is_symlink():
            raise RepositoryError('Record storage cannot contain symlinks')
        return path

    def ensure(self):
        self._check()
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        return self.directory

    def read(self, name):
        path = self._path(name)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'r', encoding='utf-8') as stream:
            meta = os.fstat(stream.fileno())
            if not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1 or meta.st_size > self.max_bytes:
                raise RepositoryError('Record exceeds its storage contract')
            text = stream.read(self.max_bytes + 1)
            if len(text.encode('utf-8')) > self.max_bytes:
                raise RepositoryError('Record exceeds its storage contract')
        value = json.loads(text)
        if not isinstance(value, dict):
            raise RepositoryError('Stored record must be an object')
        return value

    def _content(self, content):
        if not isinstance(content, str) or len(content.encode('utf-8')) > self.max_bytes:
            raise RepositoryError('Record exceeds its storage contract')
        return content

    def create(self, name, content):
        path = self._path(name)
        self.ensure()
        self._content(content)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(content); stream.flush(); os.fsync(stream.fileno())
        except BaseException:
            path.unlink(missing_ok=True)
            raise

    def replace(self, name, content):
        if self.immutable:
            raise RepositoryError('Immutable artifacts cannot be replaced')
        path = self._path(name)
        self._content(content)
        fd, temporary = tempfile.mkstemp(dir=self.directory, prefix='.run-', suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(content); stream.flush(); os.fsync(stream.fileno())
            self._path(name)
            os.replace(temporary, path)
            directory_fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try: os.fsync(directory_fd)
            finally: os.close(directory_fd)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def names(self, *, order: Literal['name', 'recent', 'native'] = 'name', limit=None):
        self._check()
        if order not in {'name', 'recent', 'native'} or (limit is not None and (type(limit) is not int or limit < 0)):
            raise RepositoryError('Invalid file lookup options')
        paths = self.directory.glob('*.json')
        if order == 'name': paths = sorted(paths, key=lambda p: p.name)
        elif order == 'recent': paths = sorted(paths, key=lambda p: p.lstat().st_mtime, reverse=True)
        from itertools import islice
        return [path.name for path in (islice(paths, limit) if limit is not None else paths)]


class FilePlans(FileJsonRecords):
    def __init__(self, directory):
        from geoagent_harness.core.policy.approvals.service import MAX_PLAN_FILE_BYTES
        super().__init__(directory, max_bytes=MAX_PLAN_FILE_BYTES, immutable=True)

    def load(self, name):
        # Keep the original schema/version/path validator as the plan codec.
        from geoagent_harness.core.policy.approvals import load_planner_result, ApprovalError
        try:
            path = self._path(name)
        except RepositoryError as error:
            raise ApprovalError(str(error)) from error
        return load_planner_result(path=path, plan_root=self.directory)
