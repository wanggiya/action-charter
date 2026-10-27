"""Reuse create-only publication and descriptor-based project path boundaries."""
from contextlib import ExitStack
import os
import stat
from .service import MAX_BYTES, PostgresError
from geoagent_harness.discovery.source import relative_path, _parent

def publish(root,path,data):
    from geoagent_harness.tabular.service import _publish
    return _publish(root,path,data)

def read_output(root,path):
    value=relative_path(path,'output')
    with ExitStack() as stack:
        try:
            parent,name=_parent(stack,root.resolve(),value)
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent);stack.callback(os.close,fd)
            before=os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size>MAX_BYTES:raise PostgresError('Output must be a bounded regular file')
            data=bytearray()
            while chunk:=os.read(fd,65536):
                data.extend(chunk)
                if len(data)>MAX_BYTES:raise PostgresError('Output exceeds 64 MiB')
            after=os.fstat(fd)
            if (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns):raise PostgresError('Output changed during verification')
            return bytes(data)
        except OSError as error:raise PostgresError('Output is unavailable or contains an unsafe link') from error
