from geoagent_harness.core.policy.table import validate_steps
"""Validate table contracts/references before any approval or execution."""
from pathlib import Path
from pydantic import ValidationError
from geoagent_harness.contracts.tabular import ARGUMENTS, WRITE_IDS, is_extension, is_table_write
from geoagent_harness.contracts.operation_packages import ProjectionArguments
from geoagent_harness.contracts.paths import TabularError, relative_path
from geoagent_harness.contracts.table_sources import TABLE_SUFFIXES



def preflight_calculations(steps, root):
    """Bounded read-only checks for known sources; intermediates recheck at runtime."""
    from geoagent_harness.data.tabular.service import read_bytes, read_frame
    from geoagent_harness.data.tabular.calculations import calculate
    from geoagent_harness.contracts.calculations import column_names
    known = {step.step_id: step for step in steps}
    cached = {}

    def columns(step_id, visiting=None):
        if step_id in cached:
            return cached[step_id]
        visiting = set() if visiting is None else visiting
        if step_id in visiting:
            return None  # Existing dependency policy rejects cycles.
        visiting = visiting | {step_id}
        step = known[step_id]
        args = step.arguments
        if step.skill == 'aggregate_csv':
            names = [*args['by'], *(item['output_column'] for item in args['aggregations'])]
        elif args.get('path') and step.skill in ARGUMENTS and step.skill != 'vector_attributes_to_csv':
            names = list(read_frame(read_bytes(root, args['path']), args.get('delimiter', ',')).columns)
        elif args.get('source_step') in known:
            names = columns(args['source_step'], visiting)
        else:
            names = None
        if step.skill == 'select_csv_columns': names = args['columns']
        elif step.skill == 'aggregate_csv': names = [*args['by'], *(item['output_column'] for item in args['aggregations'])]
        elif step.skill == 'join_csv': names = None  # Rechecked against actual joined output.
        elif step.skill == 'calculate_csv_columns' and names is not None:
            names = [*names, *(item['output_column'] for item in args['calculations'])]
        cached[step_id] = names
        return names

    for step in steps:
        if step.skill != 'calculate_csv_columns':
            continue
        args = ARGUMENTS[step.skill].model_validate(step.arguments)
        if args.path:
            frame = read_frame(read_bytes(root, args.path), args.delimiter)
            from geoagent_harness.data.tabular.calculations import numeric_inputs
            numeric_inputs(frame, args)  # Validate all referenced source values/types.
            calculate(frame.head(100), args)  # No publication; bounded candidate check.
        else:
            names = columns(args.source_step)
            if names is not None:
                outputs = {item.output_column for item in args.calculations}
                references = set().union(*(column_names(item.expression) for item in args.calculations))
                if references - set(names) or outputs & set(names) or len(names) + len(outputs) > 100:
                    raise TabularError('Calculation references unknown source columns or collides with the source schema')
