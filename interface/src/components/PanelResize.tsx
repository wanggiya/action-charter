import { useEffect, useRef } from "react";
export function PanelResize({ side }: {side:"planner"|"information"|"results"}) {
  const drag=useRef<{x:number;width:number}|null>(null);
  const variable=side==="planner"?"--planner-panel-width":side==="results"?"--results-panel-width":"--information-panel-width";
  const key=`actioncharter:${side}-width`;
  const apply=(width:number)=>{const workspace=document.querySelector(".workspace");const other=document.querySelector(side==="planner"?".workspace > .inspector":".workspace.text-planner-open > .text-planner");const available=(workspace?.getBoundingClientRect().width??window.innerWidth)-(other?.getBoundingClientRect().width??0)-240;const next=Math.max(side==="results"?320:240,Math.min(width,side==="results"?1100:800,available));document.documentElement.style.setProperty(variable,`${next}px`);return next;};
  useEffect(()=>{try{const saved=Number(localStorage.getItem(key));if(saved>=240)apply(saved);}catch{/* Optional persistence. */}},[side]);
  const save=()=>{try{localStorage.setItem(key,document.documentElement.style.getPropertyValue(variable).replace('px',''));}catch{/* Optional persistence. */}};
  return <div className={`panel-resize-handle resize-${side}`} role="separator" aria-label={`Resize ${side} panel`} aria-orientation="vertical" title={`Drag to resize ${side}; use left/right arrow keys`} tabIndex={0}
    onPointerDown={event=>{event.preventDefault();const panel=event.currentTarget.parentElement;drag.current={x:event.clientX,width:panel?.getBoundingClientRect().width??320};event.currentTarget.setPointerCapture(event.pointerId);}}
    onPointerMove={event=>{if(drag.current)apply(drag.current.width+(event.clientX-drag.current.x)*(side==="planner"?1:-1));}}
    onPointerUp={()=>{drag.current=null;save();}} onPointerCancel={()=>{drag.current=null;}}
    onKeyDown={event=>{if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();apply((event.currentTarget.parentElement?.getBoundingClientRect().width??320)+(event.key==='ArrowRight'?20:-20)*(side==='planner'?1:-1));save();}}}/>
}
