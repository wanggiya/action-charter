import { useEffect, useId, useRef, useState } from 'react';

type Expression = {kind:'column';name:string}|{kind:'number';value:number}|{kind:'binary'|'compare';operator:string;left:Expression;right:Expression}|{kind:'if';condition:Expression;then:Expression;otherwise:Expression};
type Calculation = {output_column:string;expression:Expression};
const number = ():Expression => ({kind:'number',value:0});
const defaults = (kind:string):Expression => kind==='column'?{kind:'column',name:''}:kind==='number'?number():kind==='if'?{kind:'if',condition:{kind:'compare',operator:'gt',left:{kind:'column',name:''},right:number()},then:number(),otherwise:number()}:{kind:kind as 'binary'|'compare',operator:kind==='binary'?'add':'gt',left:{kind:'column',name:''},right:number()};
const symbols:Record<string,string>={add:'+',subtract:'−',multiply:'×',divide:'÷',eq:'=',ne:'≠',gt:'>',ge:'≥',lt:'<',le:'≤'};

export function formulaText(value:unknown,depth=0):string {
  if(depth>8||!value||typeof value!=='object')return 'Invalid expression';
  const node=value as Record<string,unknown>;
  if(node.kind==='column')return String(node.name??'');
  if(node.kind==='number')return String(node.value??'');
  if(node.kind==='binary'||node.kind==='compare')return `(${formulaText(node.left,depth+1)} ${symbols[String(node.operator)]??'?'} ${formulaText(node.right,depth+1)})`;
  if(node.kind==='if')return `if ${formulaText(node.condition,depth+1)} then ${formulaText(node.then,depth+1)} otherwise ${formulaText(node.otherwise,depth+1)}`;
  return 'Invalid expression';
}

function NumberInput({value,onChange,onValidity,disabled}:{value:number;onChange:(value:number)=>void;onValidity:(id:string,valid:boolean)=>void;disabled:boolean}) {
  const id=useId();
  const [text,setText]=useState(String(value));
  const [invalid,setInvalid]=useState(false);
  const report=useRef(onValidity);report.current=onValidity;
  useEffect(()=>{setText(String(value));},[value]);
  useEffect(()=>()=>report.current(id,true),[id]);
  return <label>Number<input aria-label="Calculation number" aria-invalid={invalid} disabled={disabled} type="number" step="any" value={text} onChange={event=>{
    setText(event.target.value);
    const valid=event.target.value!==''&&Number.isFinite(event.target.valueAsNumber);
    setInvalid(!valid);onValidity(id,valid);
    if(valid)onChange(event.target.valueAsNumber);
  }}/>{invalid&&<small role="alert">Enter a finite number before saving.</small>}</label>;
}

function ExpressionEditor({value,onChange,onValidity,disabled,depth=1}:{value:Expression;onChange:(value:Expression)=>void;onValidity:(id:string,valid:boolean)=>void;disabled:boolean;depth?:number}) {
  const id=useId();
  return <fieldset className="calculation-expression" disabled={disabled}>
    <legend>Expression · level {depth}</legend>
    <label htmlFor={id}>Expression type</label><select id={id} value={value.kind} onChange={event=>onChange(defaults(event.target.value))}>
      <option value="column">Source column</option><option value="number">Number</option>
      {depth<8&&<><option value="binary">Arithmetic</option><option value="compare">Comparison</option>{depth<7&&<option value="if">Conditional</option>}</>}
    </select>
    {value.kind==='column'?<label>Column name<input aria-label="Calculation source column" value={value.name} maxLength={200} onChange={event=>onChange({...value,name:event.target.value})}/></label>:value.kind==='number'?<NumberInput value={value.value} disabled={disabled} onValidity={onValidity} onChange={number=>onChange({...value,value:number})}/>:value.kind==='if'?<>
      <div><strong>When</strong><ExpressionEditor value={value.condition} depth={depth+1} disabled={disabled} onValidity={onValidity} onChange={condition=>onChange({...value,condition})}/></div>
      <div><strong>Then</strong><ExpressionEditor value={value.then} depth={depth+1} disabled={disabled} onValidity={onValidity} onChange={then=>onChange({...value,then})}/></div>
      <div><strong>Otherwise</strong><ExpressionEditor value={value.otherwise} depth={depth+1} disabled={disabled} onValidity={onValidity} onChange={otherwise=>onChange({...value,otherwise})}/></div>
    </>:<>
      <label>Operator<select aria-label="Calculation operator" value={value.operator} onChange={event=>onChange({...value,operator:event.target.value})}>{(value.kind==='binary'?['add','subtract','multiply','divide']:['eq','ne','gt','ge','lt','le']).map(operator=><option key={operator} value={operator}>{symbols[operator]} · {operator}</option>)}</select></label>
      <div><strong>Left</strong><ExpressionEditor value={value.left} depth={depth+1} disabled={disabled} onValidity={onValidity} onChange={left=>onChange({...value,left})}/></div>
      <div><strong>Right</strong><ExpressionEditor value={value.right} depth={depth+1} disabled={disabled} onValidity={onValidity} onChange={right=>onChange({...value,right})}/></div>
    </>}
  </fieldset>;
}

export function CalculationSummary({arguments:args}:{arguments:Record<string,unknown>}) {
  const rows=Array.isArray(args.calculations)?args.calculations as Calculation[]:[];
  return <div className="calculation-summary"><p>Numeric calculations · missing values: {String(args.missing_policy??'not specified')} · division by zero fails.</p>{rows.map((row,index)=><p key={index}><strong>{row.output_column}</strong> = {formulaText(row.expression)}</p>)}{Array.isArray(args.assumptions)&&args.assumptions.map((text,index)=><p key={`assumption-${index}`}>Assumption: {String(text)}</p>)}</div>;
}

export function CalculationEditor({value,onValue,onValidity,disabled}:{value:unknown;onValue:(value:unknown)=>void;onValidity:(valid:boolean)=>void;disabled:boolean}) {
  const invalidFields=useRef(new Set<string>());
  const validity=useRef(onValidity);validity.current=onValidity;
  useEffect(()=>()=>validity.current(true),[]);
  const report=(id:string,valid:boolean)=>{if(valid)invalidFields.current.delete(id);else invalidFields.current.add(id);validity.current(invalidFields.current.size===0);};
  const rows=Array.isArray(value)?value as Calculation[]:[];
  const update=(index:number,row:Calculation)=>onValue(rows.map((current,i)=>i===index?row:current));
  return <div className="calculation-editor" role="group" aria-label="Calculated columns">
    <p>Use original numeric columns. New columns cannot replace existing ones. Validate edits before execution.</p>
    {rows.map((row,index)=><section key={index}><label>Output column<input aria-label="Calculation output column" disabled={disabled} value={row.output_column} maxLength={200} onChange={event=>update(index,{...row,output_column:event.target.value})}/></label>
      <p className="calculation-formula">{formulaText(row.expression)}</p>
      <ExpressionEditor value={row.expression} disabled={disabled} onValidity={report} onChange={expression=>update(index,{...row,expression})}/>
      <button type="button" disabled={disabled||rows.length===1} onClick={()=>onValue(rows.filter((_,i)=>i!==index))}>Remove calculation</button>
    </section>)}
    <button type="button" disabled={disabled||rows.length>=5} onClick={()=>onValue([...rows,{output_column:'',expression:defaults('column')}])}>Add calculated column</button>
  </div>;
}
