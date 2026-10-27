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
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-agent-modes-'));
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
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--calculation-fixture','--agent-modes-fixture'],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'true',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});
 let stderr='';child.stderr.on('data',data=>stderr+=data);
 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error(`API startup timeout: ${stderr}`)),20000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exited ${code}: ${stderr}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
 await page.goto(origin);
 for(const mode of ['three','single']){
  if(cases.length){if(!await page.getByRole('textbox',{name:'Message Planner'}).isVisible())await page.getByRole('button',{name:'Planner agent',exact:true}).click();await page.getByRole('button',{name:'New chat',exact:true}).click();}
  await page.getByRole('button',{name:'Conversation settings',exact:true}).click();
  await page.getByLabel('Task agent mode',{exact:true}).selectOption(mode);
  await page.waitForFunction(expected=>document.querySelector('[aria-label="Task agent mode"]')?.disabled===false,mode);
  await page.getByRole('button',{name:'Close conversation settings',exact:true}).click();
  await page.getByRole('textbox',{name:'Message Planner'}).fill('Calculate doubled amount in sample_orders.csv. Preserve existing columns and propagate missing amounts. Prepare only.');
  await page.locator('.planner-composer button[type=submit]').click();
  await page.locator('[data-operation-node="planned_step_2"]').waitFor({timeout:20000});
  const prepare=page.waitForResponse(response=>response.url().endsWith('/api/v1/workflow/prepare'));
  await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
  const reviewed=await (await prepare).json();assert.equal(reviewed.agent_mode,mode);
  await page.locator('.workflow-authorization-form textarea').fill('Exact temporary fixture outputs only.');
  const beforeExecution=calls.filter(c=>c.path==='/api/v1/workflow/runs'&&c.action==='start').length;
  await page.locator('.workflow-authorization-form button[type=submit]').click();await page.locator('.authorization-duration').waitFor();
  assert.equal(calls.filter(c=>c.path==='/api/v1/workflow/runs'&&c.action==='start').length,beforeExecution);
  const starting=page.waitForResponse(response=>response.url().endsWith('/api/v1/workflow/runs')&&response.request().postDataJSON()?.action==='start');
  await page.locator('.workflow-review-panel .execute-button').click();
  const run=await (await starting).json();
  await page.locator('.results-workspace .outcome-step').first().waitFor({timeout:30000});
  const report=page.locator('.results-workspace .task-agent-report').first();
  await report.locator('summary').first().click();
  await report.getByRole('button',{name:'Download recorded report',exact:true}).waitFor({timeout:20000});
  const downloading=page.waitForEvent('download');
  await report.getByRole('button',{name:'Download recorded report',exact:true}).click();
  const download=await downloading;
  assert.ok(download.suggestedFilename().endsWith('.txt'));
  const reportText=await readFile(await download.path(),'utf8');
  assert.ok(reportText.includes('Recorded operations')&&reportText.includes(`Mode: ${mode}`));
  assert.ok((await report.innerText()).includes(mode==='single'?'Self-review is not an independent':'Critic uses a separate context'));
  const requestCount=calls.filter(c=>c.path==='/api/v1/workflow/runs'&&c.action==='start').length;
  await page.screenshot({path:`/tmp/actioncharter-${mode}-agent-report.png`});
  await page.reload();
  await page.getByRole('button',{name:'Conversation settings',exact:true}).click();
  await page.waitForFunction(expected=>{const select=document.querySelector('[aria-label="Task agent mode"]');return select&&!select.disabled&&select.value===expected;},mode);
  assert.equal(await page.getByLabel('Task agent mode',{exact:true}).inputValue(),mode);
  await page.getByRole('button',{name:'Close conversation settings',exact:true}).click();
  assert.equal(calls.filter(c=>c.path==='/api/v1/workflow/runs'&&c.action==='start').length,requestCount);
  const response=await fetch(origin+'/api/v1/workflow/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'report',run_id:run.run_id})});
  const stored=await response.json();assert.equal(stored.mode,mode);assert.equal(stored.authority_granted,false);
  cases.push(`${mode}: selector persisted, exact authorization, actual CSV execution, recorded report restored without replay`);
 }
 assert.deepEqual(errors,[]);
 cases.push('Authorization alone produces no execution, data output or live database request');
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,live_service_calls:0,page_errors:errors},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls},null,2));throw error;}
finally{if(browser)await browser.close();child?.kill();await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
