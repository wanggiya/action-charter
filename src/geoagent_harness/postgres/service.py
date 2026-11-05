"""Fixed-query PostgreSQL adapter. All write entry points retain recipe authority gates."""
from contextlib import contextmanager, ExitStack
import csv
import hashlib
import io
import json
import re
from decimal import Decimal, InvalidOperation
import os
import stat
from pathlib import Path
import psycopg
from psycopg import sql
from .schemas import ARGUMENTS, READ_IDS, WRITE_IDS
from geoagent_harness.discovery.source import relative_path, _parent
from geoagent_harness.recipes.control import checkpoint
from geoagent_harness.write_policy import guarded

MAX_BYTES=64*1024*1024
MAX_ROWS=200000
MAX_COLUMNS=100
TIMEOUT_MS=15000
class PostgresError(ValueError):
    """Safe operational finding; never includes driver messages or connection secrets."""

def profile(settings):
    return {'profile':'configured','host':settings.postgres_host,'port':settings.postgres_port,'database':settings.postgres_database,'user':settings.postgres_user}

def connection_sha256(settings):
    return hashlib.sha256(json.dumps(profile(settings),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def _schema(args,settings):
    if args.target_schema not in settings.allowed_schemas:raise PostgresError('PostgreSQL schema is outside the configured allowlist')

def _relation(args):return sql.SQL('{}.{}').format(sql.Identifier(args.target_schema),sql.Identifier(args.target_table))

@contextmanager
def _transaction(settings,*,write=False):
    from geoagent_harness.verifier.postgis import _read_password, PostGISVerificationError
    connection=None
    try:
        connection=psycopg.connect(host=settings.postgres_host,port=settings.postgres_port,dbname=settings.postgres_database,
            user=settings.postgres_user,password=_read_password(settings.postgres_password_file),connect_timeout=5)
        with connection:
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ'+(' READ WRITE' if write else ' READ ONLY'))
                cursor.execute("SELECT set_config('statement_timeout', %s, true), set_config('lock_timeout', '3000', true), set_config('idle_in_transaction_session_timeout', '30000', true)",(str(TIMEOUT_MS),))
            yield connection
    except psycopg.Error as error:
        # A commit acknowledgement lost over the network must not imply rollback.
        raise PostgresError('PostgreSQL operation failed or commit is unconfirmed. Inspect the recorded run and actual target before a deliberate retry; driver details are private.') from error
    except (OSError, PostGISVerificationError) as error:
        raise PostgresError('PostgreSQL credentials are unavailable; check the launcher password-file configuration') from error
    finally:
        if connection is not None:connection.close()

def _metadata(connection,args):
    with connection.cursor() as c:
        c.execute("SELECT c.relkind FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=%s AND c.relname=%s",(args.target_schema,args.target_table))
        found=c.fetchone()
        if not found or found[0]!='r':raise PostgresError('Target must be an existing ordinary table; views, foreign and partitioned tables are unsupported')
        c.execute("SELECT column_name, data_type, udt_name, is_nullable FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position LIMIT 101",(args.target_schema,args.target_table))
        columns=[{'name':r[0],'type':r[1],'udt':r[2],'nullable':r[3]=='YES'} for r in c.fetchall()]
        if not columns or len(columns)>MAX_COLUMNS:raise PostgresError('Table exceeds 100 columns or is inaccessible')
        c.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_trigger WHERE tgrelid=%s::regclass AND NOT tgisinternal), EXISTS (SELECT 1 FROM pg_catalog.pg_class WHERE oid=%s::regclass AND relrowsecurity)",(f'"{args.target_schema}"."{args.target_table}"',)*2)
        triggers,rls=c.fetchone()
        if rls:raise PostgresError('Row-level security prevents this exact full-table snapshot contract; use a separately reviewed adapter')
    return columns,bool(triggers or rls)

def _value(value,kind):
    if value is None:return None
    if kind in {'bigint','int8','int4','int2'}:
        if not re.fullmatch(r'[+-]?[0-9]+',value):raise PostgresError('Integer mapping contains a non-integer value')
        number=int(value)
        if not -(2**63)<=number<2**63:raise PostgresError('Integer mapping exceeds bigint range')
        return str(number)
    if kind=='numeric':
        try:
            number=Decimal(value)
            if not number.is_finite() or len(value)>200 or abs(number.as_tuple().exponent)>1000:raise PostgresError('Numeric value is non-finite or exceeds precision budget')
            if number==0:return '0'
            # Exact canonical numeric spelling, independent of source scale.
            return format(number,'f').rstrip('0').rstrip('.') if '.' in format(number,'f') else format(number,'f')
        except InvalidOperation as error:raise PostgresError('Numeric mapping contains a non-numeric value') from error
    if kind in {'boolean','bool'}:
        if value.lower() not in {'true','false'}:raise PostgresError('Boolean mapping requires explicit true/false values')
        return value.lower()
    return value

def _row_digest(row,kinds):
    return hashlib.sha256(json.dumps([_value(v,k) for v,k in zip(row,kinds)],ensure_ascii=False,separators=(',',':')).encode()).digest()

def _snapshot(connection,args,settings,*,lock=False):
    if lock:
        with connection.cursor() as c:c.execute(sql.SQL('LOCK TABLE {} IN SHARE ROW EXCLUSIVE MODE').format(_relation(args)))
    columns,restricted=_metadata(connection,args)
    with connection.cursor() as c:
        c.execute('''SELECT k.conname,k.contype,array_agg(a.attname ORDER BY u.position)
            FROM pg_catalog.pg_constraint k
            JOIN pg_catalog.pg_class t ON t.oid=k.conrelid
            JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace
            CROSS JOIN LATERAL unnest(k.conkey) WITH ORDINALITY u(number,position)
            JOIN pg_catalog.pg_attribute a ON a.attrelid=t.oid AND a.attnum=u.number
            WHERE n.nspname=%s AND t.relname=%s AND k.contype IN ('p','u')
            GROUP BY k.conname,k.contype ORDER BY k.conname LIMIT 21''',(args.target_schema,args.target_table))
        key_rows=c.fetchall()
        if len(key_rows)>20:raise PostgresError('Table key metadata exceeds 20 constraints')
    key_constraints=[{'name':row[0],'kind':'primary' if row[1]=='p' else 'unique','columns':list(row[2])} for row in key_rows]
    names=[c['name'] for c in columns]
    query=sql.SQL('SELECT {} FROM {} LIMIT {}').format(sql.SQL(',').join(sql.SQL('{}::text').format(sql.Identifier(n)) for n in names),_relation(args),sql.Literal(MAX_ROWS+1))
    digests=[];preview=[];nulls={n:0 for n in names};used=0
    with connection.cursor(name='actioncharter_snapshot') as c:
        c.execute(query)
        while batch:=c.fetchmany(1000):
            checkpoint()
            for row in batch:
                encoded=json.dumps(list(row),ensure_ascii=False,separators=(',',':')).encode()
                used+=len(encoded)
                if used>MAX_BYTES or len(digests)>=MAX_ROWS:raise PostgresError('Table snapshot exceeds 200,000 rows or 64 MiB; refine the workflow')
                digests.append(_row_digest(row,[c['udt'] for c in columns]))
                for n,v in zip(names,row):nulls[n]+=v is None
                item={n:None if v is None else str(v)[:160] for n,v in zip(names,row)}
                if len(preview)<getattr(args,'preview_rows',5) and len(json.dumps(preview+[item]).encode())<=4096:preview.append(item)
    digest=hashlib.sha256(json.dumps([profile(settings),args.target_schema,args.target_table,columns,key_constraints],sort_keys=True).encode())
    for part in sorted(digests):digest.update(part)
    return {'target_schema':args.target_schema,'target_table':args.target_table,'connection':profile(settings),'connection_sha256':connection_sha256(settings),'row_count':len(digests),
        'column_metadata':columns,'key_constraints':key_constraints,'columns':names,'preview':preview,'missing_counts':nulls,'table_sha256':digest.hexdigest(),
        'semantic_sha256':hashlib.sha256(b''.join(sorted(digests))).hexdigest(),'restricted_write_target':restricted,'snapshot_policy':'Exact bounded multiset of all rows and column metadata; includes soft-deleted records. Not a persistent lock.'}

def inspect(skill,arguments,settings,completed_results=None):
    if skill not in READ_IDS:raise PostgresError('Only read-only database skills can use this entry point')
    args=ARGUMENTS[skill].model_validate(arguments);_schema(args,settings)
    if skill=='validate_postgres_import':
        if args.connection_sha256!=connection_sha256(settings):raise PostgresError('Configured database profile changed')
        from .preflight import assess
        data,binding=_input(args,settings,completed_results)
        return {'operation':skill,'execution_performed':True,**assess(args,data,binding)}
    with _transaction(settings) as connection:
        if skill=='discover_postgres_tables':
            with connection.cursor() as c:
                c.execute('SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname=%s)',(args.target_schema,))
                if not c.fetchone()[0]:raise PostgresError('Allowed PostgreSQL schema does not exist; creation is a separate administrator action')
                c.execute("SELECT c.relname FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=%s AND c.relkind='r' ORDER BY c.relname LIMIT 201",(args.target_schema,))
                rows=c.fetchall()
                if len(rows)>200:raise PostgresError('Schema discovery exceeds 200 tables')
            value={'target_schema':args.target_schema,'tables':[r[0] for r in rows],'connection':profile(settings),'connection_sha256':connection_sha256(settings)}
        else:value=_snapshot(connection,args,settings)
    return {'operation':skill,**value,'execution_performed':True,'database_written':False}

def _input(args,settings,completed):
    area='input';value=args.path;expected=args.source_sha256
    if args.source_step:
        prior=(completed or {}).get(args.source_step)
        if not prior or not prior.validation_performed or not (prior.validation_result or {}).get('passed'):raise PostgresError('CSV source_step must be a validated completed ancestor')
        result=prior.execution.result
        if result.get('data_contract')!='table/csv-v1':raise PostgresError('CSV source_step must produce a CSV artifact')
        value=result['output']['path'];expected=result['output']['sha256'];area='output'
    value=relative_path(value,area)
    if Path(value).suffix.lower() not in {'.csv','.tsv'}:raise PostgresError('Database import requires CSV/TSV input')
    with ExitStack() as stack:
        try:
            parent,name=_parent(stack,Path(settings.project_root).resolve(),value)
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent);stack.callback(os.close,fd)
            before=os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size>MAX_BYTES:raise PostgresError('Import input must be a regular file within 64 MiB')
            data=bytearray()
            while chunk:=os.read(fd,65536):
                checkpoint();data.extend(chunk)
                if len(data)>MAX_BYTES:raise PostgresError('Import input exceeds 64 MiB')
            after=os.fstat(fd)
            if (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns):raise PostgresError('Import source changed while reading')
        except OSError as error:raise PostgresError('Import source is unavailable or contains an unsafe path') from error
    if hashlib.sha256(data).hexdigest()!=expected:raise PostgresError('Import source digest changed since inspection; inspect and authorize the new source')
    return bytes(data),{'path':value,'sha256':expected,'area':area,'source_step':args.source_step}

def _bound_table(args,completed):
    if not args.source_step:return args.expected_table_sha256
    prior=(completed or {}).get(args.source_step)
    if not prior or not prior.validation_performed or not (prior.validation_result or {}).get('passed'):raise PostgresError('Database source_step must be completed and validated')
    result=prior.execution.result
    if result.get('target_schema')!=args.target_schema or result.get('target_table')!=args.target_table:raise PostgresError('Database source_step targets a different table')
    expected=result.get('table_sha256')
    if not expected:raise PostgresError('Database source_step has no verified table snapshot')
    return expected

def effects(skill,arguments,settings=None):
    args=ARGUMENTS[skill].model_validate(arguments)
    out={'connection_profile':'configured','schema':args.target_schema,'action':skill,'table':getattr(args,'target_table',None)}
    if settings:out['connection']=profile(settings)
    if skill=='import_csv_to_postgres':out.update(mode='Create new table only; existing targets reject',column_mapping=[c.model_dump() for c in args.columns],soft_delete_marker=args.soft_delete_marker,source_sha256=args.source_sha256,recovery='One transaction; no automatic retry. Inspect target if commit is unconfirmed.')
    elif skill=='export_postgres_to_csv':out.update(target_path=args.target_path,columns=args.columns,null_token=args.null_token,expected_table_sha256=args.expected_table_sha256,source_step=args.source_step,recovery='Create-only file; database unchanged. Choose fresh path after inspecting any partial outcome.')
    elif skill not in READ_IDS:out.update(selection={'key_column':args.key_column,'keys':args.keys},expected_affected_rows=args.expected_affected_rows,marker=args.deleted_column,marker_value=skill=='soft_delete_postgres_rows',expected_table_sha256=args.expected_table_sha256,recovery='Atomic marker update. Restore/delete requires a new snapshot and fresh authorization.')
    return out

def claim_authority(settings,approval_id,step_id):
    """One attempt per approved database step, including failed/unconfirmed attempts."""
    identity=hashlib.sha256((approval_id+':'+step_id).encode()).hexdigest()
    from geoagent_harness.workspace import runtime_store_path
    receipt_root=runtime_store_path(settings.project_root,'recipe-runs')
    receipt_root.mkdir(mode=0o700,parents=True,exist_ok=True)
    with ExitStack() as stack:
        try:
            parent,name=_parent(stack,receipt_root,'postgres-attempts/'+identity+'.json',create=True)
            fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            with os.fdopen(fd,'w') as handle:
                json.dump({'approval_id':approval_id,'step_id':step_id,'status':'attempted_or_unconfirmed'},handle);handle.flush();os.fsync(handle.fileno())
            os.fsync(parent)
        except FileExistsError as error:raise PostgresError('This database step authority already has an attempt; inspect the target and obtain fresh authorization') from error
        except OSError as error:raise PostgresError('Database authority receipt could not be safely persisted; nothing dispatched') from error

@guarded
def run_operation(skill,arguments,settings,completed_results=None):
    if skill not in WRITE_IDS or not settings.enable_write_tools:raise PostgresError('Database/file write operations are disabled')
    args=ARGUMENTS[skill].model_validate(arguments);_schema(args,settings);checkpoint()
    source=None;output=None;semantic=None
    if skill=='import_csv_to_postgres':
        if args.connection_sha256!=connection_sha256(settings):raise PostgresError('Configured database profile changed; inspect and authorize the intended connection')
        data,source=_input(args,settings,completed_results)
        from .preflight import assess
        preflight=assess(args,data,source)
        if not preflight['passed']:raise PostgresError('Import mapping preflight rejected: '+json.dumps({'columns':preflight['column_findings'],'key':preflight['key_findings']},separators=(',',':'))[:2000])
    if skill=='export_postgres_to_csv':
        relative_path(args.target_path,'output')
        if not args.target_path.endswith('.csv'):raise PostgresError('Database export target must be a new .csv under data/output')
    with _transaction(settings,write=skill!='export_postgres_to_csv') as connection:
        if skill=='import_csv_to_postgres':
            try:reader=csv.reader(io.StringIO(data.decode('utf-8-sig')),delimiter=',' if args.source_step else args.delimiter,strict=True);header=next(reader)
            except (UnicodeError,csv.Error,StopIteration) as error:raise PostgresError('Import requires UTF-8 CSV with a header') from error
            if len(header)!=len(set(header)) or len(header)>MAX_COLUMNS or any(not n or len(n)>200 for n in header):raise PostgresError('Import CSV needs bounded unique nonempty columns')
            if any(c.source not in header for c in args.columns):raise PostgresError('Column mapping references absent source columns')
            indices=[header.index(c.source) for c in args.columns]
            from .preflight import declarations,mapped_values
            with connection.cursor() as c:
                c.execute(sql.SQL('CREATE TABLE {} ({})').format(_relation(args),sql.SQL(',').join(declarations(args))))
                query=sql.SQL('COPY {} ({}) FROM STDIN').format(_relation(args),sql.SQL(',').join(sql.Identifier(x.name) for x in args.columns))
                count=0;expected_rows=[]
                try:
                    with c.copy(query) as copy:
                        for row in reader:
                            if not row:continue
                            count+=1
                            if count%1000==0:checkpoint()
                            if count>MAX_ROWS or len(row)!=len(header) or any(len(v)>4096 for v in row):raise PostgresError('CSV is ragged or exceeds 200,000 rows / 4,096 characters per cell')
                            values=mapped_values(row,indices,args)
                            canonical=tuple(_value(v,col.type) for v,col in zip(values,args.columns))
                            expected_rows.append(_row_digest([*canonical,*(['false'] if args.soft_delete_marker else [])],[*[col.type for col in args.columns],*(['boolean'] if args.soft_delete_marker else [])]))
                            copy.write_row(canonical)
                except (csv.Error,UnicodeError) as error:raise PostgresError('Import CSV parsing failed; transaction rolled back') from error
            after=_snapshot(connection,args,settings)
            if after['semantic_sha256']!=hashlib.sha256(b''.join(sorted(expected_rows))).hexdigest():raise PostgresError('Imported values do not match the declared source mapping; rolled back')
            if after['row_count']!=count:raise PostgresError('Import row-count reconciliation failed; transaction rolled back')
            affected=count
        elif skill=='export_postgres_to_csv':
            before=_snapshot(connection,args,settings)
            if before['table_sha256']!=_bound_table(args,completed_results):raise PostgresError('Database snapshot changed; inspect and authorize the current table')
            if set(args.columns)-set(before['columns']):raise PostgresError('Export references absent columns')
            stream=io.StringIO(newline='');writer=csv.writer(stream,lineterminator='\n');writer.writerow(args.columns);row_hashes=[]
            with connection.cursor(name='actioncharter_export') as c:
                c.execute(sql.SQL('SELECT {} FROM {}').format(sql.SQL(',').join(sql.SQL('{}::text').format(sql.Identifier(n)) for n in args.columns),_relation(args)))
                for row in c:
                    if len(row_hashes)%1000==0:checkpoint()
                    if any(v==args.null_token for v in row):raise PostgresError('Export null token collides with a data value; choose another token')
                    writer.writerow([args.null_token if v is None else v for v in row]);row_hashes.append(hashlib.sha256(json.dumps(list(row),ensure_ascii=False,separators=(',',':')).encode()).digest())
                    if stream.tell()>MAX_BYTES:raise PostgresError('Export exceeds 64 MiB')
            exported=stream.getvalue().encode();semantic=hashlib.sha256(b''.join(sorted(row_hashes))).hexdigest()
            if len(exported)>MAX_BYTES or len(row_hashes)!=before['row_count']:raise PostgresError('Export exceeds bounds or row reconciliation failed')
            # Publish after the read-only transaction exits successfully.
            after=before;affected=len(row_hashes)
        else:
            before=_snapshot(connection,args,settings,lock=True)
            if before['restricted_write_target']:raise PostgresError('Marker updates reject tables with user triggers or row-level security')
            if before['table_sha256']!=args.expected_table_sha256:raise PostgresError('Database snapshot changed; inspect and authorize current rows')
            meta={c['name']:c for c in before['column_metadata']}
            if args.key_column not in meta or args.deleted_column not in meta or meta[args.deleted_column]['udt']!='bool' or meta[args.deleted_column]['nullable']:raise PostgresError('Soft delete/restore requires an existing NOT NULL boolean marker and a known key')
            target=skill=='soft_delete_postgres_rows'
            with connection.cursor() as c:
                c.execute(sql.SQL('SELECT {}::text,{} FROM {} WHERE {}::text=ANY(%s)').format(sql.Identifier(args.key_column),sql.Identifier(args.deleted_column),_relation(args),sql.Identifier(args.key_column)),(args.keys,))
                rows=c.fetchall()
                if len(rows)!=args.expected_affected_rows or len({r[0] for r in rows})!=len(rows) or {r[0] for r in rows}!=set(args.keys) or any(r[1] is target for r in rows):raise PostgresError('Keys must uniquely select exactly the expected rows in the opposite marker state')
                c.execute(sql.SQL('UPDATE {} SET {}=%s WHERE {}::text=ANY(%s)').format(_relation(args),sql.Identifier(args.deleted_column),sql.Identifier(args.key_column)),(target,args.keys))
                affected=c.rowcount
                if affected!=args.expected_affected_rows:raise PostgresError('Affected row count changed; transaction rolled back')
            after=_snapshot(connection,args,settings)
            if after['row_count']!=before['row_count']:raise PostgresError('Marker operation changed row count; transaction rolled back')
        checkpoint()  # Cancellation before commit rolls back the complete active transaction.
    if skill=='export_postgres_to_csv':
        from .files import publish
        path=publish(Path(settings.project_root),args.target_path,exported)
        output={'path':path,'sha256':hashlib.sha256(exported).hexdigest()}
    if skill=='export_postgres_to_csv':
        after={**after,'columns':args.columns,'column_metadata':[c for c in after['column_metadata'] if c['name'] in args.columns],'preview':[{k:row[k] for k in args.columns} for row in after['preview']],'missing_counts':{k:after['missing_counts'][k] for k in args.columns}}
    return {'operation':skill,**after,'affected_rows':affected,'sources':[source] if source else [],'output':output,
        **({'mapping_sha256':preflight['mapping_sha256'],'executed_ddl':preflight['proposed_ddl']} if skill=='import_csv_to_postgres' else {}),
        'semantic_sha256':semantic or after['semantic_sha256'],'data_contract':'table/csv-v1' if output else 'database/snapshot-v1','arguments':args.model_dump(mode='json',exclude_none=True),'effects':effects(skill,arguments),
        'committed':skill!='export_postgres_to_csv','database_written':skill!='export_postgres_to_csv','execution_performed':True,
        'validation_performed':False,'recovery':'No automatic write retry. Inspect actual targets and this receipt before proposing a new authorized operation.'}

def validate_output(result,settings):
    args=ARGUMENTS[result['operation']].model_validate(result['arguments']);_schema(args,settings)
    if result['operation']=='export_postgres_to_csv':
        from .files import read_output
        data=read_output(Path(settings.project_root),args.target_path)
        parsed=csv.reader(io.StringIO(data.decode()),strict=True);header=next(parsed);digests=[]
        for row in parsed:
            checkpoint()
            if len(row)!=len(header):raise PostgresError('Export output is ragged')
            decoded=[None if v==args.null_token else v for v in row]
            digests.append(hashlib.sha256(json.dumps(decoded,ensure_ascii=False,separators=(',',':')).encode()).digest())
        checks={'output_sha256':hashlib.sha256(data).hexdigest()==result['output']['sha256'],'columns':header==args.columns,
            'row_count':len(digests)==result['row_count'],'semantic_values':hashlib.sha256(b''.join(sorted(digests))).hexdigest()==result['semantic_sha256']}
    else:
        current=inspect('inspect_postgres_table',{'target_schema':args.target_schema,'target_table':args.target_table,'preview_rows':0},settings)
        checks={'table_snapshot':current['table_sha256']==result['table_sha256'],'row_count':current['row_count']==result['row_count']}
        if result['operation']=='import_csv_to_postgres':
            if args.source_step:
                from .files import read_output
                source=result['sources'][0]
                checks['source_identity']=hashlib.sha256(read_output(Path(settings.project_root),source['path'])).hexdigest()==source['sha256']
            if args.path:
                data,_=_input(args,settings,{})
                checks['source_identity']=hashlib.sha256(data).hexdigest()==result['sources'][0]['sha256']
    return {'passed':all(checks.values()),'checks':checks,'row_count':result['row_count'],'target':args.target_schema+'.'+args.target_table,'committed':result['committed'],'workflow_executed':True}
