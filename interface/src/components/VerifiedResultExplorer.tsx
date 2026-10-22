import {useEffect,useState} from 'react';
import {defaultExplorationQuery,type ExplorationQuery,type ExplorationResult} from '../lib/result-exploration';

export function VerifiedResultExplorer({data,busy,error,onLoad}:{data:ExplorationResult|null;busy:boolean;error:string;onLoad:(query:ExplorationQuery)=>void}){
  const [draft,setDraft]=useState<ExplorationQuery>(defaultExplorationQuery);
  const [previous,setPrevious]=useState<number[]>([]);
  useEffect(()=>{if(data)setDraft(data.query);},[data]);
  const profiles=data?.column_profiles??[];
  const filter=draft.filters[0];
  const modifyFilter=(patch:Partial<NonNullable<typeof filter>>)=>setDraft(value=>({...value,offset:0,filters:[{...(value.filters.length?value.filters[0]:{column:profiles[0]?.name??'',operator:'eq' as const,value:'',value_type:'text' as const}),...patch}]}));
  return <section className="verified-result-explorer" aria-label="Complete CSV exploration">
    <p>{data?`${data.matched_row_count} matching / ${data.row_count} recorded rows · ${data.preview.length} rows in this page`:'Read and verify the recorded CSV to explore beyond the saved preview.'}</p>
    <small>Filters and sorting apply to the complete bounded artifact. No workflow is executed and no data is modified.</small>
    {data&&<>
      <details><summary>Column profiles · complete verified source</summary><div className="result-table-scroll"><table><thead><tr><th>Column</th><th>Observed values</th><th>Missing</th><th>Distinct</th></tr></thead><tbody>{profiles.map(profile=><tr key={profile.name}><th>{profile.name}</th><td>{profile.observed_type}</td><td>{profile.missing_count}</td><td>{profile.distinct_count}</td></tr>)}</tbody></table></div><small>Stored values remain strings. Numeric compatibility is observed, not an inferred unit or domain meaning. Profiles cover the source before filtering.</small></details>
      <details><summary>Filter and sort complete CSV</summary>
        <div className="visualization-controls"><label>Filter column<select aria-label="Complete CSV filter column" value={filter?.column??''} onChange={event=>event.target.value?modifyFilter({column:event.target.value}):setDraft(value=>({...value,offset:0,filters:[]}))}><option value="">No filter</option>{profiles.map(profile=><option key={profile.name}>{profile.name}</option>)}</select></label>
          <label>Condition<select aria-label="Complete CSV filter condition" disabled={!filter} value={filter?.operator??'eq'} onChange={event=>modifyFilter({operator:event.target.value as NonNullable<typeof filter>['operator'],value:['is_missing','not_missing'].includes(event.target.value)?null:''})}>{['eq','ne','gt','ge','lt','le','contains','is_missing','not_missing'].map(value=><option key={value}>{value}</option>)}</select></label>
          <label>Compare as<select aria-label="Complete CSV filter type" disabled={!filter||filter.operator==='contains'} value={filter?.value_type??'text'} onChange={event=>modifyFilter({value_type:event.target.value as 'text'|'number'})}><option value="text">Text</option><option value="number">Number</option></select></label>
          <label>Value<input aria-label="Complete CSV filter value" maxLength={160} disabled={!filter||['is_missing','not_missing'].includes(filter.operator)} value={filter?.value??''} onChange={event=>modifyFilter({value:event.target.value})}/></label>
          <label>Sort column<select aria-label="Complete CSV sort column" value={draft.sort?.column??''} onChange={event=>setDraft(value=>({...value,offset:0,sort:event.target.value?{column:event.target.value,descending:false,value_type:'text'}:null}))}><option value="">Original order</option>{profiles.map(profile=><option key={profile.name}>{profile.name}</option>)}</select></label>
          <label>Sort as<select aria-label="Complete CSV sort type" disabled={!draft.sort} value={draft.sort?.value_type??'text'} onChange={event=>setDraft(value=>({...value,offset:0,sort:value.sort?{...value.sort,value_type:event.target.value as 'text'|'number'}:null}))}><option value="text">Text</option><option value="number">Number</option></select></label>
          <label>Order<select aria-label="Complete CSV sort order" disabled={!draft.sort} value={draft.sort?.descending?'descending':'ascending'} onChange={event=>setDraft(value=>({...value,offset:0,sort:value.sort?{...value.sort,descending:event.target.value==='descending'}:null}))}><option value="ascending">Ascending</option><option value="descending">Descending</option></select></label>
        </div>
        {draft.filters.length>1&&<p>This Planner view has {draft.filters.length} combined filters. Editing the first filter replaces that list; Reset clears it.</p>}
        <div className="verified-preview-controls"><button disabled={busy} onClick={()=>{setPrevious([]);onLoad({...draft,offset:0});}}>Apply to complete CSV</button><button disabled={busy} onClick={()=>{setPrevious([]);onLoad(defaultExplorationQuery());}}>Reset complete CSV query</button></div>
      </details>
      <div className="result-pagination"><button disabled={busy||!previous.length} onClick={()=>{const offset=previous[previous.length-1];setPrevious(value=>value.slice(0,-1));onLoad({...data.query,offset});}}>Previous verified page</button><span>Matched rows {data.preview.length?data.offset+1:0}–{data.offset+data.preview.length} of {data.matched_row_count}</span><button disabled={busy||data.next_offset===null} onClick={()=>{setPrevious(value=>[...value,data.offset]);onLoad({...data.query,offset:data.next_offset!});}}>Next verified page</button></div>
      {data.cells_truncated&&<p>Some cell text is shortened to 160 characters; filtering and sorting use original values.</p>}
    </>}
    {busy&&<p role="status">Verifying source and computing the requested view…</p>}
    {error&&<p role="alert">{error} The saved snapshot remains available.</p>}
  </section>;
}
