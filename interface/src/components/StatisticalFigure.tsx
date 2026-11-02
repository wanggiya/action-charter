import {useState} from 'react';
import type {StatisticalFigure as Figure} from '../lib/statistical-figures';
export function StatisticalFigure({figure}:{figure:Figure}){
 const [selected,setSelected]=useState<number|null>(null);
 const choose=(target:EventTarget|null)=>{const mark=target instanceof Element?target.closest('[data-mark]'):null;setSelected(mark?Number(mark.getAttribute('data-mark')):null);};
 return <figure className="statistical-figure" aria-label={figure.title} tabIndex={0} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget))setSelected(null);}} onClick={e=>{e.currentTarget.focus();choose(e.target);}} onKeyDown={e=>{if(e.key==='Escape')setSelected(null);if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(e.target);}}}>
  <div className="statistical-svg" dangerouslySetInnerHTML={{__html:figure.svg}}/>
  <figcaption>{figure.caption}</figcaption>{selected!==null&&figure.marks[selected]&&<p role="status">{figure.marks[selected].detail}</p>}
 </figure>;
}
