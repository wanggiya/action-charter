"""Portable structural decoding; authoritative validators keep all field rules."""
from copy import deepcopy


def decoder_schema(schema, operation_schemas=None, *, step_sequence=None, inspection_source=None, inspection_arguments=None):
    # Older local grammar compilers reject some regexes/bounds in full Pydantic
    # schemas. Keep structure, enums/consts and closed objects; validate patterns,
    # limits and cross-field policy independently after generation. This is not
    # an execution schema or an automatic downgrade to unstructured generation.
    omitted = {'pattern', 'title', 'default', 'description', 'maxLength', 'minLength',
               'maxItems', 'minItems', 'minimum', 'maximum', 'exclusiveMinimum',
               'exclusiveMaximum', 'format'}
    def walk(value, mapping=False):
        if isinstance(value, list):
            return [walk(item) for item in value]
        if not isinstance(value, dict):
            return value
        return {key: walk(item, key in {'properties', '$defs', 'definitions', 'patternProperties'})
                for key, item in value.items() if mapping or key not in omitted}
    result = walk(deepcopy(schema))
    if not operation_schemas:
        return result

    step = result['$defs']['PlanStep']
    available = step['properties']['skill']['enum']
    alternatives = []
    for skill, source in operation_schemas.items():
        if skill not in available:
            continue
        argument = walk(deepcopy(source))
        # Each argument model owns a separate definition namespace. Recursive
        # expression references must not resolve against another model's defs.
        names = {name: f'operation_{skill}_{name}' for name in argument.pop('$defs', {})}
        definitions = source.get('$defs', {})

        def refs(value):
            if isinstance(value, list):
                return [refs(item) for item in value]
            if not isinstance(value, dict):
                return value
            return {key: ('#/$defs/' + names[item[8:]] if key == '$ref' and item.startswith('#/$defs/') and item[8:] in names else refs(item)) for key, item in value.items()}

        for name, definition in definitions.items():
            result['$defs'][names[name]] = refs(walk(deepcopy(definition)))
        argument = refs(argument)
        # Materialize the trusted Source model's exclusive choices as closed
        # objects. Grammar compilers need not interpret intersecting allOf /
        # oneOf property overrides to keep path and source_step exclusive.
        variants = [argument]
        for left, right in (('path', 'source_step'), ('right_path', 'right_step')):
            if not {left, right}.issubset(argument.get('properties', {})):
                continue
            constraint = next((item for item in argument.get('allOf', [])
                               if item.get('oneOf') and {tuple(choice.get('required', [])) for choice in item['oneOf']} == {(left,), (right,)}), None)
            if constraint is None:
                continue
            expanded = []
            for variant in variants:
                for chosen, unused in ((left, right), (right, left)):
                    choice = deepcopy(variant)
                    choice['properties'].pop(unused)
                    choice['properties'][chosen] = {'type': 'string'}
                    choice['required'] = list(dict.fromkeys([*choice.get('required', []), chosen]))
                    choice['allOf'] = [item for item in choice.get('allOf', []) if item != constraint]
                    if not choice['allOf']:
                        choice.pop('allOf')
                    expanded.append(choice)
            variants = expanded
        branch = deepcopy(step)
        branch['properties']['skill'] = {'type': 'string', 'const': skill}
        branch['properties']['arguments'] = variants[0] if len(variants) == 1 else {'anyOf': variants}
        branch['required'] = list(dict.fromkeys([*branch['required'], 'arguments']))
        alternatives.append(branch)
    remaining = [skill for skill in available if skill not in operation_schemas]
    if remaining:
        branch = deepcopy(step)
        branch['properties']['skill']['enum'] = remaining
        alternatives.append(branch)
    result['$defs']['PlanStep'] = {'anyOf': alternatives}
    if step_sequence:
        # A small requested workflow skeleton, not a generated fallback plan.
        # Every argument/expression still comes from the model and is validated.
        by_skill = {branch['properties']['skill'].get('const'): branch for branch in alternatives}
        result['$defs']['WorkflowPlan']['properties']['steps'] = {
            'type': 'array', 'prefixItems': [deepcopy(by_skill[skill]) for skill in step_sequence],
            'minItems': len(step_sequence), 'maxItems': len(step_sequence),
        }
        if inspection_source is not None and step_sequence == ['inspect_csv', 'calculate_csv_columns']:
            # "Keep the inspection" binds its existing source, not the generic
            # example filename. Inspection is not a table-producing source_step.
            for branch in result['$defs']['WorkflowPlan']['properties']['steps']['prefixItems']:
                arguments = branch['properties']['arguments']
                if branch['properties']['skill'].get('const') == 'inspect_csv' and inspection_arguments is not None:
                    branch['properties']['arguments'] = {
                        'type': 'object', 'properties': {key: {'const': value} for key, value in inspection_arguments.items()},
                        'required': list(inspection_arguments), 'additionalProperties': False,
                    }
                    continue
                if 'anyOf' in arguments:
                    arguments = next(item for item in arguments['anyOf'] if 'path' in item['properties'])
                    branch['properties']['arguments'] = arguments
                arguments['properties']['path'] = {'type': 'string', 'const': inspection_source}
                branch['properties']['depends_on'] = {'type': 'array', 'items': {'type': 'string', 'const': 'step_1'}, 'minItems': 1, 'maxItems': 1}
                branch['required'] = list(dict.fromkeys([*branch['required'], 'depends_on']))
    # A full proposal cannot simultaneously request a separate workflow action
    # or recipe/discovery exchange. These are already rejected by the service;
    # express the same distinction to the grammar instead of spending repair on
    # incompatible optional fields filled by small models.
    definitions = result.pop('$defs')
    proposal = deepcopy(result)
    proposal['properties']['plan'] = {'$ref': '#/$defs/WorkflowPlan'}
    proposal['required'] = list(dict.fromkeys([*proposal['required'], 'plan']))
    for name in ('workflow_action', 'recipe_uses', 'recipe_discovery'):
        proposal['properties'].pop(name)
    exchange = deepcopy(result)
    exchange['properties']['plan'] = {'type': 'null'}
    return {'type': 'object', 'anyOf': [proposal, exchange], '$defs': definitions}
