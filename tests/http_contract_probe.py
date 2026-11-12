"""Bounded in-memory HTTP contract probe; public sample metadata, no model/network."""
from contextlib import ExitStack, nullcontext
from email.message import Message
from io import BytesIO
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch


def capture_contract(inventory):
    from geoagent_harness.apps.http import server
    from geoagent_harness.platform.model_gateway import catalog, diagnostics
    from geoagent_harness.capabilities.registry import discovery
    from geoagent_harness.capabilities.registry import api as operations
    from geoagent_harness.capabilities.registry import registry
    from geoagent_harness.task_actions import execution
    source = Path(__file__).resolve().parents[1]
    with TemporaryDirectory() as directory, ExitStack() as stack:
        root = Path(directory)
        (root / 'context').mkdir()
        shutil.copyfile(source / 'context/SKILLS_INDEX.yaml', root / 'context/SKILLS_INDEX.yaml')
        (root / 'data/input').mkdir(parents=True)
        stack.enter_context(patch.object(catalog, 'request_selection', lambda _root: nullcontext()))
        stack.enter_context(patch.object(catalog, 'catalog', lambda _root: {'models': [], 'fixture': True}))
        stack.enter_context(patch.object(diagnostics, 'inspect_model_configuration', lambda: {'fixture': True}))
        stack.enter_context(patch.object(discovery, 'library_inventory', lambda *_args: {'fixture': True, 'libraries': []}))
        stack.enter_context(patch.object(operations, 'scan', lambda *_args: {'fixture': True, 'scan_performed': False}))
        # Host package versions are live capability evidence, not HTTP extraction
        # changes. Fix only this probe's metadata to its original fixture values;
        # keep every response field and the historical snapshot unchanged.
        versions = {item['distribution']: item['installed_version']
            for operation in inventory['responses']['GET /api/v1/operations/catalog'][1]['operations']
            for item in operation['runtime_requirements']}
        missing = registry.metadata.PackageNotFoundError

        def fixture_version(name):
            if versions.get(name) is None:
                raise missing(name)
            return versions[name]

        stack.enter_context(patch.object(registry, 'metadata',
            SimpleNamespace(version=fixture_version, PackageNotFoundError=missing)))
        stack.enter_context(patch.object(server, 'effective_write_settings', lambda *_args: SimpleNamespace(enable_write_tools=False)))
        stack.enter_context(patch.object(server, '_EXECUTION_PROGRESS', {}))
        stack.enter_context(patch.object(execution, '_EXECUTION_PROGRESS', {}))
        handler_class = server._handler(root)
        results = {}

        def request(key, method, path, body=b'{}', content_type='application/json',
                    length=None, origin=None, error=None):
            handler = handler_class.__new__(handler_class)
            handler.path = path
            handler.headers = Message()
            if content_type is not None:
                handler.headers['Content-Type'] = content_type
            if length is not None:
                handler.headers['Content-Length'] = str(length)
            elif body is not None:
                handler.headers['Content-Length'] = str(len(body))
            if origin is not None:
                handler.headers['Origin'] = origin
            handler.rfile = BytesIO(body or b'')
            sent = []
            handler._send = lambda status, payload: sent.append([int(status), payload])
            if error is None:
                getattr(handler, 'do_' + method)()
            else:
                def fail(*_args, **_kwargs):
                    raise error
                with patch.object(server, 'plan_interface_task', fail):
                    getattr(handler, 'do_' + method)()
            assert len(sent) == 1, (key, sent)
            # Resource references stay logical; normalize only temporary source paths.
            results[key] = json.loads(json.dumps(sent[0]).replace(str(root), '<project>'))

        regex_paths = {
            'task_match': '/api/v1/tasks/task-fixture/context',
            'relationship_match': '/api/v1/tasks/task-fixture/relationships',
            'artifact_match': '/api/v1/tasks/task-fixture/artifacts',
            'review_match': '/api/v1/context/reviews/context-review.' + 'a' * 64 + '.json',
            'intent_review_match': '/api/v1/intent/reviews/intent-review.' + 'a' * 64 + '.json',
            'progress_match': '/api/v1/executions/' + 'a' * 64,
        }
        for item in inventory['get_routes']:
            path = regex_paths[item['match_name']] if item['kind'] == 'regex' else item['path']
            if item['kind'] == 'prefix':
                for suffix in ('catalog', 'libraries', 'scans', 'candidates', 'unknown'):
                    request('GET ' + path + suffix, 'GET', path + suffix)
            else:
                request('GET ' + path, 'GET', path)
        request('GET unknown', 'GET', '/api/v1/unknown')
        request('GET query rejected', 'GET', '/api/v1/health?q=1')
        request('GET origin rejected', 'GET', '/api/v1/health', origin='https://untrusted.invalid')
        for path in inventory['post_paths']:
            request('POST invalid ' + path, 'POST', path)
        request('POST unknown', 'POST', '/api/v1/unknown')
        request('POST origin rejected', 'POST', '/api/v1/plans/create', origin='https://untrusted.invalid')
        request('POST content type', 'POST', '/api/v1/plans/create', content_type='text/plain')
        request('POST malformed length', 'POST', '/api/v1/plans/create', length='invalid')
        request('POST missing length', 'POST', '/api/v1/plans/create', body=None)
        request('POST oversized', 'POST', '/api/v1/plans/create', length=65537)
        request('POST malformed JSON', 'POST', '/api/v1/plans/create', body=b'{')
        errors = {
            'bad input': server.InterfaceApiError('fixture invalid'),
            'changed digest': server.InterfaceApiError('fixture digest no longer matches'),
            'history': server.TaskHistoryError('fixture'),
            'compile': server.RecipeCompilationError('fixture'),
            'storage': server.RecipeStorageError('fixture'),
            'approval': server.RecipeApprovalError('fixture'),
            'critic': server.CriticAgentError('fixture'),
            'evidence': server.CriticEvidenceError('fixture'),
            'critic record': server.CriticResultRecordError('fixture'),
            'release': server.ReleaseAssessmentError('fixture'),
            'planner': server.PlannerAgentError('invalid plan schema'),
            'policy': server.PlannerPolicyError('fixture'),
            'model timeout': server.ModelClientError.timeout(),
            'model settings': server.ModelSettingsError('fixture'),
            'context': server.ContextPackError('fixture'),
            'write policy': server.WritePolicyError('fixture'),
            'registry': server.SkillRegistryError('fixture'),
            'io': OSError('fixture'),
            'value': ValueError('fixture'),
        }
        body = json.dumps({'action': 'plan_task', 'request': 'Inspect only',
                           'allowed_skill_ids': ['inspect_vector']}).encode()
        for name, error in errors.items():
            request('ERROR ' + name, 'POST', '/api/v1/plans/create', body=body, error=error)
        return results
