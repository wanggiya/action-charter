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
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-cp26-recipes-'));
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
 }catch(error){res.writeHead(500);res.end(String(error));}
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

 page.setDefaultTimeout(15000);
 await page.goto(origin);
 await page.getByRole('switch',{name:'Chat memory'}).waitFor();
 await page.getByRole('button',{name:'Reusable recipes',exact:true}).click();
 let dialog=page.getByRole('dialog',{name:'Reusable recipes'});
 await dialog.getByRole('button',{name:/^Select columns and fill missing cells/}).click();
 await dialog.getByText('Advanced parameter inspector',{exact:true}).click();
 await dialog.getByLabel(/^source/).fill('data/input/sample_orders.csv');
 await dialog.getByLabel(/^columns/).fill('["region","amount"]');
 await dialog.getByLabel(/^fill values/).fill('{"region":"Unknown"}');
 await dialog.getByLabel(/^selected path/).fill('data/output/browser_selected.csv');
 await dialog.getByLabel(/^target path/).fill('data/output/browser_cleaned.csv');
 await dialog.getByRole('button',{name:'Use recipe · create workflow',exact:true}).click();
 await dialog.waitFor({state:'hidden'});
 await page.locator('[data-operation-node="planned_step_2"]').waitFor();
 await page.waitForFunction(async()=>{
  const id=localStorage.getItem('actioncharter:planner-conversation:v1');
  const response=await fetch('/api/v1/planner/conversation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'read',conversation_id:id})});
  return (await response.json()).planner_result?.plan.steps.length===2;
 });
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 cases.push('Recipe expands into a validated graph and binds the empty current chat without a model or execution');
 await page.getByRole('button',{name:'Reusable recipes',exact:true}).click();
 dialog=page.getByRole('dialog',{name:'Reusable recipes'});
 await dialog.getByText('Create a reusable recipe from this workflow',{exact:true}).click();
 await dialog.getByRole('button',{name:'Prepare recipe',exact:true}).click();
 await dialog.getByText('Critic: supported',{exact:true}).waitFor({timeout:25000});
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 await dialog.getByRole('button',{name:'Register tested recipe',exact:true}).click();
 await dialog.getByRole('button',{name:/^Browser verified cleaner/}).waitFor();
 await dialog.getByRole('button',{name:'Close reusable recipes',exact:true}).click();
 await page.reload();
 await page.locator('[data-operation-node="planned_step_2"]').waitFor();
 await page.getByRole('button',{name:'Reusable recipes',exact:true}).click();
 await page.getByRole('button',{name:/^Browser verified cleaner/}).waitFor();
 await page.getByRole('button',{name:'Close reusable recipes',exact:true}).click();
 cases.push('Planner authoring, real isolated fixture tests and Critic prepare a candidate; one registration persists across refresh');
 await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
 await page.locator('.workflow-authorization-form textarea').fill('Only temporary browser fixture outputs.');
 await page.locator('.workflow-authorization-form button[type=submit]').click();
 await page.locator('.authorization-duration').waitFor();
 await writeFile(resolve(root,'hold-validation'),'fixture only');
 await page.locator('.workflow-review-panel .execute-button').click();
 for(let i=0;i<100;i++){try{await readFile(resolve(root,'validation-entered'));break;}catch{await new Promise(r=>setTimeout(r,50));}}
 await page.getByRole('button',{name:'Cancel',exact:true}).click();
 await page.getByRole('button',{name:'Stopping after current operation…',exact:true}).waitFor();
 await rm(resolve(root,'hold-validation'));
 await page.locator('.workflow-runs-panel').getByRole('heading',{name:'cancelled',exact:true}).waitFor();
 assert.deepEqual(await readdir(resolve(root,'data/output')),['browser_selected.csv']);
 await page.locator('.run-step-list > li').first().locator('summary').first().click();
 await page.getByText('Validation',{exact:true}).waitFor();
 cases.push('One Cancel click lets active validation finish, skips the next write and retains the first output');
 await page.getByRole('button',{name:'Prepare recovery with fresh targets',exact:true}).click();
 await page.getByText(/New recovery workflow prepared with fresh targets/).waitFor();
 await page.getByRole('button',{name:'Close workflow runs',exact:true}).click();
 await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
 await page.locator('.workflow-authorization-form textarea').fill('Only new temporary recovery targets.');
 await page.locator('.workflow-authorization-form button[type=submit]').click();
 await page.locator('.authorization-duration').waitFor();
 await page.locator('.workflow-review-panel .execute-button').click();
 await page.locator('.workflow-outcome-panel .outcome-step').first().waitFor({timeout:25000});
 assert.equal((await readdir(resolve(root,'data/output'))).length,3);
 await page.getByRole('button',{name:'Execution History',exact:true}).click();
 await page.getByRole('button',{name:'Workflow runs · cancellation and recovery',exact:true}).click();
 await page.locator('.workflow-runs-panel').waitFor();
 await page.waitForFunction(()=>document.querySelector('.workflow-runs-panel select')?.options.length===3);
 assert.equal(await page.locator('.workflow-runs-panel select option').count(),3);
 cases.push('Recovery saves a new full workflow with fresh targets, requires fresh authorization and preserves old output/history');

 await page.getByRole('button',{name:'Close workflow runs',exact:true}).click();
 await page.getByRole('button',{name:'Reusable recipes',exact:true}).click();
 dialog=page.getByRole('dialog',{name:'Reusable recipes'});
 await dialog.getByRole('button',{name:/^Vector attributes to CSV/}).click();
 await dialog.getByText('Advanced parameter inspector',{exact:true}).click();
 await dialog.getByLabel(/^path/).fill('data/input/sample_points.geojson');
 await dialog.getByLabel(/^target path/).fill('data/output/chain_attributes.csv');
 await dialog.getByRole('button',{name:'Add to composition',exact:true}).click();
 await dialog.getByRole('button',{name:/^Select columns and fill missing cells/}).click();
 await dialog.getByText('Advanced parameter inspector',{exact:true}).click();
 await dialog.getByRole('combobox',{name:'Connect previous recipe output'}).selectOption('recipe_1');
 await dialog.getByLabel(/^columns/).fill('["id","name"]');
 await dialog.getByLabel(/^fill values/).fill('{"name":"Unknown"}');
 await dialog.getByLabel(/^selected path/).fill('data/output/chain_selected.csv');
 await dialog.getByLabel(/^target path/).fill('data/output/chain_cleaned.csv');
 await dialog.getByRole('button',{name:'Use recipe · create workflow',exact:true}).click();
 await dialog.waitFor({state:'hidden'});
 await page.locator('[data-operation-node="planned_step_4"]').waitFor();
 await page.waitForFunction(async()=>{
  const id=localStorage.getItem('actioncharter:planner-conversation:v1');
  const response=await fetch('/api/v1/planner/conversation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'read',conversation_id:id})});
  const state=await response.json();return state.planner_result?.plan.steps[2].arguments.source_step==='step_2';
 });
 assert.equal((await readdir(resolve(root,'data/output'))).length,3);
 cases.push('UI composes spatial attribute and CSV cleaning recipes with typed output binding and four explicit operations');
 const beforeRestart=await readdir(resolve(root,'data/output'));
 await new Promise(done=>{child.once('exit',done);child.kill();});
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--recipe-runs-fixture'],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'true',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});

 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error('Restart timeout')),15000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});});
 await page.reload();
 await page.locator('[data-operation-node="planned_step_4"]').waitFor();
 await page.getByRole('button',{name:'Reusable recipes',exact:true}).click();
 await page.getByRole('button',{name:/^Browser verified cleaner/}).waitFor();
 await page.getByRole('button',{name:'Close reusable recipes',exact:true}).click();
 await page.getByRole('button',{name:'Execution History',exact:true}).click();
 await page.getByRole('button',{name:'Workflow runs · cancellation and recovery',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.workflow-runs-panel select')?.options.length===3);
 assert.deepEqual(await readdir(resolve(root,'data/output')),beforeRestart);
 cases.push('Actual API restart preserves registered recipe, current chat graph and both durable attempts without reexecution');
 assert.deepEqual(errors,[]);
 assert.equal(calls.filter(c=>c.path==='/api/v1/workflow/runs'&&c.action==='start').length,2);
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,live_service_calls:0,page_errors:errors},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls:calls.slice(-30)},null,2));throw error;}
finally{if(browser)await browser.close();child?.kill();await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
