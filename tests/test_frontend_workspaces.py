"""P0-6 store and workspace ownership regressions; no model or live services."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).parents[1]


def node(code):
    result = subprocess.run(['node', '--input-type=module', '-e', code], cwd=ROOT/'interface', capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stderr


def test_workspace_store_updates_batches_and_isolation():
    node(r'''
import {readFile} from 'node:fs/promises';
import {transformWithEsbuild} from 'vite';
import assert from 'node:assert/strict';
const compiled=await transformWithEsbuild(await readFile('src/workspaces/store.ts','utf8'),'store.ts',{loader:'ts'});
const {createStore,batchActions}=await import('data:text/javascript;base64,'+Buffer.from(compiled.code).toString('base64'));
let initialized=0;
const first=createStore(()=>{initialized++;return {chat:'A',plan:'plan-A',run:'run-A',review:'review-A',authorization:'approval-A',count:0};});
const other=createStore(()=>({chat:'B',plan:null,run:null,review:null,authorization:null,count:0}));
assert.equal(initialized,1);
const initial=first.getSnapshot();
const observed=[];const unsubscribe=first.subscribe(()=>observed.push({...first.getSnapshot()}));
first.set('chat','A');assert.equal(first.getSnapshot(),initial);assert.equal(observed.length,0);
first.set('count',n=>n+1);first.set('count',n=>n+1);assert.equal(first.getSnapshot().count,2);
assert.equal(initial.count,0,'Prior snapshots must not be mutated');
observed.length=0;
first.batch(()=>{
 first.set('chat','C');first.set('plan',null);
 first.batch(()=>{first.set('run',null);first.set('review',null);first.set('authorization',null);});
});
assert.equal(observed.length,1);assert.deepEqual(observed[0],{chat:'C',plan:null,run:null,review:null,authorization:null,count:2});
assert.equal(other.getSnapshot().chat,'B');assert.equal(other.getSnapshot().count,0,'Providers cannot share state');
observed.length=0;
const actions=batchActions({change(){first.set('plan','new');first.set('run','new-run');return 'done';}},first.batch);
assert.equal(actions.change(),'done');assert.equal(observed.length,1);
unsubscribe();first.set('count',3);assert.equal(observed.length,1);
assert.throws(()=>first.batch(()=>{first.set('count',4);throw Error('UI transition failed');}),/UI transition failed/);
let notified=0;first.subscribe(()=>notified++);first.set('count',5);assert.equal(notified,1,'Batch bookkeeping must recover after errors');
''')


def test_workspace_defaults_do_not_restore_authority_or_dispatch():
    node(r'''
import {readFile} from 'node:fs/promises';
import {transformWithEsbuild} from 'vite';
import ts from 'typescript';
import assert from 'node:assert/strict';
const source=await readFile('src/workspaces/state.ts','utf8');
const file=ts.createSourceFile('state.ts',source,ts.ScriptTarget.Latest,true);
const body=file.statements.filter(s=>!ts.isImportDeclaration(s)).map(s=>s.getText(file)).join(String.fromCharCode(10));
const stubs="const loadAppearance=()=>({buttonStyle:'outline',filledText:'white'});const currentChatId=()=>'chat-A';const demoWorkflow={id:'fixture',readOnly:true,nodes:[],edges:[]};";
const compiled=await transformWithEsbuild(stubs+body,'state.ts',{loader:'ts'});
const {createWorkspaceState,setterKeys}=await import('data:text/javascript;base64,'+Buffer.from(compiled.code).toString('base64'));
const previous=globalThis.fetch;let calls=0;globalThis.fetch=()=>{calls++;throw Error('Store must not call API');};
try{
 const state=createWorkspaceState();
 assert.equal(state.conversationId,'chat-A');
 for(const key of ['plannerResult','savedPlannerResult','editedPlan','workflowReview','workflowAuthorization','workflowRun','currentInspection','historicalRecord'])assert.equal(state[key],null,key);
 assert.equal(state.graphSelection,'default');assert.equal(state.outcomeOpen,false);
 assert.equal(setterKeys.setWorkflowBusy,'executionWorkflowBusy');
 assert.equal(setterKeys.setConversationId,'conversationId');
 assert.equal(calls,0);
}finally{globalThis.fetch=previous;}
''')


def test_app_is_composition_and_workspaces_keep_their_owners():
    node(r'''
import {readFile} from 'node:fs/promises';
import ts from 'typescript';
import assert from 'node:assert/strict';
const app=await readFile('src/App.tsx','utf8');
assert(app.split(String.fromCharCode(10)).length<100,'App should compose workspaces rather than own their implementation');
for(const name of ['WorkspaceStoreProvider','PlannerWorkspace','GraphWorkspace','ResultsWorkspacePanel','SettingsWorkspace'])assert(app.includes(name));
assert(!app.includes('useState')&&!app.includes('fetch('));
const graph=await readFile('src/workspaces/createGraphActions.ts','utf8');
for(const name of ['startNodeDrag','moveNode','endNodeDrag','startConnectionDrag','endConnectionDrag','validateEdits'])assert(graph.includes(name));
const results=await readFile('src/workspaces/createResultsActions.ts','utf8');
for(const name of ['authorizeReviewedWorkflow','executeReviewedWorkflow','acceptSubmittedInspection'])assert(results.includes(name));
const effects=await readFile('src/workspaces/useWorkspaceEffects.ts','utf8');
assert(effects.includes('setWorkflowAuthorization(null)'));
const planner=await readFile('src/workspaces/PlannerWorkspace.tsx','utf8');
assert(planner.includes('onConversationChange={setConversationId}'));
assert(planner.includes('batchWorkspace(() =>'));
const store=await readFile('src/workspaces/store.ts','utf8');
for(const forbidden of ['localStorage','sessionStorage','fetch(','authorizeCurrentWorkflow','executeCurrentWorkflow'])assert(!store.includes(forbidden));
for(const file of ['WorkspaceStore.tsx','useWorkspaceBindings.ts','useWorkspaceModel.ts']){
 const text=await readFile('src/workspaces/'+file,'utf8');
 const ast=ts.createSourceFile(file,text,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
 assert.equal(ast.parseDiagnostics.length,0,file);
}
''')
