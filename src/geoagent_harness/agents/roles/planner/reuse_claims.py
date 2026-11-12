"""Ground descriptive reuse claims in sources supplied to this planning turn."""
from copy import deepcopy


class UnverifiedReuseClaim(ValueError):
    """The model claimed provenance unavailable or irrelevant to its proposal."""


def supplied_reuse_sources(methods, observations):
    sources = {item['method_id']: {
        'name': item['name'], 'skills': [step['skill'] for step in item['historical_operations']],
    } for item in methods}
    for request, finding in observations:
        if request.action != 'inspect' or finding.get('status') != 'found':
            continue
        item = finding.get('definition') or finding.get('own_chat_example')
        sources[request.recipe_id or request.method_id] = {
            'name': item['name'],
            'skills': item.get('skills') or [step['skill'] for step in item['historical_operations']],
        }
    return sources


def constrain_reuse_claims(schema, source_ids):
    """Constrain root Reply branches; never change operation argument fields."""
    result = deepcopy(schema)
    allowed = sorted(set(source_ids))

    def root(node):
        properties = node.get('properties', {})
        if 'reused_recipe_ids' in properties:
            if allowed:
                properties['reused_recipe_ids']['items'] = {'type': 'string', 'enum': allowed}
            else:
                # No empty enum or invented ID placeholders for grammar compilers.
                # Reply's default is []; no supplied provenance means no claim.
                properties.pop('reused_recipe_ids')
        for keyword in ('anyOf', 'oneOf'):
            for branch in node.get(keyword, []):
                root(branch)

    root(result)
    return result
