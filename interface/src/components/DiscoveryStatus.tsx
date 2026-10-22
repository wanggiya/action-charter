import {RasterMetadata} from './RasterMetadata';
const object=(value:unknown):Record<string,unknown>=>value&&typeof value==='object'&&!Array.isArray(value)?value as Record<string,unknown>:{};

/** Shared progress presentation; preliminary facts never imply verification. */
export function DiscoveryStatus({outcome,runStatus,detailed=true}:{outcome:Record<string,unknown>;runStatus:string;detailed?:boolean}) {
  const discovery=object(outcome.discovery);
  if(!['csv-discovery-v1','spatial-discovery-v1'].includes(String(discovery.schema_version)))return null;
  const pending=discovery.phase==='verifying',spatial=discovery.schema_version==='spatial-discovery-v1';
  const stopped=pending&&!['queued','running','cancelling'].includes(runStatus);
  const large=Number(discovery.file_bytes)>8*1024*1024||Number(outcome.row_count)>10000;
  return <section className="discovery-status" role="status">
    <strong>{pending?(stopped?'Characteristics saved · verification incomplete':'Characteristics ready · verifying full file…'):spatial?'Spatial metadata · package SHA-256 recorded':'Complete CSV scan · SHA-256 recorded'}</strong>
    <p>{(Number(discovery.file_bytes)/1048576).toFixed(2)} MiB · {spatial?`${String(outcome.driver)} · metadata only`:`${String(outcome.column_count)} columns · ${pending?'Exact row count pending':`${String(outcome.row_count)} rows`}`}</p>
    {pending&&<p>Shown values are preliminary; full-file verification has not finished.</p>}
    {spatial&&detailed&&<>
      <p>Counts and extents are available driver metadata. Unavailable counts are not zero. Hash completion does not validate all geometries or pixels.</p>
      {outcome.width!==undefined&&<RasterMetadata outcome={outcome}/>}
      {Array.isArray(outcome.layers)&&outcome.layers.map((value,index)=>{const layer=object(value);return <details key={index}><summary>{String(layer.name)} · {layer.feature_count===null?'Count not computed':`${String(layer.feature_count)} features (driver metadata)`}</summary><p>{String(layer.geometry_type)} · {String(layer.crs??'CRS not recorded')}</p><p>{Array.isArray(layer.fields)?layer.fields.map(value=>{const field=object(value);return `${String(field.name)} (${String(field.type)})`;}).join(', '):'No recorded fields'}</p>{Boolean(layer.fields_truncated)&&<p>Field list is truncated.</p>}</details>;})}
    </>}
    {large&&detailed&&<p>{spatial?'Large-file geometry/pixel display and processing retain separate limits. Use these characteristics without rendering every feature or pixel.':'This is a bounded preview. Complete filtering and transformations retain their separate 8 MiB / 10,000-row limits.'}</p>}
  </section>;
}
