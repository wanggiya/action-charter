import {dataCardSchema} from '../lib/data-card';

const display=(value:unknown)=>value==null?'Not recorded':typeof value==='number'?value.toLocaleString(undefined,{maximumFractionDigits:5}):String(value).replaceAll('_',' ');

/** Recorded facts only; mounting or expanding never fetches data or calls a model. */
export function DataCard({value}:{value:unknown}) {
  const parsed=dataCardSchema.safeParse(value);
  if(!parsed.success)return null;
  const card=parsed.data;
  return <section className="data-card discovery-status" aria-label="Data Card">
    <strong>Data Card · {card.scope==='sample'?'Preliminary sample':card.scope==='driver_metadata'?'Driver metadata':'Recorded inspection'}</strong>
    <p className="data-card-source">{card.source}</p>
    <dl className="result-summary-facts">
      <div><dt>Scope</dt><dd>{display(card.scope)}</dd></div>
      {card.kind==='table'?<><div><dt>Source rows</dt><dd>{display(card.source_rows)}</dd></div><div><dt>Profile rows</dt><dd>{display(card.profile_rows)}</dd></div><div><dt>Fields</dt><dd>{display(card.field_count)}</dd></div></>:<><div><dt>Layers</dt><dd>{display(card.layer_count)}</dd></div><div><dt>Raster size</dt><dd>{card.width==null?'Not recorded':`${display(card.width)} × ${display(card.height)}`}</dd></div><div><dt>Bands</dt><dd>{display(card.band_count)}</dd></div></>}
      <div><dt>Identity</dt><dd>{display(card.identity_basis)}</dd></div>
    </dl>
    {card.fields.length>0&&<details><summary>Field facts · {card.fields.length} shown{card.fields_omitted?` · ${card.fields_omitted} omitted`:''}</summary><div className="data-card-table"><table><thead><tr><th>Field</th><th>Type / candidate role</th><th>Missing</th><th>Distinct</th><th>Mean</th><th>Min / max</th></tr></thead><tbody>{card.fields.map(field=><tr key={field.name}><th scope="row">{field.name}</th><td>{display(field.observed_type??field.storage_type)}<br/>{display(field.candidate_role)}</td><td>{display(field.missing_count)}</td><td>{display(field.distinct_count)}</td><td>{display(field.mean)}</td><td>{display(field.minimum)} / {display(field.maximum)}</td></tr>)}</tbody></table></div></details>}
    <details><summary>Identity, selection and quality scope</summary><p>SHA-256: {card.source_sha256??'Pending / not recorded'}</p><p>Missingness: {display(card.missingness)} · excess duplicate rows: {display(card.excess_duplicate_rows)}</p><pre>{JSON.stringify(card.selection,null,2)}</pre></details>
    <small>Saved facts identify the recorded read; current file freshness is not checked. Unknown is not zero. Roles are candidates. No execution authority.</small>
  </section>;
}
