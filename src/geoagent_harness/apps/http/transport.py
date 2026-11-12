"""Loopback HTTP parsing, origin checks and response serialization."""
from __future__ import annotations
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
import json
import os
import re
from functools import wraps
from typing import Any
from geoagent_harness.contracts.interface_limits import MAX_INTERFACE_REQUEST_BYTES
from geoagent_harness.apps.http.context import RESPONSE_SENT
from geoagent_harness.apps.http.dispatch import POST_PATHS, dispatch_get, dispatch_post
from geoagent_harness.apps.http.errors import send_post_error


def make_handler(route_context):
    project_root = route_context.project_root
    from geoagent_harness.platform.execution_services import execution_services, using_execution_services
    configured_services = execution_services()
    class InterfaceRequestHandler(BaseHTTPRequestHandler):
        server_version = "ActionCharterInterface/1.0"
        sys_version = ""

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _send(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'none'")
            self.end_headers()
            self.wfile.write(body)

        def _reject_origin(self) -> bool:
            origin = self.headers.get('Origin')
            configured_origin = os.environ.get('INTERFACE_FRONTEND_ORIGIN')
            allowed_origins = {'http://127.0.0.1:5173', 'http://localhost:5173'}
            if configured_origin and re.fullmatch('http://(?:127\\.0\\.0\\.1|localhost):[1-9][0-9]{0,4}', configured_origin):
                allowed_origins.add(configured_origin)
            if origin is None or origin in allowed_origins:
                return False
            self._send(HTTPStatus.FORBIDDEN, {'error': 'request origin is not allowed'})
            return True

        def do_GET(self):
            if self._reject_origin():
                return
            dispatch_get(self, route_context)

        def do_POST(self) -> None:
            if self._reject_origin():
                return
            from geoagent_harness.platform.model_gateway.catalog import request_selection
            with request_selection(project_root):
                self._post_selected()

        def _post_selected(self):
            if self._reject_origin():
                return
            if self.path not in POST_PATHS:
                self._send(HTTPStatus.NOT_FOUND, {'error': 'endpoint is not available'})
                return
            if self.headers.get_content_type() != 'application/json':
                self._send(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {'error': 'application/json is required'})
                return
            try:
                length = int(self.headers.get('Content-Length', ''))
            except ValueError:
                length = -1
            if length < 1 or length > MAX_INTERFACE_REQUEST_BYTES:
                self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {'error': 'request body size is invalid'})
                return
            try:
                payload = json.loads(self.rfile.read(length))
                response = dispatch_post(self, route_context, payload)
            except Exception as exc:
                if not send_post_error(self, route_context, exc):
                    raise
                return
            if response is not RESPONSE_SENT:
                self._send(HTTPStatus.OK, response)

    def with_services(function):
        @wraps(function)
        def invoke(*args, **kwargs):
            with using_execution_services(configured_services):
                return function(*args, **kwargs)
        return invoke

    # Request threads start with an empty context. Bind the server's trusted
    # service profile explicitly; never fall back to another global profile.
    InterfaceRequestHandler.do_GET = with_services(InterfaceRequestHandler.do_GET)
    InterfaceRequestHandler.do_POST = with_services(InterfaceRequestHandler.do_POST)
    return InterfaceRequestHandler
