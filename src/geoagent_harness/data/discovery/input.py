"""Read-only existence check for explicitly selected task input, not content validation."""
from __future__ import annotations
from contextlib import ExitStack
import os
from pathlib import Path, PurePosixPath
import stat


def input_references(message, root):
    """Explicit mentions only; existence checks, never content reads or listing."""
    import re
    from geoagent_harness.contracts.paths import relative_path
    from geoagent_harness.contracts.table_sources import TABLE_SUFFIXES
    extensions = '|'.join(re.escape(suffix[1:]) for suffix in (*TABLE_SUFFIXES, '.geojson', '.gpkg', '.shp', '.tiff', '.tif'))
    pattern = r'(?<![\w/])(?:data/input/)?[A-Za-z0-9_./-]+\.(?:' + extensions + r')(?:\.[A-Za-z0-9_-]+)*\b'
    existing, missing = [], []
    unsafe = False
    for match in re.finditer(pattern, message, re.I):
        value = match[0]
        if value.startswith('data/output/'):
            continue
        prefix = message[max(0, match.start() - 90):match.start()]
        if re.search(r'\b(?:save|write|export|output|convert)(?:\s+\w+){0,4}\s+(?:to|as)\s*$', prefix, re.I):
            continue
        if re.search(r'\b(?:do not|don\x27t|never|not|without)\s+(?:read|use|inspect|open|include)\s*$', prefix, re.I):
            continue
        try:
            path = relative_path(value, 'input')
            if not path.startswith('data/input/'):
                raise ValueError('Input scope required')
        except ValueError:
            unsafe = True
            continue
        try:
            path = check_task_input(project_root=root, input_path=path)
        except ValueError:
            if path not in missing:
                missing.append(path)
        else:
            if path not in existing:
                existing.append(path)
        if len(existing) + len(missing) >= 8:
            break
    return {'existing_supplied_paths': existing, 'missing_supplied_paths': missing,
            'unsafe_input_reference': unsafe, 'existence_only': True,
            'content_inspected': False, 'execution_authority_granted': False}


def check_task_input(*, project_root: Path, input_path: str) -> str:
    from geoagent_harness.contracts.intent import IntentError
    if not isinstance(input_path, str) or not input_path.strip() or len(input_path) > 960:
        raise IntentError('select one input filename or relative path before reasoning')
    from geoagent_harness.contracts.paths import relative_path
    try:
        value = relative_path(input_path.strip(), 'input')
    except ValueError as error:
        raise IntentError(str(error)) from error
    parsed = PurePosixPath(value)
    if ('\\' in value or '\x00' in value or parsed.is_absolute() or '..' in parsed.parts
            or len(parsed.parts) < 3 or parsed.parts[:2] != ('data', 'input') or str(parsed) != value):
        raise IntentError('selected input must be a normalized relative path under data/input')
    try:
        # Open each component relative to its parent descriptor. Never follow a
        # directory/file symlink or block on a FIFO masquerading as a dataset.
        with ExitStack() as stack:
            parent = os.open(project_root.resolve(strict=True), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            stack.callback(os.close, parent)
            for component in parsed.parts[:-1]:
                parent = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                stack.callback(os.close, parent)
            fd = os.open(parsed.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            stack.callback(os.close, fd)
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise IntentError('selected input must be a regular file')
    except (OSError, ValueError) as exc:
        raise IntentError('selected input is unavailable or unsafe; choose an existing file under data/input') from exc
    return value
