"""One immutable package contract for PostGIS lifecycle evidence; old bytes retained."""
from geoagent_harness.platform.storage.ledger_provider import ledger_repositories
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile

from pydantic import BaseModel, ValidationError
from geoagent_harness.contracts.redaction import redact_value
from geoagent_harness.platform.workspace import _no_links


@dataclass(frozen=True)
class ArtifactStore:
    model: type[BaseModel]
    id_field: str
    suffix: str
    filename: str
    label: str
    error: type[Exception]
    redact: bool = False

    def snapshot(self, value):
        try: snapshot = self.model.model_validate(value.model_dump(mode='json'))
        except (ValidationError, AttributeError) as exc:
            raise self.error(f'{self.label} failed schema validation') from exc
        return snapshot

    def canonical(self, value):
        snapshot = self.snapshot(value)
        payload = snapshot.model_dump(mode='json')
        if self.redact and redact_value(payload) != payload:
            raise self.error(f'{self.label} contains unredacted secret material')
        return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + '\n'

    def digest(self, value):
        return hashlib.sha256(self.canonical(value).encode()).hexdigest()

    def package_name(self, value, digest):
        return f'{getattr(value, self.id_field)}.{digest}.{self.suffix}'

    def persist(self, value, root):
        value = self.snapshot(value)
        content = self.canonical(value)
        digest = hashlib.sha256(content.encode()).hexdigest()
        temporary = None
        try:
            _no_links(root)
            root.mkdir(mode=0o700, parents=True, exist_ok=True)
            root = root.resolve(strict=True)
            directory = root / self.package_name(value, digest)
            if directory.exists() or directory.is_symlink():
                raise self.error(f'{self.label} package already exists')
            temporary = Path(tempfile.mkdtemp(prefix='.postgis-evidence-', dir=root))
            staged = temporary / 'record'; staged.mkdir(mode=0o700)
            fd = os.open(staged / self.filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
                stream.write(content); stream.flush(); os.fsync(stream.fileno())
            ledger_repositories().immutable(directory.parent).publish_directory(staged, directory.name, rename=True)
            temporary.rmdir(); temporary = None
            parent = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try: os.fsync(parent)
            finally: os.close(parent)
            path = directory / self.filename
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise self.error(f'persisted {self.label} digest changed')
            return path, digest, value
        except (OSError, ValueError) as exc:
            raise self.error(f'{self.label} could not be persisted safely (symlink or unavailable root)') from exc
        finally:
            if temporary is not None: shutil.rmtree(temporary, ignore_errors=True)

    def load(self, path, root):
        try:
            _no_links(root)
            root = root.resolve(strict=True)
            candidate = path if path.is_absolute() else root / path
            _no_links(candidate)
            safe = candidate.resolve(strict=True)
            if safe.name != self.filename or safe.parent.parent != root:
                raise self.error(f'{self.label} evidence is invalid: escaped its approved package')
            from geoagent_harness.platform.storage.ledger_contracts import UnsafeLedgerRecord
            try:
                raw = ledger_repositories().immutable(safe.parent).read_bytes(safe.name, max_bytes=4_000_000).decode('utf-8')
            except UnsafeLedgerRecord as exc:
                raise self.error(f'{self.label} evidence is unsafe or oversized') from exc
            value = self.model.model_validate_json(raw)
        except (OSError, ValueError) as exc:
            raise self.error(f'{self.label} evidence is unavailable or invalid (including symlinks)') from exc
        canonical = self.canonical(value)
        if raw != canonical:
            raise self.error(f'{self.label} file is not canonical')
        if safe.parent.name != self.package_name(value, self.digest(value)):
            raise self.error(f'{self.label} package identity is invalid')
        if {item.name for item in safe.parent.iterdir()} != {self.filename}:
            raise self.error(f'{self.label} package contains unexpected files')
        return value
