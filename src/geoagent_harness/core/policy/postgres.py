"""Database contracts validated for both Planner and direct recipe clients."""
from geoagent_harness.contracts.postgres import ARGUMENTS, WRITE_IDS
from geoagent_harness.contracts.paths import relative_path

def validate_steps(steps,dependencies):
    known={s.step_id:s for s in steps}
    def skill(s):return getattr(s,'skill',getattr(s,'skill_id',None))
    for step in steps:
        id=skill(step)
        if id not in ARGUMENTS:continue
        args=ARGUMENTS[id].model_validate(step.arguments)
        if getattr(args,'path',None):relative_path(args.path,'input')
        if getattr(args,'target_path',None):
            target=relative_path(args.target_path,'output')
            if not target.endswith('.csv'):raise ValueError('PostgreSQL export requires a .csv output')
        if id in WRITE_IDS and hasattr(step,'requires_approval') and (not step.requires_approval or not step.validation_required):raise ValueError('Database/file writes require approval and validation')
        ref=getattr(args,'source_step',None)
        if ref:
            from geoagent_harness.contracts.graph import ancestors
            if ref not in ancestors(step.step_id,dependencies):raise ValueError('Database source_step must be a preceding ancestor')
            source=known[ref]
            if id in {'import_csv_to_postgres','validate_postgres_import'}:
                from geoagent_harness.contracts.tabular import is_table_write
                if not is_table_write(skill(source)) and skill(source)!='export_postgres_to_csv':raise ValueError('Database import source_step must produce a validated CSV')
            elif id=='export_postgres_to_csv':
                if skill(source) not in {'import_csv_to_postgres','soft_delete_postgres_rows','restore_postgres_rows'}:raise ValueError('Database export source_step must produce a validated database snapshot')
                if any(source.arguments.get(k)!=getattr(args,k) for k in ('target_schema','target_table')):raise ValueError('Database export ancestor must target the same table')
    writers=[s for s in steps if skill(s)=='import_csv_to_postgres']
    targets=[(s.arguments['target_schema'],s.arguments['target_table']) for s in writers]
    if len(targets)!=len(set(targets)):raise ValueError('Each database import requires a distinct fresh table')
