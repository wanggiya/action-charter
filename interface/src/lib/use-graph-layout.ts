import {useEffect,useMemo,useState,type SetStateAction} from 'react';
import type {Workflow} from './workflow';
type Position={x:number;y:number};
type Positions=Record<string,Position>;
const valid=(v:unknown):v is Position=>!!v&&typeof v==='object'&&['x','y'].every(key=>typeof (v as Position)[key as keyof Position]==='number'&&Number.isFinite((v as Position)[key as keyof Position])&&(v as Position)[key as keyof Position]>=0&&(v as Position)[key as keyof Position]<=16000);
export function freePosition(position:Position,occupied:Position[],horizontal:boolean):Position {
 const width=horizontal?218:112/.72+28,height=horizontal?140:190/1.25+28;
 const collides=(p:Position)=>occupied.some(other=>Math.abs(other.x-p.x)<width&&Math.abs(other.y-p.y)<height);
 const origin={x:Math.min(16000,Math.max(0,position.x)),y:Math.min(16000,Math.max(0,position.y))};
 if(!collides(origin))return origin;
 for(let ring=1;ring<=200;ring++)for(const [dx,dy] of [[0,ring],[ring,0],[0,-ring],[-ring,0],[ring,ring],[-ring,ring]]){
  const next={x:origin.x+dx*width,y:origin.y+dy*height};
  if(next.x>=0&&next.y>=0&&next.x<=16000&&next.y<=16000&&!collides(next))return next;
 }
 return {x:origin.x+width*201,y:origin.y};
}
function read(scope:string):Positions {
 try{const value=JSON.parse(localStorage.getItem(`actioncharter:graph-layout:v1:${scope}`)??'{}');return Object.fromEntries(Object.entries(value).filter(([id,p])=>id.length<150&&valid(p)).slice(0,150)) as Positions;}catch{return {};}
}
/** Layout is presentation only; never copied into a plan, digest or authority. */
export function useGraphLayout(source:Workflow['nodes'],scope:string,horizontal:boolean){
 const [saved,setSaved]=useState<{scope:string;positions:Positions}>(()=>({scope,positions:read(scope)}));
 const positions=useMemo(()=>saved.scope===scope?saved.positions:read(scope),[saved,scope]);
 const resolved=useMemo(()=>{
  const placed:Positions=Object.create(null),occupied:Position[]=[];
  const positionOf=(id:string)=>Object.hasOwn(positions,id)?positions[id]:undefined;
  // Preserve established positions first; only new/unpositioned nodes seek space.
  for(const node of [...source.filter(n=>positionOf(n.id)),...source.filter(n=>!positionOf(n.id))]){
   const position=freePosition(positionOf(node.id)??node,occupied,horizontal);placed[node.id]=position;occupied.push(position);
  }
  return placed;
 },[source,positions,horizontal]);
 useEffect(()=>{
  const combined=Object.fromEntries(Object.entries({...positions,...resolved}).slice(-150));
  if(saved.scope===scope&&JSON.stringify(saved.positions)===JSON.stringify(combined))return;
  setSaved({scope,positions:combined});
  try{localStorage.setItem(`actioncharter:graph-layout:v1:${scope}`,JSON.stringify(combined));}catch{/* Layout remains usable without persistence. */}
 },[resolved,saved,scope,positions]);
 const setPositions=(action:SetStateAction<Positions>)=>{
  const next=typeof action==='function'?action(resolved):action;
  const combined=Object.fromEntries(Object.entries({...positions,...next}).slice(-150));
  setSaved({scope,positions:combined});
  try{localStorage.setItem(`actioncharter:graph-layout:v1:${scope}`,JSON.stringify(combined));}catch{/* Optional browser storage. */}
 };
 const nodes=source.map(node=>({...node,...resolved[node.id],...(!horizontal?{x:120+resolved[node.id].y*1.25,y:35+resolved[node.id].x*.72}:{})}));
 return {nodes,positions:resolved,setPositions};
}
