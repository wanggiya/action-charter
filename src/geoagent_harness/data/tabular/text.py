"""Closed text-transform language. Model strings are data, never Python/regex."""
from __future__ import annotations
from geoagent_harness.contracts.text_transform import TextStep, TextTransform


def reference_value(value, definition):
    """Independent scalar oracle; check expansion before allocating replacement."""
    if value is None: return None
    for step in definition.steps:
        if step.kind == 'strip': value=value.strip()
        elif step.kind == 'upper': value=value.upper()
        elif step.kind == 'lower': value=value.lower()
        elif step.kind == 'collapse_whitespace': value=' '.join(value.split())
        else:
            length=len(value)+value.count(step.old)*(len(step.new)-len(step.old))
            if length>4096: raise ValueError('Text transformation exceeds the 4096-character cell bound')
            value=value.replace(step.old,step.new)
        if len(value)>4096: raise ValueError('Text transformation exceeds the 4096-character cell bound')
    return value

def transform_frame(frame, definition):
    from geoagent_harness.contracts.paths import TabularError
    from geoagent_harness.data.tabular.service import _guard, pd
    if definition.source_column not in frame.columns: raise TabularError('Text source column does not exist')
    if definition.output_column in frame.columns: raise TabularError('Text output column already exists; preserve original columns')
    # Scalar preflight also bounds intermediate expansions before vectorization.
    for value in frame[definition.source_column]:
        reference_value(None if pd.isna(value) else str(value),definition)
    series=frame[definition.source_column].copy()
    for step in definition.steps:
        if step.kind=='strip':series=series.str.strip()
        elif step.kind=='upper':series=series.str.upper()
        elif step.kind=='lower':series=series.str.lower()
        elif step.kind=='collapse_whitespace':series=series.str.split().str.join(' ')
        else:series=series.str.replace(step.old,step.new,regex=False)
    result=frame.copy();result[definition.output_column]=series
    return _guard(result)

def verify_frame(original, actual, definition):
    from geoagent_harness.data.tabular.service import pd
    if definition.source_column not in original.columns or definition.output_column in original.columns:return False
    if list(actual.columns)!=[*original.columns,definition.output_column] or len(actual)!=len(original):return False
    if not actual[list(original.columns)].equals(original):return False
    expected=[reference_value(None if pd.isna(v) else str(v),definition) for v in original[definition.source_column]]
    # CSV's established contract represents an empty field as missing.
    observed=[None if pd.isna(v) else str(v) for v in actual[definition.output_column]]
    return observed==[None if v=='' else v for v in expected]


def execute_text(skill, args, definition, settings, completed_results=None):
    from geoagent_harness.data.tabular.service import _source, _csv_bytes, read_frame, _publish, _preview
    from geoagent_harness.contracts.paths import TabularError
    from geoagent_harness.core.policy.write_policy import guarded
    import hashlib
    @guarded
    def execute(settings):
        if not settings.enable_write_tools:raise TabularError('Write tools are disabled')
        original,source=_source(settings.project_root,args,completed_results or {})
        data=_csv_bytes(transform_frame(original,definition));actual=read_frame(data)
        if not verify_frame(original,actual,definition):raise TabularError('Independent text transformation verification failed before publication')
        path=_publish(settings.project_root,args.target_path,data)
        return {'operation':skill,'data_contract':'table/csv-v1','sources':[source],
            'output':{'path':path,'sha256':hashlib.sha256(data).hexdigest()},**_preview(actual,10),
            'text_transform_definition':definition.model_dump(mode='json'),'source_delimiter':',' if args.source_step else args.delimiter,
            'effects':'create_csv','execution_performed':True,'validation_performed':False,'warnings':[]}
    return execute(settings=settings)
