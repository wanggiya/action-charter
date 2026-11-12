"""Bounded verified installed-package metadata; no installation, model or execution."""
from __future__ import annotations
import json
import os
import re
from contextlib import ExitStack
from geoagent_harness.platform.workspace import runtime_store_path, ensure_state_root, WorkspaceError
from geoagent_harness.contracts.operation_packages import PackageError, ADAPTER_ENTRYPOINT, VERIFIER, DIRECTORY, MAX_BYTES, parse_package, package_sha

def _directory(stack, root, create=False):
    try:
        directory=runtime_store_path(root,DIRECTORY)
        if create:ensure_state_root(root)
    except WorkspaceError as error:raise PackageError(str(error)) from error
    fd=os.open(directory.parent.resolve(strict=True),os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    stack.callback(os.close,fd)
    if create:
        try:os.mkdir(DIRECTORY,0o700,dir_fd=fd)
        except FileExistsError:pass
    fd=os.open(DIRECTORY,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
    stack.callback(os.close,fd)
    return fd


def installed_packages(root):
    try:directory=runtime_store_path(root,DIRECTORY)
    except WorkspaceError as error:raise PackageError(str(error)) from error
    if not directory.exists() and not directory.is_symlink():return {}
    result={}
    try:
        with ExitStack() as stack:
            parent=_directory(stack,root)
            entries=[name for name in os.listdir(parent) if not re.fullmatch(r'\.package\.[a-f0-9]{32}\.tmp',name)]
            if len(entries)>20:raise PackageError('Installed package count exceeds 20')
            for filename in sorted(entries):
                if not re.fullmatch(r'ext_[a-z][a-z0-9_]{0,60}\.json',filename):raise PackageError('Unexpected installed package record')
                fd=os.open(filename,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
                with os.fdopen(fd,'rb') as handle:data=handle.read(MAX_BYTES+1)
                if len(data)>MAX_BYTES:raise PackageError('Installed package exceeds its bound')
                stored=json.loads(data)
                if set(stored)!={'package','package_sha256'}:raise PackageError('Installed package record has unknown fields')
                package=parse_package(stored['package'])
                if filename!=f'{package.id}.json' or stored['package_sha256']!=package_sha(package):raise PackageError('Installed package identity/digest mismatch')
                if package.id in result:raise PackageError('Conflicting installed versions; explicit update is not supported')
                result[package.id]=package
    except OSError as error:raise PackageError('Installed package directory/file is unsafe or unavailable') from error
    return result


def package_skills(root):
    from geoagent_harness.contracts.skill_registry import SkillDefinition
    return [SkillDefinition(id=p.id,version=p.version,status='implemented',kind='transformation',access='artifact_write',approval_required=True,validation_required=True,entrypoint=ADAPTER_ENTRYPOINT,verifier=VERIFIER) for p in installed_packages(root).values()]

