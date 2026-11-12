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

