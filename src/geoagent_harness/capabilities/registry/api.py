"""Shared metadata/package services used by HTTP and CLI."""
from pathlib import Path
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
from geoagent_harness.capabilities.registry.registry import operation_catalog
from geoagent_harness.capabilities.registry.discovery import ScanRequest, scan_libraries, library_inventory
from geoagent_harness.capabilities.registry.storage import save_scan, read_scan, candidate_page
from geoagent_harness.contracts.operation_packages import parse_package
from geoagent_harness.capabilities.registry.packages import test_package, install_package

class PackageRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    action:Literal['test_operation_package','install_operation_package']
    manifest:dict
    confirmed_package_sha256:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    confirm_install:bool=False

def scan(request,root):
    report=scan_libraries(request)
    save_scan(root,report)
    return {key:value for key,value in report.items() if key!='candidates'} | {'snapshot_saved':True,'snapshot_effect':'project_local_discovery_metadata_only','page':candidate_page(report)}

def package_action(request,root):
    package=parse_package(request.manifest)
    if request.action=='test_operation_package':return test_package(package.model_dump())
    return install_package(package.model_dump(),request.confirmed_package_sha256,root=root,confirm=request.confirm_install)
