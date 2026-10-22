#!/usr/bin/env node
// Actual shared backend and temporary CSV files; deterministic model proposal only.
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,writeFile,readdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve,dirname,extname,isAbsolute} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const repo=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-cp27-retention-'));
const provider=process.env.ACTIONCHARTER_PLAYWRIGHT_MODULE??resolve(repo,'interface/node_modules/playwright/index.mjs');
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(repo,'interface/.playwright-browsers');
const browserLibArchitecture=process.arch==='arm64'?'aarch64-linux-gnu':'x86_64-linux-gnu';
process.env.LD_LIBRARY_PATH=[resolve(repo,'interface/.browser-system-libs/runtime/usr/lib',browserLibArchitecture),process.env.LD_LIBRARY_PATH].filter(Boolean).join(':');
const {chromium}=await import(isAbsolute(provider)?pathToFileURL(provider).href:provider);
let apiPort,child,browser; const calls=[],errors=[],cases=[];
const frontend=createServer(async(req,res)=>{
 try {
  if(req.url.startsWith('/api/')) {
   const chunks=[];for await(const chunk of req)chunks.push(chunk);
   calls.push({method:req.method,path:req.url,action:req.method==='POST'?JSON.parse(Buffer.concat(chunks).toString()).action:undefined});
   const response=await fetch(`http://127.0.0.1:${apiPort}${req.url}`,{method:req.method,headers:{'Content-Type':'application/json'},...(req.method==='POST'?{body:Buffer.concat(chunks)}:{})});
   res.writeHead(response.status,{'Content-Type':'application/json'});res.end(await response.text());return;
  }
  const pathname=new URL(req.url,'http://localhost').pathname;
  const file=pathname.startsWith('/assets/')?resolve(repo,'interface/dist','.'+pathname):resolve(repo,'interface/dist/index.html');
  const content=await readFile(file);res.setHeader('Content-Type',({'.js':'text/javascript','.css':'text/css','.html':'text/html'})[extname(file)]??'application/octet-stream');res.end(content);
 }catch(error){if(res.headersSent||res.destroyed){res.destroy();}else{res.writeHead(500);res.end(String(error));}}
});
await new Promise(done=>frontend.listen(0,'127.0.0.1',done));
const origin=`http://127.0.0.1:${frontend.address().port}`;
try{
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--recipe-runs-fixture'],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'true',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});
 let stderr='';child.stderr.on('data',data=>stderr+=data);
 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error(`API startup timeout: ${stderr}`)),20000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exited ${code}: ${stderr}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());


 page.setDefaultTimeout(20000);
 const state=()=>page.evaluate(async()=>{const conversation_id=localStorage.getItem('actioncharter:planner-conversation:v1');return (await fetch('/api/v1/planner/conversation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'read',conversation_id})})).json();});
 const send=async(message)=>{await page.getByRole('textbox',{name:'Message Planner'}).fill(message);await page.locator('.planner-composer button[type=submit]').click();};
 const authorize=async()=>{await page.getByRole('button',{name:'Authorize',exact:true}).first().click();await page.locator('.workflow-authorization-form textarea').fill('Only the reviewed temporary CSV fixture outputs.');await page.locator('.workflow-authorization-form button[type=submit]').click();await page.locator('.authorization-duration').waitFor();};
 await page.goto(origin);
 await page.getByRole('button',{name:'Conversation settings',exact:true}).click();
 await page.getByRole('switch',{name:'Chat memory'}).waitFor();
 await page.getByRole('button',{name:'Close conversation settings',exact:true}).click();
 await send('Clean sample_orders.csv: keep region and amount, and replace missing regions with Unknown.');
 await page.locator('[data-operation-node="planned_step_2"]').waitFor();
 let chat=await state(); const originalChat=chat.conversation_id;
 const catalog=async(id=originalChat)=>page.evaluate(async conversation_id=>(await fetch('/api/v1/reusable-recipes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'list',conversation_id})})).json(),id);
 await page.getByRole('button',{name:'Reusable recipes',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Reusable recipes'});
 await dialog.getByRole('button',{name:'Recipe list',exact:true}).waitFor();
 assert.equal(await dialog.getByText(/Recorded success ·/).count(),0);
 assert.equal((await catalog()).successful_records.length,0);
 await page.getByRole('button',{name:'Close reusable recipes',exact:true}).click();
 cases.push('Planning alone creates no successful record and requires no registration or recipe-authoring conversation');
 const before=await readFile(resolve(root,'model-calls.jsonl'),'utf8');
 await authorize();
 await page.locator('.workflow-review-panel .execute-button').click();
 await page.locator('.workflow-outcome-panel .outcome-step').first().waitFor();
 await page.locator('.results-workspace').getByRole('tab',{name:'Checks',exact:true}).click();
 await page.locator('.workflow-outcome-panel .critic-outcome').getByText('Recorded operations completed and their reported validation is available.',{exact:true}).waitFor();
 await page.getByRole('button',{name:'Reusable recipes',exact:true}).click();
 await dialog.getByRole('button',{name:/^Select columns and handle missing values/}).waitFor();
 let result=await catalog(); let method=result.successful_records[0];
 assert(method.tags.includes('csv')&&method.tags.includes('cleaning'));
 assert.equal(method.sources.length,1);
 assert.equal(method.execution_authority_granted,false);
 const roleCalls=(await readFile(resolve(root,'model-calls.jsonl'),'utf8')).slice(before.length).trim().split('\n').map(line=>JSON.parse(line));
 assert.deepEqual(roleCalls,[{role:'critic'}]); // Existing outcome review only; no authoring/retention inference.
 assert.equal(await dialog.getByRole('button',{name:'Register tested recipe',exact:true}).count(),0);
 cases.push('Successful execution is retained automatically; existing Critic review is the only post-run model call');
 await dialog.getByRole('button',{name:'Keywords',exact:true}).click();
 assert.equal(await dialog.getByRole('region',{name:'Recipe list',exact:true}).count(),0);
 assert.equal(await dialog.getByLabel('Find a recipe',{exact:false}).count(),0);
 assert.equal(await dialog.getByText('Advanced recipe authoring',{exact:true}).count(),0);
 await dialog.getByRole('button',{name:'csv',exact:true}).click();
 await dialog.getByText('Keyword: csv',{exact:true}).waitFor();
 assert.equal(await dialog.getByRole('region',{name:'Recipe keywords',exact:true}).count(),0);
 await dialog.getByRole('button',{name:/^Select columns and handle missing values/}).click();
 await dialog.getByText('Execution evidence',{exact:true}).click();
 cases.push('Recipe list and Keywords are exclusive views; choosing a keyword switches to filtered summaries and details open only on selection');
 await dialog.getByText('Successful source runs · 1',{exact:true}).click();
 await dialog.getByRole('button',{name:'Inspect recorded outcome',exact:true}).click();
 await page.getByText('Successful workflow saved automatically in Reusable recipes. Historical success grants no new authority.',{exact:true}).waitFor();
 const starts=calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='start').length;
 const originalOutputs=await readdir(resolve(root,'data/output'));
 await page.evaluate(async run_id=>fetch('/api/v1/workflow/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'retain',run_id})}),method.sources[0].run_id);
 assert.deepEqual(await readdir(resolve(root,'data/output')),originalOutputs);
 assert.equal((await catalog()).successful_records[0].sources.length,1);
 cases.push('Inspecting source evidence and retrying indexing preserve outputs and never rerun processing');
 const savedCalls=await readFile(resolve(root,'model-calls.jsonl'),'utf8');
 await page.reload();
 await page.getByRole('button',{name:'Reusable recipes',exact:true}).click();
 await page.getByRole('button',{name:/^Select columns and handle missing values/}).waitFor();
 assert.equal(await readFile(resolve(root,'model-calls.jsonl'),'utf8'),savedCalls);
 assert.equal(calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='start').length,starts);
 cases.push('Refresh restores indexed successful evidence without inference, registration or reexecution');
 await page.getByRole('button',{name:'Close reusable recipes',exact:true}).click();
 await page.getByRole('button',{name:'Planner agent',exact:true}).click();
 await writeFile(resolve(root,'data/input/next_orders.csv'),await readFile(resolve(root,'data/input/sample_orders.csv')));
 const adaptationResponse=page.waitForResponse(response=>response.url().endsWith('/api/v1/planner/conversation')&&response.request().method()==='POST'&&response.request().postDataJSON().action==='turn');
 await send('Clean next_orders.csv: keep region and amount and fill missing regions with Unknown. Use fresh outputs. Find a suitable method automatically.');
 const adapted=await adaptationResponse;
 assert.equal(adapted.status(),200);
 chat=await adapted.json();
 await page.getByRole('log',{name:'Planning conversation'}).getByText(/Adapted from:/).last().waitFor();
 assert.equal(chat.context_usage.recipe_discovery.rounds,2);
 assert.equal(chat.context_usage.recipe_reuse[0].id,method.method_id);
 assert.equal(chat.planner_result.plan.steps[0].arguments.path,'data/input/next_orders.csv');
 assert(chat.planner_result.plan.steps.every(step=>!originalOutputs.includes(step.arguments.target_path?.split('/').pop())));
 assert.equal(calls.filter(call=>call.action==='start').length,starts);
 await authorize();
 await page.locator('.workflow-review-panel .execute-button').click();
 await page.locator('.workflow-outcome-panel .outcome-step').first().waitFor();
 assert.equal((await readdir(resolve(root,'data/output'))).length,originalOutputs.length+2);
 cases.push('Planner searches and inspects methods from ordinary chat, adapts a new CSV with fresh targets and requires fresh authorization without manual recipe selection');
 await page.getByRole('button',{name:'Planner agent',exact:true}).click();
 await page.getByRole('button',{name:'New chat',exact:true}).click();
 await page.waitForFunction(id=>localStorage.getItem('actioncharter:planner-conversation:v1')!==id,originalChat);
 const newId=await page.evaluate(()=>localStorage.getItem('actioncharter:planner-conversation:v1'));
 await page.getByRole('button',{name:'Reusable recipes',exact:true}).click();
 await page.getByRole('button',{name:'Recipe list',exact:true}).waitFor();
 assert.equal(await page.getByText(/Recorded success ·/).count(),0);
 assert.equal((await catalog(newId)).successful_records.length,0);
 assert.equal((await catalog(originalChat)).successful_records.length,1);
 assert.deepEqual(errors,[]);
 cases.push('New chat cannot inherit private successful records or bindings from another conversation');
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,live_service_calls:0,page_errors:errors},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls:calls.slice(-25)},null,2));throw error;}
finally{if(browser)await browser.close();child?.kill();await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
