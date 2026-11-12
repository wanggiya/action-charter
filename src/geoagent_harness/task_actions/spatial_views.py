"""Recorded-run scope and concurrency checks for bounded spatial display."""
from __future__ import annotations
from threading import BoundedSemaphore
from geoagent_harness.workspaces.sandbox.spatial_rendering import SpatialDisplayError, SpatialViewOptions, render_snapshot, raster_view, _png

_VIEW_SLOT = BoundedSemaphore(1)


def spatial_result(root, record, request):
    from geoagent_harness.contracts.errors import InterfaceApiError
    from geoagent_harness.workspaces.sandbox.inspection import bounded_read
    if (not request.conversation_id or request.conversation_id != record.get('conversation_id')
            or request.confirmed_plan_sha256 != record.get('plan_sha256')):
        raise InterfaceApiError('Spatial view requires the exact recorded chat and plan')
    step = next((s for s in record['steps'] if s['step_id'] == request.step_id), None)
    if not step or step['status'] not in {'completed', 'validated_success', 'reused_completed'}:
        raise InterfaceApiError('Select a completed spatial inspection')
    options = request.spatial
    skill = 'inspect_vector' if options.mode == 'vector' else 'inspect_raster'
    if step['skill_id'] != skill:
        raise InterfaceApiError('The requested view does not match this inspector')
    outcome = step.get('outcome') or {}
    digest = outcome.get('source_sha256') or outcome.get('spatial_source_sha256')
    path = step['arguments'].get('path')
    if not digest or not path:
        raise InterfaceApiError('This older result has no bounded spatial source binding. Its saved snapshot remains available; run a new inspection to enable verified viewing')
    if not _VIEW_SLOT.acquire(blocking=False):
        raise InterfaceApiError('Another spatial view is being prepared; wait for it before requesting a new read')
    try:
        result = bounded_read(root, action='spatial_view', path=path, source_sha256=digest,
                              view_options=options.model_dump(mode='json'))
    finally:
        _VIEW_SLOT.release()
    return {**result, 'run_id': record['run_id'], 'plan_sha256': record['plan_sha256'],
            'conversation_id': record['conversation_id'], 'step_id': step['step_id'],
            'source': path, 'source_sha256': digest, 'verified_at_read': True,
            'execution_performed': False, 'approval_performed': False}
