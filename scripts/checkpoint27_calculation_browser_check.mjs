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
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-calculation-'));
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
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--calculation-fixture',omissionFixture?'--calculation-omission-fixture':'--calculation-invalid-json-fixture',...(failureMode==='reuse'?['--calculation-reuse-claim-fixture']:[])],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'true',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});
 let stderr='';child.stderr.on('data',data=>stderr+=data);
 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error(`API startup timeout: ${stderr}`)),20000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exited ${code}: ${stderr}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
 await page.goto(origin);
 if(omissionFixture) {
   await page.evaluate(()=>localStorage.setItem('actioncharter:planner-conversation:v1','c'.repeat(32)));
   await page.reload();
   await page.getByRole('region',{name:'Workflow operations'}).getByRole('button',{name:/Inspect CSV table/}).waitFor();
   assert.equal(await page.getByRole('region',{name:'Workflow operations'}).getByRole('button').count(),1);
   assert.equal(await page.locator('.calculation-summary').count(),0);
   assert((await page.locator('.missing-calculation').textContent()).includes('no calculation step'));
   assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
   cases.push('Historical inspection-only proposal restores honestly with a missing-calculation notice, not an invented formula');
 }
 await page.getByRole('textbox',{name:'Message Planner'}).fill('Inspect sample_orders.csv. Create a new numeric column doubled equal to amount multiplied by 2. Preserve all original columns and propagate missing values. Save to a fresh CSV. Do not execute yet.');
 await page.locator('.planner-composer button[type=submit]').click();
 await page.locator('[data-operation-node="planned_step_2"]').waitFor({timeout:20000});
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 const session=await page.evaluate(async()=>{
   const id=localStorage.getItem('actioncharter:planner-conversation:v1');
   const response=await fetch('/api/v1/planner/conversation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'read',conversation_id:id})});return response.json();
 });
 assert.equal(session.context_usage.effort_budget.model_calls,2);
 assert.deepEqual(session.context_usage.recipe_reuse,[]);
 const operations=page.getByRole('region',{name:'Workflow operations'});
 assert.equal(await operations.getByRole('button').count(),2);
 assert((await operations.textContent()).includes('doubled = (amount × 2)'));
 await operations.getByRole('button',{name:/Calculate table columns/}).click();
 assert.equal(await page.locator('[data-operation-node="planned_step_2"]').getAttribute('class').then(value=>value.includes('selected')),true);
 assert((await page.locator('.calculation-summary').textContent()).includes('amount × 2'));
 assert.equal(await page.locator('.inspector-raw-arguments').getAttribute('open'),null);
 for(const title of ['Execution details','Evidence']) {
   const disclosure=page.locator('.inspector-disclosure').filter({has:page.locator('summary').filter({hasText:new RegExp(`^${title}$`)})});
   assert.equal(await disclosure.getAttribute('open'),null);
   await disclosure.locator(':scope > summary').click();
   assert.equal(await disclosure.getAttribute('open'),'');
   await disclosure.locator(':scope > summary').click();
 }
 assert.equal(await page.locator('.inspector h3').filter({hasText:/^Performed by$/}).count(),0);
 cases.push('Operation list exposes both steps and formula before graph selection; optional audit and raw arguments collapse without hiding the formula');
 cases.push(failureMode==='reuse'?'Unverified reuse claim on a complete calculation is rejected once, then corrected without fabricated provenance':omissionFixture?'Inspection-only success claim is rejected and corrected into actual calculation steps before saving':'Exact acceptance wording recovers one invalid JSON reply within the existing correction budget');
 await page.getByRole('button',{name:'Add',exact:true}).click();
 const picker=page.getByRole('dialog',{name:'Add operation'});
 await picker.getByRole('textbox',{name:'Search operations'}).fill('Calculate');
 assert.equal(await picker.locator('.operation-picker-results button').count(),1);
 await picker.getByRole('button',{name:'Close add operation panel'}).click();
 await page.getByRole('button',{name:'Block tools',exact:true}).click();
 await page.getByRole('button',{name:'Parameters',exact:true}).click();
 const editor=page.getByRole('group',{name:'Calculated columns',exact:true});
 await editor.getByRole('spinbutton',{name:'Calculation number'}).fill('');
 assert(await page.getByRole('button',{name:'Validate and save edits',exact:true}).isDisabled());
 await editor.getByRole('spinbutton',{name:'Calculation number'}).fill('3');
 await page.getByRole('button',{name:'Validate and save edits',exact:true}).click();
 await page.getByRole('button',{name:'Validate and save edits',exact:true}).waitFor({state:'hidden'});
 assert((await page.locator('.calculation-summary').textContent()).includes('amount × 3'));
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 cases.push('Searchable graph operation and formula controls edit without manual JSON; backend validates before saving');
 await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
 await page.locator('.workflow-authorization-form textarea').fill('Temporary calculated output only.');
 await page.locator('.workflow-authorization-form button[type=submit]').click();
 await page.locator('.authorization-duration').waitFor();
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 await page.locator('.workflow-review-panel .execute-button').click();
 await page.locator('.workflow-outcome-panel .outcome-step').first().waitFor({timeout:30000});
 const outputs=await readdir(resolve(root,'data/output'));
 assert.equal(outputs.length,1);
 const data=await readFile(resolve(root,'data/output',outputs[0]),'utf8');
 assert(data.includes('doubled'));assert(data.includes('001,north,10,01,a,30.0'));assert(data.includes('003,south,,03,c,'));
 cases.push('Fresh authority precedes real calculation, with expected values and propagated missing inputs');
 await page.getByRole('button',{name:'Close outcome'}).click();
 await page.reload();
 await page.locator('[data-operation-node="planned_step_2"]').waitFor();
 await page.locator('[data-operation-node="planned_step_2"]').click();
 assert((await page.locator('.calculation-summary').textContent()).includes('amount × 3'));
 assert.equal(calls.filter(c=>c.path==='/api/v1/workflow/runs'&&c.action==='start').length,1);
 cases.push('Refresh restores the exact edited formula without regeneration or reexecution');
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,live_service_calls:0,page_errors:errors},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls},null,2));throw error;}
finally{if(browser)await browser.close();child?.kill();await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
