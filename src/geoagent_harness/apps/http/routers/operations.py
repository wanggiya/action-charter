"""Existing operations HTTP adapters; shared actions retain execution authority."""
from __future__ import annotations
from http import HTTPStatus
import json
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.apps.http.context import RESPONSE_SENT

def get_metadata(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from urllib.parse import urlparse, parse_qs
    from geoagent_harness.capabilities.registry.registry import operation_catalog
    from geoagent_harness.capabilities.registry.discovery import library_inventory
    from geoagent_harness.capabilities.registry.storage import read_scan, candidate_page
    from geoagent_harness.capabilities.registry.storage import saved_scans
    url = urlparse(self.path)
    params = parse_qs(url.query)
    try:
        if url.path == '/api/v1/operations/catalog':
            payload = operation_catalog(project_root, params.get('q', [''])[0])
        elif url.path == '/api/v1/operations/libraries':
            payload = library_inventory()
        elif url.path == '/api/v1/operations/scans':
            payload = saved_scans(project_root)
        elif url.path == '/api/v1/operations/candidates':
            payload = candidate_page(read_scan(project_root, params.get('scan', [''])[0]), params.get('q', [''])[0], params.get('distribution', [''])[0], params.get('kind', [''])[0], int(params.get('offset', ['0'])[0]), int(params.get('limit', ['50'])[0]))
        else:
            self._send(HTTPStatus.NOT_FOUND, {'error': 'Operation metadata endpoint not available'})
            return RESPONSE_SENT
    except (ValueError, OSError, RuntimeError):
        self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error': 'Operation metadata is unavailable or request bounds/identity are invalid'})
        return RESPONSE_SENT
    self._send(HTTPStatus.OK, payload)
    return RESPONSE_SENT

def post_1_scan(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.capabilities.registry.discovery import ScanRequest
    from geoagent_harness.capabilities.registry.api import PackageRequest, scan, package_action
    if self.path == '/api/v1/operations/scan':
        response = scan(ScanRequest.model_validate(payload), project_root)
    else:
        operation_request = PackageRequest.model_validate(payload)
        expected = 'test_operation_package' if self.path.endswith('/test-package') else 'install_operation_package'
        if operation_request.action != expected:
            raise route_context.services.InterfaceApiError('Package action does not match the endpoint')
        response = package_action(operation_request, project_root)
    return response
