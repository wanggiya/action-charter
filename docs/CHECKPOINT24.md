"""Exercise real frontend dependency edits, including deletion and cycle guards."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_operation_edits_preserve_dependencies_and_reject_cycles():
    if not shutil.which('node') or not (ROOT / 'interface/node_modules/vite').exists():
        pytest.skip('Installed frontend dependencies required for operation-graph integration')
    code = r'''
import {transformWithEsbuild} from 'vite';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const source = await readFile('src/lib/operation-graph.ts', 'utf8');
const transformed = await transformWithEsbuild(source, 'operation-graph.ts', {loader:'ts', target:'es2022'});
const graph = await import('data:text/javascript;base64,' + Buffer.from(transformed.code).toString('base64'));
const original = {plan:{steps:[{step_id:'step_1'},{step_id:'step_2'},{step_id:'step_3'}]}};
assert.deepEqual(graph.operationDependencies(original.plan.steps), {step_1:[],step_2:['step_1'],step_3:['step_2']});
assert.equal(graph.canConnectOperations(original.plan.steps,'step_2','step_1'),false);
assert.equal(graph.canConnectOperations(original.plan.steps,'step_1','step_2'),false);
assert.equal(graph.canConnectOperations(original.plan.steps,'step_1','step_99'),false);
assert.equal(graph.canConnectOperations(original.plan.steps,'step_1','step_1'),false);
const disconnected = graph.disconnectOperations(original,'step_2','step_3');
assert.deepEqual(disconnected.plan.steps[2].depends_on,[]);
assert.equal(graph.canConnectOperations(disconnected.plan.steps,'step_1','step_3'),true);
const connected = graph.connectOperations(disconnected,'step_1','step_3');
assert.deepEqual(connected.plan.steps[2].depends_on,['step_1']);
assert.throws(() => graph.connectOperations(connected,'step_3','step_1'), /cycle/);
const renamed = graph.deleteOperation(connected,'step_2');
assert.deepEqual(renamed.plan.steps.map(s=>s.step_id),['step_1','step_2']);
assert.deepEqual(renamed.plan.steps[1].depends_on,['step_1']);
const lostParent = graph.deleteOperation(original,'step_2');
assert.deepEqual(lostParent.plan.steps[1].depends_on,[]);
assert.equal(original.plan.steps[2].depends_on,undefined);
const tables = {plan:{steps:[
 {step_id:'step_1',arguments:{}},
 {step_id:'step_2',arguments:{path:'data/input/a.csv'}},
 {step_id:'step_3',arguments:{source_step:'step_2'}},
 {step_id:'step_4',arguments:{source_step:'step_3',right_step:'step_2'}}
]}};
const removedInspection = graph.deleteOperation(tables,'step_1');
assert.equal(removedInspection.plan.steps[1].arguments.source_step,'step_1');
assert.deepEqual(removedInspection.plan.steps[2].arguments,{source_step:'step_2',right_step:'step_1'});
const removedProducer = graph.deleteOperation(tables,'step_2');
assert.equal(removedProducer.plan.steps[1].arguments.source_step,'');
assert.equal(removedProducer.plan.steps[2].arguments.right_step,'');
assert.equal(removedProducer.plan.steps[2].arguments.source_step,'step_2');
assert.equal(tables.plan.steps[3].arguments.source_step,'step_3');
assert.throws(() => graph.deleteOperation({plan:{steps:[{step_id:'step_1'}]}},'step_1'), /at least one/);
const four = {plan:{steps:[{step_id:'step_1'},{step_id:'step_2'},{step_id:'step_3'},{step_id:'step_4'}]}};
assert.deepEqual(graph.pinConnections(four.plan.steps,'step_2','in'),[{from:'step_1',to:'step_2'}]);
assert.deepEqual(graph.breakPinConnections(four,'step_2','in').plan.steps[1].depends_on,[]);
assert.deepEqual(graph.breakPinConnections(four,'step_2','out').plan.steps[2].depends_on,[]);
const movedInput = graph.movePinConnections(four,'step_2','step_4','in');
assert.deepEqual(movedInput.plan.steps[1].depends_on,[]);
assert.deepEqual(movedInput.plan.steps[3].depends_on,['step_3','step_1']);
const movedOutput = graph.movePinConnections(four,'step_2','step_1','out');
assert.deepEqual(movedOutput.plan.steps[2].depends_on,['step_1']);
assert.equal(four.plan.steps[2].depends_on,undefined);
const fanout = {plan:{steps:[{step_id:'step_1',depends_on:[]},{step_id:'step_2',depends_on:['step_1']},{step_id:'step_3',depends_on:['step_1']}]}};
const unchanged = JSON.stringify(fanout);
assert.throws(() => graph.movePinConnections(fanout,'step_1','step_3','out'), /cycle/);
assert.equal(JSON.stringify(fanout),unchanged);
console.log('Frontend dependency edit invariants passed');
'''
    completed = subprocess.run(['node', '--input-type=module', '-e', code], cwd=ROOT / 'interface', capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    assert 'invariants passed' in completed.stdout


def test_planner_projection_displays_distinct_input_files_and_exact_references():
    code = r'''
import {transformWithEsbuild} from 'vite';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const app=await readFile('src/App.tsx','utf8');
const source=app.slice(app.indexOf('const plannerInputPaths ='),app.indexOf('const editedPlannerWorkflow ='));
const compiled=await transformWithEsbuild(source+'\nexport {plannerWorkflow,plannerReferenceFacts,withRecordedOutcome};','projection.ts',{loader:'ts'});
const stubs='const skillLabel=id=>id; const operationDependencies=steps=>Object.fromEntries(steps.map((s,i)=>[s.step_id,i?[steps[i-1].step_id]:[]]));\n';
const module=await import('data:text/javascript;base64,'+Buffer.from(stubs+compiled.code).toString('base64'));
const result={model:'fixture',original_request:'Join',plan:{steps:[
 {step_id:'step_1',skill:'inspect_csv',arguments:{path:'data/input/left.csv'},requires_approval:false,expected_artifacts:[]},
 {step_id:'step_2',skill:'join_csv',arguments:{path:'data/input/left.csv',right_path:'data/input/right.csv',target_path:'data/output/joined.csv'},requires_approval:true,expected_artifacts:[]}
]}};
const graph=module.plannerWorkflow(result);
assert.equal(graph.nodes.filter(n=>n.id.startsWith('planned_input_')).length,2);
assert.equal(graph.edges.filter(e=>e.label==='source file').length,3);
assert.deepEqual(module.plannerReferenceFacts(result,'planned_input_1'),[['Source path','data/input/right.csv']]);
assert(module.plannerReferenceFacts(result,'planned_step_2').some(([k,v])=>k==='Source path'&&v==='data/input/left.csv'));
assert(graph.nodes.filter(n=>n.id.startsWith('planned_input_')).every(n=>n.status==='pending'&&n.performedBy==='Not executed'));
assert.equal(module.withRecordedOutcome(graph,null),graph);
const completed=module.withRecordedOutcome(graph,{success:true,evidence:'recipe-evidence/fixture.json',steps:['planned_step_1','planned_step_2']});
assert.equal(completed.nodes.at(-1).id,'planned_outcome');
assert.equal(completed.nodes.at(-1).authority,'Recorded result only');
assert.deepEqual(completed.edges.filter(e=>e.to==='planned_outcome').map(e=>e.from),['planned_step_2']);
assert.equal(module.withRecordedOutcome({...graph,readOnly:false}, {success:true,evidence:'fixture',steps:[]}).nodes.length,graph.nodes.length);

'''
    completed=subprocess.run(['node','--input-type=module','-e',code],cwd=ROOT/'interface',capture_output=True,text=True)
    assert completed.returncode==0,completed.stderr


def test_saved_plan_restoration_resets_drafts_and_binds_exact_action_scope():
    code=r'''
import {transformWithEsbuild} from 'vite';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const app=await readFile('src/App.tsx','utf8');
const source=app.slice(app.indexOf('  const resumeSavedPlan = async'),app.indexOf('  const savePlannerPlan = async'));
const projection=app.slice(app.indexOf('const plannerInputPaths ='),app.indexOf('const editedPlannerWorkflow ='));
const setters=[...new Set(source.match(/set[A-Z][A-Za-z]+(?=\()/g))];
const stubs=`const calls={}; ${setters.map(name=>`const ${name}=value=>{calls['${name}']=value};`).join(' ')}
const skillLabel=id=>id; const operationDependencies=steps=>Object.fromEntries(steps.map((s,i)=>[s.step_id,i?[steps[i-1].step_id]:[]]));
const cancelNodeLayoutDrag=()=>{}; const window={sessionStorage:{removeItem:()=>{}}}; const requestAnimationFrame=fn=>fn(); const plannerRequestRef={current:null};
const readablePlannerRequest=value=>value; const preparePlannerApproval=async()=>({status:'prepared_not_recorded'});
`;
const compiled=await transformWithEsbuild(stubs+projection+source+'\nexport {resumeSavedPlan,calls,plannerInputPaths};','restore.ts',{loader:'ts'});
const module=await import('data:text/javascript;base64,'+Buffer.from(compiled.code).toString('base64'));
const item={plan_sha256:'a'.repeat(64),plan_filename:'saved.json',approvals:[],planner_result:{model:'fixture',original_request:'Inspect CSV',context_references:[],warnings:[],plan:{steps:[{step_id:'step_1',skill:'inspect_csv',purpose:'Inspect',arguments:{path:'sample_orders.csv'},requires_approval:false,validation_required:false,expected_artifacts:[]},{step_id:'step_2',skill:'select_csv_columns',purpose:'Select',arguments:{path:'data/input/sample_orders.csv',columns:['order_id'],target_path:'data/output/selected.csv'},requires_approval:true,validation_required:true,expected_artifacts:[]}]}}};
await module.resumeSavedPlan(item);
assert.equal(module.calls.setMode,'evidence');
assert.equal(module.calls.setDraft,null);assert.equal(module.calls.setEditedPlan,null);
assert.equal(module.calls.setWorkflowAuthorization,null);
assert.equal(module.calls.setGraphSelection,'live-plan');
assert.equal(module.calls.setSavedPlannerResult.plan_filename,item.plan_filename);
assert.equal(module.calls.setSavedPlannerResult.plan_sha256,item.plan_sha256);
assert.equal(module.calls.setSavedPlannerResult.approval_performed,false);
assert.equal(module.calls.setSavedPlannerResult.execution_performed,false);
assert.deepEqual(module.plannerInputPaths(item.planner_result),['data/input/sample_orders.csv']);
assert.equal(module.calls.setPlannerResult.plan.steps[0].arguments.path,'sample_orders.csv','Display grouping must not modify stored arguments');
assert.equal(module.calls.setWorkflow.nodes.filter(n=>n.id.startsWith('planned_input_')).length,1);
'''
    completed=subprocess.run(['node','--input-type=module','-e',code],cwd=ROOT/'interface',capture_output=True,text=True)
    assert completed.returncode==0,completed.stderr


def test_panel_drag_and_collapsible_source_groups_preserve_view_only_behavior():
    code=r'''
import React from 'react';
import {transformWithEsbuild} from 'vite';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
async function load(file,exports,hookState){
 let source=await readFile(file,'utf8');
 source=source.replace(/^import .* from "react";/m,'');
 const compiled=await transformWithEsbuild(source,'view.tsx',{loader:'tsx',jsx:'transform',jsxFactory:'React.createElement'});
 const prefix=`import React from ${JSON.stringify(import.meta.resolve('react'))}; const {Children,isValidElement}=React; const useRef=()=>({current:null}); const useEffect=()=>{}; const useState=()=>[${hookState},()=>{}];\n`;
 return import('data:text/javascript;base64,'+Buffer.from(prefix+compiled.code).toString('base64'));
}
const values=new Map(),stored=new Map();
globalThis.document={documentElement:{style:{setProperty:(k,v)=>values.set(k,v),getPropertyValue:k=>values.get(k)||''}},querySelector:()=>null};
globalThis.window={innerWidth:1600};globalThis.localStorage={getItem:k=>stored.get(k)??null,setItem:(k,v)=>stored.set(k,v)};
const resize=await load('src/components/PanelResize.tsx','PanelResize','false');
for(const side of ['planner','information']){
 const element=resize.PanelResize({side});const props=element.props;
 const target={parentElement:{getBoundingClientRect:()=>({width:300})},setPointerCapture:()=>{}};
 props.onPointerDown({preventDefault:()=>{},currentTarget:target,clientX:100,pointerId:1});
 props.onPointerMove({clientX:200});props.onPointerUp();
 assert.equal(values.get(side==='planner'?'--planner-panel-width':'--information-panel-width'),side==='planner'?'400px':'240px');
 assert.equal(props.role,'separator');
}
const sources=await load('src/components/GraphSourcePicker.tsx','GraphSourcePicker','true');
const selected=[];
const element=sources.GraphSourcePicker({value:'plan:a',disabled:false,onSelect:key=>selected.push(key),children:[React.createElement('option',{value:'default'},'Default'),...['Saved plans','Saved recipes','Durable runs'].map((label,i)=>React.createElement('optgroup',{label},React.createElement('option',{value:['plan:a','recipe:b','run:c'][i]},label+' fixture')))]});
const groups=element.props.children[1].props.children;
assert.equal(groups.length,4);
assert(groups.slice(1).every(group=>group.type==='details'&&!group.props.open));
groups[1].props.children[1][0].props.onClick();
assert.deepEqual(selected,['plan:a']);
'''
    completed=subprocess.run(['node','--input-type=module','-e',code],cwd=ROOT/'interface',capture_output=True,text=True)
    assert completed.returncode==0,completed.stderr

Startup now loads saved source lists immediately. If no plan or draft is open, conversation recovery opens the remembered saved revision, falling back to its existing saved conversation proposal if the remembered artifact is absent. It never guesses an unrelated newest plan, saves a new artifact, calls the model, approves or runs operations. The graph selector uses larger labels and options. To accept this change, reload without clicking Open conversation plan: expect the saved workflow and source groups to appear automatically, with no new execution attempt. Existing drafts/open plans and changed conversation identity block stale recovery.
