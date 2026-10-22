"""Shared no-follow local path access; legacy tabular names remain re-exported."""
from __future__ import annotations
import os
from pathlib import PurePosixPath

class TabularError(ValueError):
    pass

def relative_path(value, area):
    if not isinstance(value,str): raise TabularError('File reference must be a string')
    if area == 'input' and '/' not in value and '\\' not in value and value not in {'.','..'}:
        value = 'data/input/' + value
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or str(parsed) != value or '\\' in value or any(ord(c)<32 for c in value) or '..' in parsed.parts or len(parsed.parts)<3 or parsed.parts[:2] != ('data',area):
        raise TabularError('Use a normalized relative path under data/' + area)
    return value

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

