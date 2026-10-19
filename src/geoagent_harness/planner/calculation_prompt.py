"""Positive planning examples, never an executable fallback or parsed user intent."""


def calculation_reply_example(*, include_inspection):
    """Generic identifiers deliberately differ from the operator's actual task."""
    steps = []
    if include_inspection:
        steps.append({'step_id': 'step_1', 'skill': 'inspect_csv',
                      'purpose': 'Inspect the requested original CSV',
                      'arguments': {'path': 'data/input/example.csv'},
                      'requires_approval': False, 'validation_required': False})
    calculation = {
        'step_id': f'step_{len(steps) + 1}', 'skill': 'calculate_csv_columns',
        'purpose': 'Calculate a new numeric column while preserving the original columns',
        'arguments': {
            'path': 'data/input/example.csv', 'missing_policy': 'propagate',
            'calculations': [{'output_column': 'scaled_value', 'expression': {
                'kind': 'binary', 'operator': 'multiply',
                'left': {'kind': 'column', 'name': 'input_value'},
                'right': {'kind': 'number', 'value': 1.5}}}],
        },
        'requires_approval': True, 'validation_required': True,
    }
    if steps:
        calculation['depends_on'] = ['step_1']
    steps.append(calculation)
    return {
        'message': 'The calculation workflow is ready for review. Nothing was authorized or executed.',
        'plan': {'schema_version': '1.0', 'status': 'planned',
                 'summary': 'Inspect and calculate a new numeric column' if include_inspection else 'Calculate a new numeric column',
                 'steps': steps, 'assumptions': [], 'risks': [],
                 'execution_performed': False, 'validation_performed': False},
        'approval_performed': False, 'execution_performed': False,
    }


class SchemaRepairDeferral(ValueError):
    """A promise to repair is neither a workflow nor a missing-input question."""
