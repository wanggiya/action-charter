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
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-writes-'));
const failureMode=process.env.ACTIONCHARTER_CALCULATION_FAILURE_MODE??'reuse';
const omissionFixture=failureMode!=='invalid_json';
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
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--calculation-fixture','--write-policy-fixture'],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'false',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});
 let stderr='';child.stderr.on('data',data=>stderr+=data);
 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error(`API startup timeout: ${stderr}`)),20000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exited ${code}: ${stderr}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
 await page.goto(origin);
 const setWrites=async enabled=>{
   const headerToggle=page.getByRole('switch',{name:'⚠ Allow writes',exact:true});
   if((await headerToggle.getAttribute('aria-checked'))!==String(enabled))await headerToggle.click();
   await page.waitForFunction(value=>document.querySelector('[aria-labelledby="toolbar-write-label"]')?.getAttribute('aria-checked')===String(value),enabled);
   await page.getByRole('button',{name:'Settings',exact:true}).click();
   const settingsToggle=page.getByRole('switch',{name:'Allow write operations',exact:true});
   assert.equal(await settingsToggle.getAttribute('aria-checked'),String(enabled));
   await page.getByRole('button',{name:'Close settings',exact:true}).click();
 };
 const generate=async()=>{
   await page.getByRole('textbox',{name:'Message Planner'}).fill('Inspect sample_orders.csv. Calculate doubled as amount multiplied by 2, propagate missing values, and export to fresh CSV outputs. Do not execute yet.');
   await page.locator('.planner-composer button[type=submit]').click();
   await page.locator('[data-operation-node="planned_step_3"]').waitFor({timeout:20000});
 };
 const authorize=async()=>{
   await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
   await page.locator('.workflow-authorization-form textarea').fill('Only fresh temporary fixture CSV outputs.');
   await page.locator('.workflow-authorization-form button[type=submit]').click();
   await page.locator('.authorization-duration').waitFor();
 };
 await page.getByText('Writes: OFF',{exact:true}).waitFor();
 await generate();
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
 await page.locator('.workflow-review-panel').getByRole('alert').filter({hasText:'Write operations are OFF'}).waitFor();
 await setWrites(true);
 await page.getByText('Writes: ON',{exact:true}).waitFor();
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 cases.push('Startup OFF still plans; Warning toolbar switch and Settings share write policy without restart, model call, output or authorization');
 const authorizationResponse=page.waitForResponse(response=>response.url().endsWith('/api/v1/workflow/authorize'));
 await authorize();
 const approval=await (await authorizationResponse).json();
 const reviewCall=calls.filter(call=>call.path==='/api/v1/workflow/prepare');
 // Read exact current review for a later stale-request bypass attempt.
 const current=await page.evaluate(async()=>{
   const id=localStorage.getItem('actioncharter:planner-conversation:v1');
   const chat=await (await fetch('/api/v1/planner/conversation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'read',conversation_id:id})})).json();
   return {id,sha:chat.planner_result.plan_sha256};
 });
 const review=await page.evaluate(async sha=>(await fetch('/api/v1/workflow/prepare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'prepare_workflow',plan_filename:`planner-plan.${sha}.json`,confirmed_plan_sha256:sha})})).json(),current.sha);
 await setWrites(false);await setWrites(true);
 assert.equal(await page.locator('.authorization-duration').count(),0);
 const stale=await page.evaluate(async ({review,approval,id})=>{
   const response=await fetch('/api/v1/workflow/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'start',conversation_id:id,workflow:{action:'execute_workflow',plan_filename:review.plan_filename,confirmed_plan_sha256:review.plan_sha256,confirmed_review_sha256:review.review_sha256,plan_approval_filename:approval.plan_approval_filename,recipe_approval_filename:approval.recipe_approval_filename,confirm_execution:true}})});
   return {status:response.status,body:await response.json()};
 },{review,approval,id:current.id});
 assert(stale.status>=400);
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 cases.push('OFF then ON clears UI approval and the backend rejects a cached exact execution request');
 await authorize();
 await page.locator('.workflow-review-panel .execute-button').click();
 await page.locator('.workflow-outcome-panel .outcome-step').first().waitFor({timeout:30000});
 assert.equal((await readdir(resolve(root,'data/output'))).length,2);
 cases.push('Fresh authorization executes and verifies both real CSV writes without launcher restart');
 await page.getByRole('button',{name:'Close outcome',exact:true}).click();
 await page.reload();
 await page.getByText('Writes: ON',{exact:true}).waitFor();
 await page.locator('[data-operation-node="planned_step_3"]').waitFor();
 assert.equal((await readdir(resolve(root,'data/output'))).length,2);
 cases.push('Browser refresh preserves server availability and recorded workflow without execution');
 await page.getByRole('button',{name:'Planner agent',exact:true}).click();
 await page.getByRole('button',{name:'New chat',exact:true}).click();
 await generate();await authorize();
 await writeFile(resolve(root,'hold-validation'),'fixture only');
 await page.locator('.workflow-review-panel .execute-button').click();
 for(let i=0;i<200;i++){try{await readFile(resolve(root,'validation-entered'));break;}catch{await new Promise(resolve=>setTimeout(resolve,25));}}
 assert.equal(await readFile(resolve(root,'validation-entered'),'utf8'),'fixture only');
 await setWrites(false);
 await rm(resolve(root,'hold-validation'));
 await page.locator('.workflow-runs-panel').getByRole('heading',{name:'failed',exact:true}).waitFor({timeout:30000});
 assert.equal((await readdir(resolve(root,'data/output'))).length,3);
 assert((await page.locator('.workflow-runs-panel').textContent()).includes('Write operations are OFF'));
 const firstCompleted=page.locator('.workflow-runs-panel .run-step-list > li').nth(1);
 await firstCompleted.locator('summary').first().click();
 await firstCompleted.getByRole('heading',{name:'Validation passed',exact:true}).waitFor();
 cases.push('Disable during validation retains the verified first output, blocks the next write and exposes the failed step');
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,live_service_calls:0,page_errors:errors},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls},null,2));throw error;}
finally{if(browser)await browser.close();child?.kill();await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
