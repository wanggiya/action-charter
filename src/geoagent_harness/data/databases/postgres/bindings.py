"""Mechanical same-chat identity bindings, never permissions or database access."""
from geoagent_harness.contracts.paths import relative_path
from geoagent_harness.data.databases.postgres.service import connection_sha256

def known_sources(state):
    if hasattr(state,'model_dump'):state=state.model_dump(mode='json')
    result={}
    for observation in (state.get('analytical_session') or {}).get('observations',[]):
        payload=observation.get('result') or {}
        for value in (payload,payload.get('dataset_profile') or {}):
            if isinstance(value.get('source'),str) and isinstance(value.get('source_sha256'),str):
                result[relative_path(value['source'],'input')]=value['source_sha256']
    return result

def bind(plan,state,settings):
    sources=known_sources(state);assigned=[]
    for step in plan.steps:
        if step.skill not in {'import_csv_to_postgres','validate_postgres_import'}:continue
        args=step.arguments
        if not args.get('connection_sha256'):
            args['connection_sha256']=connection_sha256(settings);assigned.append(step.step_id)
        if args.get('path') and not args.get('source_sha256'):
            path=relative_path(args['path'],'input')
            if path in sources:args['source_sha256']=sources[path]
    return assigned
