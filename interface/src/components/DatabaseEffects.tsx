import {CircleAlert,Database} from 'lucide-react';
const names:Record<string,string>={discover_postgres_tables:'Discover tables',inspect_postgres_table:'Inspect all records',import_csv_to_postgres:'Create a new table from CSV',export_postgres_to_csv:'Create a CSV from the table',soft_delete_postgres_rows:'Mark selected records as deleted',restore_postgres_rows:'Restore selected records'};
export function DatabaseEffects({skill,arguments:args,effects}:{skill:string;arguments:Record<string,unknown>;effects?:Record<string,unknown>}){
 if(!names[skill])return null;
 const read=skill==='discover_postgres_tables'||skill==='inspect_postgres_table';
 const connection=effects?.connection&&typeof effects.connection==='object'?effects.connection as Record<string,unknown>:null;
 return <section className="database-effects" aria-label="Database effect review"><h4>{read?<Database size={15}/>:<CircleAlert size={15}/>} {names[skill]}</h4><dl>
  <div><dt>Connection</dt><dd>{connection?`${connection.host}:${connection.port} / ${connection.database}`:'Configured PostgreSQL profile'}</dd></div>
  <div><dt>Target</dt><dd>{String(args.target_schema)}{args.target_table?`.${String(args.target_table)}`:''}</dd></div>
  {skill==='import_csv_to_postgres'&&<><div><dt>Behavior</dt><dd>New table only · existing table rejects</dd></div><div><dt>Mapping</dt><dd>{Array.isArray(args.columns)?args.columns.length:0} explicitly typed columns</dd></div>{args.soft_delete_marker!=null&&<div><dt>New deletion marker</dt><dd>{String(args.soft_delete_marker)} · boolean · NOT NULL · default false</dd></div>}<div><dt>Recovery</dt><dd>Atomic transaction; inspect actual target if commit is unconfirmed.</dd></div></>}
  {skill==='export_postgres_to_csv'&&<><div><dt>New file</dt><dd>{String(args.target_path)}</dd></div><div><dt>Null encoding</dt><dd>{String(args.null_token??'\\N')}</dd></div><div><dt>Database</dt><dd>Rows remain unchanged; export includes marked records.</dd></div></>}
  {(skill==='soft_delete_postgres_rows'||skill==='restore_postgres_rows')&&<><div><dt>Exact rows</dt><dd>{String(args.expected_affected_rows)} · selected by {String(args.key_column)}</dd></div><div><dt>Change</dt><dd>{String(args.deleted_column??'is_deleted')} = {skill==='soft_delete_postgres_rows'?'true':'false'}</dd></div><div><dt>Precondition</dt><dd>Exact snapshot and opposite marker state must still match.</dd></div></>}
 </dl><p>{read?'Read-only. Includes records marked as deleted.':'Allow writes enables availability. Authorization covers only this reviewed scope; execution remains a separate action.'}</p><details><summary>Exact keys, mappings and snapshot conditions</summary><pre>{JSON.stringify(args,null,2)}</pre></details></section>;
}
