import { Children, isValidElement, useState, useEffect, useRef, type ReactNode } from "react";
type Option={value:string;children:ReactNode;disabled?:boolean};
export function GraphSourcePicker({value,disabled,onSelect,children}:{value:string;disabled:boolean;onSelect:(value:string)=>void;children:ReactNode}) {
 const [open,setOpen]=useState(false);
 const container=useRef<HTMLDivElement>(null);
 useEffect(()=>{if(!open)return;const close=(event:PointerEvent)=>{if(event.target instanceof Node&&!container.current?.contains(event.target))setOpen(false);};document.addEventListener('pointerdown',close);return()=>document.removeEventListener('pointerdown',close);},[open]);
 const groups:{label:string;options:Option[]}[]=[{label:'Current workflows',options:[]}];
 Children.forEach(children,child=>{if(!isValidElement(child))return;if(child.type==='optgroup'){const props=child.props as {label:string;children:ReactNode};const options:Option[]=[];Children.forEach(props.children,item=>{if(isValidElement(item))options.push(item.props as Option);});groups.push({label:props.label,options});}else if(child.type==='option')groups[0].options.push(child.props as Option);});
 const selected=groups.flatMap(group=>group.options).find(option=>option.value===value);
 return <div ref={container} className="graph-source-disclosure" onKeyDown={event=>{if(event.key==='Escape')setOpen(false);}}><button type="button" aria-label="Graph to view" aria-expanded={open} disabled={disabled} onClick={()=>setOpen(!open)}>{selected?.children??'Select workflow'}</button>{open&&<div className="graph-source-options" aria-label="Workflow sources">{groups.map(group=><details key={group.label} open={group.label==='Current workflows'}><summary>{group.label} · {group.options.length}</summary>{group.options.map(option=><button type="button" key={option.value} disabled={option.disabled} aria-pressed={value===option.value} onClick={()=>{onSelect(option.value);setOpen(false);}}>{option.children}</button>)}</details>)}</div>}</div>
}
