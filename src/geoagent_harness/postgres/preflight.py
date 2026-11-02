"""Complete bounded import mapping validation; no database mutation or authority."""
import csv
import hashlib
import io
import json
from psycopg import sql


def mapped_values(row,indices,args):
    return tuple(None if row[i] in (col.null_values if col.null_values is not None else args.null_values) else row[i]
                 for i,col in zip(indices,args.columns))


def declarations(args):
    values=[sql.SQL('{} {} {}').format(sql.Identifier(c.name),sql.SQL(c.type),sql.SQL('' if c.nullable else 'NOT NULL')) for c in args.columns]
    if args.soft_delete_marker:values.append(sql.SQL('{} boolean NOT NULL DEFAULT false').format(sql.Identifier(args.soft_delete_marker)))
    if args.key_columns:values.append(sql.SQL('PRIMARY KEY ({})').format(sql.SQL(',').join(map(sql.Identifier,args.key_columns))))
    return values


def assess(args,data,source):
    from .service import _value,PostgresError,MAX_ROWS,MAX_COLUMNS
    from geoagent_harness.recipes.control import checkpoint
    try:
        reader=csv.reader(io.StringIO(data.decode('utf-8-sig')),delimiter=',' if args.source_step else args.delimiter,strict=True)
        header=next(reader)
        if not header or len(header)!=len(set(header)) or len(header)>MAX_COLUMNS or any(not n or len(n)>200 for n in header):raise PostgresError('Import CSV needs bounded unique nonempty columns')
        if any(c.source not in header for c in args.columns):raise PostgresError('Column mapping references absent source columns')
        indices=[header.index(c.source) for c in args.columns];key_indices=[i for i,c in enumerate(args.columns) if c.name in args.key_columns]
        counts={c.name:{'null_rows':0,'invalid_cast_rows':0,'not_null_violations':0} for c in args.columns}
        rows=0;keys=set();key_bytes=0;duplicates=0;missing_keys=0
        for row in reader:
            if not row:continue
            rows+=1
            if rows%1000==0:checkpoint()
            if rows>MAX_ROWS or len(row)!=len(header) or any(len(v)>4096 for v in row):raise PostgresError('CSV is ragged or exceeds 200,000 rows / 4,096 characters per cell')
            canonical=[];invalid=set()
            for col,value in zip(args.columns,mapped_values(row,indices,args)):
                counts[col.name]['null_rows']+=value is None
                counts[col.name]['not_null_violations']+=value is None and not col.nullable
                try:
                    if value is not None and '\x00' in value:raise PostgresError('NUL is not supported by PostgreSQL text')
                    canonical.append(_value(value,col.type))
                except PostgresError:
                    counts[col.name]['invalid_cast_rows']+=1;canonical.append(None);invalid.add(col.name)
            if key_indices and not invalid.intersection(args.key_columns):
                key=tuple(canonical[i] for i in key_indices)
                if None in key:missing_keys+=1
                elif key in keys:duplicates+=1
                else:
                    key_bytes+=len(json.dumps(key).encode())+128
                    if key_bytes>64*1024**2:raise PostgresError('Import key preflight exceeds 64 MiB state; no partial validation')
                    keys.add(key)
        passed=not duplicates and not missing_keys and all(not v['invalid_cast_rows'] and not v['not_null_violations'] for v in counts.values())
        ddl=sql.SQL('CREATE TABLE {}.{} ({});').format(sql.Identifier(args.target_schema),sql.Identifier(args.target_table),sql.SQL(',').join(declarations(args))).as_string()
        return {'schema_version':'postgres-import-preflight-v1','passed':passed,'source':source,'row_count':rows,
            'target_schema':args.target_schema,'target_table':args.target_table,'column_mapping':[c.model_dump(mode='json') for c in args.columns],
            'mapping_sha256':hashlib.sha256(json.dumps(args.model_dump(mode='json'),sort_keys=True).encode()).hexdigest(),
            'column_findings':counts,'key_findings':{'columns':args.key_columns,'distinct_keys':len(keys),'excess_occurrences':duplicates,'missing_key_rows':missing_keys},
            'proposed_ddl':ddl,'connection_sha256':args.connection_sha256,'database_written':False,'execution_authority':False,
            'limitations':['Source mapping preflight only; target existence and current database state are checked at execution.',
                           'No clinical meaning, population completeness, permission or future execution success is established.']}
    except (UnicodeError,csv.Error,StopIteration) as error:raise PostgresError('Import requires complete valid UTF-8 CSV') from error
