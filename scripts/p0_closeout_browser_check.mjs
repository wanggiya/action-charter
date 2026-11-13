// Real API + isolated stored fixtures; no live services, user records or model calls.
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,writeFile,mkdir,rm,rename} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve,dirname,extname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const repo=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-p0c-browser-'));
const state=resolve(root,'state');await mkdir(state);
await writeFile(resolve(root,'actioncharter.workspace.json'),JSON.stringify({version:1,state_root:state}));
const python=async(code,args=[])=>new Promise((done,reject)=>{
 const child=spawn(resolve(repo,'.venv/bin/python'),['-c',code,...args],{cwd:repo,env:{...process.env,PYTHONPATH:resolve(repo,'src')}});
 let out='',error='';child.stdout.on('data',v=>out+=v);child.stderr.on('data',v=>error+=v);
 child.on('error',reject);child.on('exit',status=>status===0?done(out):reject(new Error(error+out)));
});
await python('from pathlib import Path;import sys;from geoagent_harness.platform.project_identity import initialize;initialize(Path(sys.argv[1]),offline=True)',[root]);
process.env.PLAYWRIGHT_BROWSERS_PATH=resolve(repo,'interface/.playwright-browsers');
process.env.LD_LIBRARY_PATH=[resolve(repo,'interface/.browser-system-libs/runtime/usr/lib',process.arch==='arm64'?'aarch64-linux-gnu':'x86_64-linux-gnu'),process.env.LD_LIBRARY_PATH].filter(Boolean).join(':');
const {chromium}=await import(pathToFileURL(resolve(repo,'interface/node_modules/playwright/index.mjs')).href);
let apiPort,api,browser;const calls=[],errors=[];
const models=createServer((_req,res)=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify({models:[{name:'fixture:small',size:1}]}));});
await new Promise(done=>models.listen(0,'127.0.0.1',done));
const frontend=createServer(async(req,res)=>{try{
 if(req.url.startsWith('/api/')){
  const chunks=[];for await(const part of req)chunks.push(part);const body=Buffer.concat(chunks);
  calls.push({url:req.url,body:body.length?JSON.parse(body):null});
  const response=await fetch(`http://127.0.0.1:${apiPort}${req.url}`,{method:req.method,headers:{'Content-Type':'application/json'},...(req.method==='POST'?{body}:{})});
  res.writeHead(response.status,{'Content-Type':'application/json'});res.end(await response.text());return;
 }
 const pathname=new URL(req.url,'http://localhost').pathname;
 const path=pathname.startsWith('/assets/')?resolve(repo,'interface/dist','.'+pathname):resolve(repo,'interface/dist/index.html');
 res.setHeader('Content-Type',({'.js':'text/javascript','.css':'text/css','.html':'text/html'})[extname(path)]??'application/octet-stream');res.end(await readFile(path));
}catch(error){res.writeHead(500);res.end(String(error));}});
await new Promise(done=>frontend.listen(0,'127.0.0.1',done));
const origin=`http://127.0.0.1:${frontend.address().port}`;
try{
 api=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--planning-task-fixture'],{cwd:repo,env:{...process.env,PYTHONPATH:resolve(repo,'src'),MODEL_NAME:'fixture:small',MODEL_BASE_URL:`http://127.0.0.1:${models.address().port}/v1`,ENABLE_WRITE_TOOLS:'false',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',GEOSERVER_BASE_URL:'http://127.0.0.1:1',INTERFACE_FRONTEND_ORIGIN:origin}});
 let error='';api.stderr.on('data',v=>error+=v);
 apiPort=await new Promise((done,reject)=>{let out='';const timer=setTimeout(()=>reject(new Error(error)),20000);api.stdout.on('data',v=>{out+=v;if(out.includes('\n')){clearTimeout(timer);done(JSON.parse(out.split('\n')[0]).port);}});api.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exit ${code}: ${error}`));});});
 const files=JSON.parse(await python(`import json,sys
from pathlib import Path
from geoagent_harness.contracts.recipes import WorkflowRecipe
from geoagent_harness.core.ledger.recipe_storage import save_recipe
from geoagent_harness.platform.workspace import runtime_store_path
root=Path(sys.argv[1]);directory=runtime_store_path(root,'workflow-recipes');paths=[]
for identity,skill in [('inventory-valid','inspect_csv'),('inventory-invalid','inspect_vector')]:
 recipe=WorkflowRecipe(recipe_id=identity,summary='Inventory fixture',original_request='Read only; no execution',steps=[{'step_id':'step_1','skill_id':skill,'arguments':{'path':'data/input/sample_orders.csv'}}])
 _,path=save_recipe(recipe,recipe_root=directory);paths.append(str(path))
approvals=runtime_store_path(root,'approvals');approvals.mkdir(exist_ok=True);(approvals/'recipe-approval-malformed.json').write_text('{')
plans=runtime_store_path(root,'plans');plans.mkdir(exist_ok=True);(plans/('planner-plan.'+'a'*64+'.json')).write_text('{')
print(json.dumps(paths))`,[root]));
 const digest=async path=>createHash('sha256').update(await readFile(path)).digest('hex');
 const before=await Promise.all(files.map(digest));
 const response=await fetch(`http://127.0.0.1:${apiPort}/api/v1/recipes`);assert.equal(response.status,200);
 const inventory=await response.json();assert.equal(inventory.recipe_count,1);assert.equal(inventory.invalid_record_count,2);
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
 await page.goto(origin);await page.getByRole('button',{name:'Saved records',exact:true}).click();
 const records=page.getByRole('dialog',{name:'Saved records',exact:true});await records.waitFor();
 await records.getByText('inventory-valid',{exact:true}).waitFor();
 await records.getByText('No valid saved plans available. Review unavailable records above.',{exact:true}).waitFor();
 await records.getByLabel('Saved plans unavailable records',{exact:true}).waitFor();
 const blocked=records.getByLabel('Saved recipes unavailable records',{exact:true});
 await blocked.getByText(/inspect_vector requires/).waitFor();
 assert.equal(await blocked.getByRole('button').count(),0);
 assert.ok((await blocked.innerText()).includes('recipe-approval-malformed.json'));
 assert.equal(await blocked.evaluate(el=>{
  const heading=[...el.closest('[role="dialog"]').querySelectorAll('h3')].find(h=>h.textContent.startsWith('Saved plans'));
  return Boolean(el.compareDocumentPosition(heading)&Node.DOCUMENT_POSITION_FOLLOWING);
 }),true,'unavailable recipes must appear before the potentially long saved-plan list');
 const recordsBounds=await records.boundingBox(),warningBounds=await blocked.locator('summary').boundingBox();
 assert.ok(warningBounds.y>=recordsBounds.y&&warningBounds.y+warningBounds.height<recordsBounds.y+recordsBounds.height,'warning must be visible without scrolling through plans');
 await page.screenshot({path:'/tmp/actioncharter-p0c-saved-records.png'});

 await records.getByRole('button',{name:'Open recipe',exact:true}).click();
 const recipes=page.getByRole('dialog',{name:'Saved recipes',exact:true});await recipes.waitFor();
 await recipes.getByLabel('Saved recipes unavailable records',{exact:true}).getByText(/inspect_vector requires/).waitFor();
 assert.equal(await recipes.locator('.recipe-card').count(),1);
 const notice=recipes.getByLabel('Saved recipes unavailable records',{exact:true});
 const panelBounds=await recipes.boundingBox(),noticeBounds=await notice.boundingBox();
 const cardBounds=await recipes.locator('.recipe-card').boundingBox();
 assert.ok(noticeBounds.x>=panelBounds.x&&noticeBounds.x+noticeBounds.width<=panelBounds.x+panelBounds.width-10);
 assert.ok(cardBounds.x>=noticeBounds.x-1&&cardBounds.x+cardBounds.width<=panelBounds.x+panelBounds.width-10);
 assert.equal(await notice.evaluate(el=>el.scrollWidth>el.clientWidth+1),false,'long rejected filenames must stay inside the notice');
 await page.screenshot({path:'/tmp/actioncharter-p0c-recipes.png'});
 await recipes.getByRole('button',{name:'Close saved recipes',exact:true}).click();
 assert.deepEqual(await Promise.all(files.map(digest)),before);
 await rename(files[0],resolve(root,'preserved-valid-recipe.json'));
 await page.getByRole('button',{name:'Saved records',exact:true}).click();
 await records.getByText('No valid saved recipes available. Review unavailable records above.',{exact:true}).waitFor();
 assert.equal(await records.getByRole('button',{name:'Open recipe',exact:true}).count(),0);
 assert.equal(await digest(files[1]),before[1]);
 assert.equal(calls.filter(c=>c.url.includes('/authorize')||c.url.includes('/execute')||c.body?.action==='start').length,0);
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'passed',stableIdentity:true,relocatedState:true,validAndInvalidDisplayed:true,allInvalidDisplayed:true,layoutContained:true,warningBeforeSavedPlans:true,filesUnchangedByViews:true,executionOrApprovalCalls:0,pageErrors:errors}));
}finally{
 frontend.closeAllConnections();models.closeAllConnections();await browser?.close();api?.kill('SIGTERM');
 await new Promise(done=>frontend.close(done));await new Promise(done=>models.close(done));await rm(root,{recursive:true,force:true});
}
