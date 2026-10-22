import type {ReactNode} from 'react';

const object=(value:unknown):Record<string,unknown>=>value&&typeof value==='object'&&!Array.isArray(value)?value as Record<string,unknown>:{};
const shown=(value:unknown):string=>value===null||value===undefined?'Not recorded':Array.isArray(value)?value.map(shown).join(' × '):String(value);
function Facts({items}:{items:[string,ReactNode][]}) {
  return <dl className="raster-metadata-facts">{items.map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>;
}
function Tags({value}:{value:unknown}) {
  const entries=Object.entries(object(value));
  return entries.length?<Facts items={entries.map(([key,value])=>[key,shown(value)])}/>:<p>No tags recorded in this namespace.</p>;
}

/** Presentation of recorded metadata only; expansion never rereads the dataset. */
export function RasterMetadata({outcome}:{outcome:Record<string,unknown>}) {
  const technical=object(outcome.technical_details),bounds=object(outcome.bounds);
  const types=Array.isArray(outcome.data_types)?outcome.data_types:[];
  const nodata=Array.isArray(outcome.nodata_values)?outcome.nodata_values:[];
  const encodings=Array.isArray(outcome.nodata_encodings)?outcome.nodata_encodings:[];
  const noData=(index:number)=>shown(encodings[index]??nodata[index]);
  return <section className="raster-metadata" aria-label="Raster characteristics">
    <Facts items={[
      ['Driver',shown(outcome.driver)],['Dimensions',`${shown(outcome.width)} × ${shown(outcome.height)}`],
      ['Bands',shown(outcome.band_count)],['Declared CRS',shown(outcome.crs)],
      ['Resolution',shown(outcome.resolution)],['Data types',[...new Set(types)].join(', ')||'Not recorded'],
      ['Extent (source CRS)',Object.keys(bounds).length?['left','bottom','right','top'].map(key=>`${key}: ${shown(bounds[key])}`).join(' · '):'Not recorded'],
      ['NoData',nodata.length?[...new Set(nodata.map((_,i)=>noData(i)))].join(', '):'Not recorded'],
    ]}/>
    <details className="raster-technical-details"><summary>Raster technical details</summary>
      <p>Recorded driver metadata only. Saved statistics tags can be stale; no statistics or histogram was computed. Overview dimensions below describe band 1; per-band overview lists are decimation factors.</p>
      <Facts items={[
        ['Affine transform (a, b, c, d, e, f)',Array.isArray(outcome.transform)?outcome.transform.join(', '):'Not recorded'],
        ['Storage layout',typeof technical.tiled==='boolean'?(technical.tiled?'Tiled':'Stripped'):'Not recorded'],
        ['Compression',shown(technical.compression)],['Interleave',shown(technical.interleave)],
        ['Band 1 overview dimensions',Array.isArray(technical.overview_dimensions)&&technical.overview_dimensions.length?technical.overview_dimensions.map(value=>{const overview=object(value);return `${shown(overview.width)} × ${shown(overview.height)} (${shown(overview.factor)}×)`;}).join(', '):'None recorded'],
      ]}/>
      <details><summary>Coordinate reference system · WKT</summary><pre>{shown(technical.crs_wkt)}</pre></details>
      <details><summary>Dataset metadata tags</summary>{Object.entries(object(technical.metadata)).map(([namespace,value])=><section key={namespace}><h4>{namespace==='default'?'Default namespace':namespace}</h4><Tags value={value}/></section>)}</details>
      {Array.isArray(technical.bands)&&technical.bands.map(value=>{const band=object(value),index=Number(band.band)-1;return <details key={String(band.band)}><summary>Band {String(band.band)} · {shown(types[index])} · {shown(band.color_interpretation)}</summary><Facts items={[
        ['Data type',shown(types[index])],['NoData',noData(index)],['Description',shown(band.description)],
        ['Block size (rows × columns)',shown(band.block_shape)],['Color interpretation',shown(band.color_interpretation)],
        ['Unit',shown(band.unit)],['Scale',shown(band.scale)],['Offset',shown(band.offset)],
        ['Overview factors',Array.isArray(band.overview_levels)&&band.overview_levels.length?band.overview_levels.join(', '):'None recorded'],
      ]}/><Tags value={band.metadata}/></details>;})}
      {!Array.isArray(technical.bands)&&<p>Additional technical metadata was not recorded for this result. A new inspection is required to collect it; opening this section does not run one.</p>}
      {Boolean(technical.bands_truncated)&&<p>Band details are limited to the first recorded bands by the metadata budget. Total band count and data types remain above.</p>}
      {Boolean(technical.metadata_truncated)&&<p>Some metadata text or tags were shortened or omitted to keep the result bounded.</p>}
    </details>
  </section>;
}
