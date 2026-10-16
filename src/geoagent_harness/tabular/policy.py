"""Validate table contracts/references before any approval or execution."""
from pathlib import Path
from pydantic import ValidationError
from .schemas import ARGUMENTS, WRITE_IDS, is_extension, is_table_write
from geoagent_harness.operations.packages import ProjectionArguments
from .service import TabularError, relative_path

def validate_steps(steps, dependencies):
    known={s.step_id:s for s in steps}
    def skill(step):return getattr(step,'skill',getattr(step,'skill_id',None))
    def ancestors(id):
        result=set();pending=list(dependencies[id])
        while pending:
            parent=pending.pop()
            if parent not in result:result.add(parent);pending.extend(dependencies[parent])
        return result
    targets=[]
    for step in steps:
        if step.arguments.get('target_path'):targets.append(step.arguments['target_path'])
        if skill(step) not in ARGUMENTS and not is_extension(skill(step)):continue
        try:
            args=(ProjectionArguments if is_extension(skill(step)) else ARGUMENTS[skill(step)]).model_validate(step.arguments)
        except ValidationError as error:
            for finding in error.errors(include_input=False,include_context=False,include_url=False):
                message=finding['msg']
                if message in {'Value error, Choose exactly one path or source_step','Value error, Choose exactly one right_path or right_step'}:
                    left,right=('right_path','right_step') if 'right_path' in message else ('path','source_step')
                    raise TabularError(f'{step.step_id}: choose exactly one {left} or {right}, never both. Use {left} for an original data/input file; use {right} only for a CSV-producing ancestor, never an inspection step. Omit the unused field.') from error
            raise

        for key in ('path','right_path'):
            path=getattr(args,key,None)
            if path:
                path=relative_path(path,'input')
                suffix=Path(path).suffix.lower()
                if suffix not in ({'.geojson','.json'} if skill(step)=='vector_attributes_to_csv' else {'.csv','.tsv'}):raise TabularError('Input format does not match the operation data contract')
        if is_table_write(skill(step)):
            target=relative_path(args.target_path,'output')
            if not target.endswith('.csv'):raise TabularError('Table output must be .csv')
            if hasattr(step,'requires_approval') and (not step.requires_approval or not step.validation_required):raise TabularError('Tabular writes require explicit approval and validation')
        for key in ('source_step','right_step'):
            ref=getattr(args,key,None)
            if ref:
                if ref not in ancestors(step.step_id):raise TabularError('Intermediate references must name completed ancestor operations')
                if not is_table_write(skill(known[ref])):raise TabularError(f'{step.step_id}: {key}={ref} references {skill(known[ref])}, which does not create a CSV file. Inspection returns metadata only. Use path for the original data/input file; source_step/right_step may reference CSV-producing transforms only.')
        if skill(step)=='vector_attributes_to_csv':
            if not any(skill(known[p])=='inspect_vector' and known[p].arguments.get('path')==args.path for p in ancestors(step.step_id)):
                raise TabularError('Vector attributes export must follow inspection of the same source')
    if len(targets)!=len(set(targets)):raise TabularError('Each write operation must declare a distinct output path')
