"""Local exclusive records and journals; domain schemas/digests remain with callers."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat
import uuid
from geoagent_harness.platform.storage.ledger_contracts import UnsafeLedgerRecord


class LocalImmutableRecords:
    def __init__(self, directory):
        self.directory = Path(directory)

    def _path(self, name):
        if not isinstance(name, str) or name in {'', '.', '..'} or Path(name).name != name or '/' in name or '\\' in name:
            raise ValueError('Ledger record name must be one path component')
        return self.directory / name

    @contextmanager
    def create_text(self, name, *, encoding='utf-8', newline=None):
        path = self._path(name)
        with path.open('x', encoding=encoding, newline=newline) as stream:
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        self.sync()

    def read_text(self, name, *, encoding='utf-8'):
        return self._path(name).read_text(encoding=encoding)

    def read_bytes(self, name, *, max_bytes):
        if type(max_bytes) is not int or max_bytes < 1:
            raise ValueError('A positive record byte limit is required')
        fd = os.open(self._path(name), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > max_bytes:
                raise UnsafeLedgerRecord('Unsafe or oversized ledger record')
            content = stream.read(max_bytes + 1)
            if len(content) > max_bytes:
                raise UnsafeLedgerRecord('Ledger record exceeded its byte limit while reading')
            return content

    def sync(self):
        fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    @contextmanager
    def _publication(self):
        # Directory inode lock coordinates local writers without removable lockfiles.
        fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield fd
            os.fsync(fd)
        finally:
            os.close(fd)

    def publish_directory(self, staged, name, *, rename=False):
        destination = self._path(name)
        with self._publication():
            if destination.exists() or destination.is_symlink():
                raise FileExistsError('Immutable ledger package already exists')
            # Keep the established fault-injection primitive; neither may overwrite.
            (os.rename if rename else os.replace)(staged, destination)

    def publish_file(self, staged, name):
        with self._publication():
            os.link(staged, self._path(name))


class LocalAttemptLedger(LocalImmutableRecords):
    @contextmanager
    def lock(self, name):
        fd = os.open(self._path(name), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)

    def claim(self, name, content):
        fd = os.open(self._path(name), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        self.sync()

    def append(self, name, content, *, create, max_existing_bytes):
        flags = os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK
        if create:
            flags |= os.O_CREAT | os.O_EXCL
        fd = os.open(self._path(name), flags, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > max_existing_bytes:
                raise OSError('Unsafe attempt event history')
            data = content()  # trusted first-party constructor, after storage checks
            if os.write(fd, data) != len(data):
                raise OSError('Incomplete attempt event')
            os.fsync(fd)
        finally:
            os.close(fd)

    def replace_snapshot(self, name, content):
        destination = self._path(name)
        temporary = self.directory / ('.attempt-' + uuid.uuid4().hex)
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
            self.sync()
        finally:
            temporary.unlink(missing_ok=True)

    def append_checked(self, name, content, *, max_bytes):
        fd = os.open(self._path(name), os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK, 0o644)
        with os.fdopen(fd, 'a+b') as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > max_bytes:
                raise UnsafeLedgerRecord('Unsafe or oversized append-only ledger')
            os.fchmod(stream.fileno(), 0o644)
            stream.seek(0)
            existing = stream.read(max_bytes + 1)
            block = content(existing)  # domain validation under the same lock
            if len(existing) + len(block) > max_bytes:
                raise OSError('Append-only ledger exceeds its byte budget')
            stream.seek(0, os.SEEK_END)
            if stream.write(block) != len(block):
                raise OSError('Incomplete append-only ledger batch')
            stream.flush()
            os.fsync(stream.fileno())
        self.sync()
