from geoagent_harness.contracts.paths import TabularError, relative_path
"""Shared no-follow local path access; legacy tabular names remain re-exported."""
import os
from pathlib import PurePosixPath



def _parent(stack, root, value, create=False):
    fd=os.open(root.resolve(strict=True),os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    stack.callback(os.close,fd)
    parts=PurePosixPath(value).parts
    for part in parts[:-1]:
        if create:
            try: os.mkdir(part,mode=0o700,dir_fd=fd)
            except FileExistsError: pass
        fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
        stack.callback(os.close,fd)
    return fd,parts[-1]


def fingerprint(root, path, *, expected_identity=None, max_bytes=1024**3):
    """Hash one closed source/package without parsing statistics or loading GDAL.

    Used only by explicitly permitted reads. Stat observations detect races;
    matching size/timestamps alone never establish reuse.
    """
    from contextlib import ExitStack
    import hashlib
    import json
    import stat
    import time
    from pathlib import Path
    from geoagent_harness.data.discovery.csv import identity
    from geoagent_harness.contracts.table_sources import RECORD_SUFFIXES, RECORD_MAX_BYTES, CSV_MAX_BYTES
    path = relative_path(path, 'input')
    suffix = Path(path).suffix.lower()
    if type(max_bytes) is not int or not 0 < max_bytes <= CSV_MAX_BYTES:
        raise ValueError('Invalid source fingerprint byte budget')
    deadline = time.monotonic() + 120
    def digest(fd, size):
        sha, count = hashlib.sha256(), 0
        while True:
            if time.monotonic() > deadline:
                raise ValueError('Source fingerprint exceeded its deadline')
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            count += len(chunk)
            if count > size:
                raise ValueError('Source grew during fingerprinting')
            sha.update(chunk)
        if count != size:
            raise ValueError('Source size changed during fingerprinting')
        return sha.hexdigest()
    if suffix in {'.shp', '.gpkg', '.tif', '.tiff'}:
        from geoagent_harness.data.discovery.spatial import package, unchanged
        with package(root, path) as (path, files, size):
            if size > max_bytes:
                raise ValueError('Source package exceeds remaining context byte budget')
            observed = {name: before for name, (_, before) in files.items()}
            if expected_identity is not None and observed != expected_identity:
                raise ValueError('Source package changed after metadata discovery')
            hashes = {name: digest(fd, before[2]) for name, (fd, before) in files.items()}
            unchanged(root, path, files)
        return dict(path=path, source_sha256=hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
                    bytes=size, source_identity=observed, identity_basis='package_manifest_sha256')
    maximum = CSV_MAX_BYTES if suffix in {'.csv', '.tsv'} else RECORD_MAX_BYTES if suffix in RECORD_SUFFIXES else 8 * 1024**2 if suffix == '.geojson' else None
    if maximum is None:
        raise ValueError('Unsupported source fingerprint format')
    maximum = min(maximum, max_bytes)
    with ExitStack() as stack:
        parent, name = _parent(stack, root, path)
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        stack.callback(os.close, fd)
        info = os.fstat(fd)
        before = identity(info)
        if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
            raise ValueError('Source fingerprint requires a bounded regular input')
        if expected_identity is not None and expected_identity != before:
            raise ValueError('Source changed after metadata discovery')
        sha = digest(fd, info.st_size)
        if identity(os.fstat(fd)) != before or identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) != before:
            raise ValueError('Source changed during fingerprinting')
    package = suffix == '.geojson'
    return dict(path=path, source_sha256=hashlib.sha256(json.dumps({path: sha}, sort_keys=True).encode()).hexdigest() if package else sha,
                bytes=info.st_size, source_identity=before,
                identity_basis='package_manifest_sha256' if package else 'file_sha256')

