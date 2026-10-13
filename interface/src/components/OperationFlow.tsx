import { ArrowRight } from "lucide-react";
import { skillLabel } from "../lib/skill-labels";
type Props={stepId:string;skill:string;arguments?:Record<string,unknown>;dependsOn?:string[]|null;outcome?:unknown};
export function OperationFlow({stepId,skill,arguments:args={},dependsOn,outcome}:Props){
 const result=outcome&&typeof outcome==='object'?outcome as Record<string,unknown>:{};
 const inputs=['path','right_path','source_step','right_step'].flatMap(key=>typeof args[key]==='string'&&args[key]?[`${key.replaceAll('_',' ')}: ${args[key]}`]:[]);
 const recordedSources=Array.isArray(result.sources)?result.sources.flatMap(source=>source&&typeof source==='object'&&typeof source.path==='string'?[source.path]:[]):[];
 const artifact=result.output&&typeof result.output==='object'?result.output as Record<string,unknown>:{};
 const output=typeof artifact.path==='string'?artifact.path:typeof args.target_path==='string'?args.target_path:typeof result.target_path==='string'?result.target_path:null;
 return <div className="operation-flow"><p className="operation-flow-order">{stepId.replace('step_','Step ')}{dependsOn&&` · After: ${dependsOn.join(', ')||'workflow start'}`}</p><div className="operation-flow-chain"><div className="operation-flow-card"><small>Input</small>{(inputs.length?inputs:recordedSources).length?(inputs.length?inputs:recordedSources).map((input,index)=><span key={`${index}:${input}`}>{input}</span>):<span>{typeof result.source_path==='string'?result.source_path:typeof result.path==='string'?result.path:'See bound input details'}</span>}</div><ArrowRight className="operation-flow-arrow" size={20} aria-label="Feeds operation"/><div className="operation-flow-card"><small>Operation</small><strong>{skillLabel(skill)}</strong></div><ArrowRight className="operation-flow-arrow" size={20} aria-label="Produces result"/><div className="operation-flow-card"><small>{outcome?'Recorded result':'Planned result'}</small><span>{output??'Inspection / operation result'}</span></div></div></div>;
}
