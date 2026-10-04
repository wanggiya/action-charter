"""Read-only existence check for explicitly selected task input, not content validation."""
from __future__ import annotations
from contextlib import ExitStack
import os
from pathlib import Path, PurePosixPath
import stat


def check_task_input(*, project_root: Path, input_path: str) -> str:
    from .service import IntentError
    if not isinstance(input_path, str) or not input_path.strip() or len(input_path) > 960:
        raise IntentError('select one input filename or relative path before reasoning')
    value = input_path.strip()
    if '/' not in value:
        value = 'data/input/' + value
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
