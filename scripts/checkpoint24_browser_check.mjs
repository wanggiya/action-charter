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
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-cp24-'));
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
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'true',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});
 let stderr='';child.stderr.on('data',data=>stderr+=data);
 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error(`API startup timeout: ${stderr}`)),20000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exited ${code}: ${stderr}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
 await page.goto(origin);
 await page.getByRole('textbox',{name:'Message Planner'}).fill('Inspect sample_orders.csv, select order_id/region/amount, fill missing region unknown and amount 0, filter amount >= 10, join sample_regions.csv by region many_to_one, group by region_name with sum amount and count order_id, export final.csv.');
 await page.locator('.planner-composer button[type=submit]').click();
 await page.locator('[data-operation-node="planned_step_7"]').waitFor({timeout:20000});
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);cases.push('Conversation produces and saves seven typed operations without execution');
 await page.getByRole('button',{name:'Add',exact:true}).click();
 const picker=page.getByRole('dialog',{name:'Add operation'});
 await picker.getByRole('textbox',{name:'Search operations'}).fill('CSV');
 assert(await picker.locator('.operation-picker-results button').count()>=4);
 await picker.getByRole('button',{name:'Close add operation panel'}).click();
 cases.push('Registered table operations are searchable in editable graph');
 await page.locator('[data-operation-node="planned_step_2"]').click();
 await page.getByRole('button',{name:'Block tools',exact:true}).click();
 await page.getByRole('button',{name:'Parameters',exact:true}).click();
 const parameter=page.getByRole('textbox',{name:'Structured operation parameter'});
 await parameter.fill('[invalid');
 await parameter.blur();
 assert(await page.getByRole('button',{name:'Validate and save edits',exact:true}).isDisabled());
 await parameter.fill('["region","amount","order_id"]');
 await parameter.blur();
 await page.getByRole('button',{name:'Validate and save edits',exact:true}).click();
 await page.getByRole('button',{name:'Validate and save edits',exact:true}).waitFor({state:'hidden'});
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 await page.waitForFunction(async()=>{
  const id=localStorage.getItem('actioncharter:planner-conversation:v1');
  const response=await fetch('/api/v1/planner/conversation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'read',conversation_id:id})});
  const state=await response.json();return JSON.stringify(state.planner_result?.plan.steps[1].arguments.columns)==='["region","amount","order_id"]';
 });
 cases.push('Graph JSON editing blocks malformed drafts and saves corrected typed columns through backend validation');
 await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
 await page.locator('.workflow-review-panel').waitFor();
 await page.locator('.workflow-authorization-form textarea').fill('Only temporary CSV fixture outputs.');
 await page.locator('.workflow-authorization-form button[type=submit]').click();
 await page.locator('.authorization-duration').waitFor();
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);cases.push('Exact authority records without writing CSV');
 await page.locator('.workflow-review-panel .execute-button').click();
 await page.locator('.workflow-outcome-panel .outcome-step').first().waitFor({timeout:30000});
 assert.equal((await readdir(resolve(root,'data/output'))).length,6);
 assert.equal(await readFile(resolve(root,'data/output/final.csv'),'utf8'),'region_name,total,orders\nNorth region,30,2\nSouth region,40,1\nUnknown region,30,1\n');
 await page.locator(".workflow-outcome-panel .outcome-step > summary").last().click();
 const table=page.locator('.table-result-preview').last();
 assert((await table.textContent()).includes('North region'));assert.equal(await table.locator('tbody tr').count(),3);
 cases.push('Execute runs real pandas pipeline; independent checks, exact final bytes and bounded preview pass');
 await page.getByRole('button',{name:'Close outcome'}).click();
 await page.getByRole('button',{name:'Execution History',exact:true}).click();
 await page.getByRole('button',{name:'Reopen run graph',exact:true}).click();
 await page.locator('.canvas-window').waitFor();
 await page.reload();
 // Startup restores the remembered saved revision without a conversation-open click.
 await page.locator('[data-operation-node="planned_step_7"]').waitFor();
 await page.getByRole('button',{name:'Execution History',exact:true}).click();
 await page.getByRole('button',{name:'Reopen run graph',exact:true}).waitFor();
 assert.equal(await page.getByRole('button',{name:'Reopen run graph',exact:true}).count(),1);
 assert.equal(calls.filter(c=>c.path==='/api/v1/workflow/runs'&&c.action==='start').length,1);cases.push('History and reload preserve plan and durable attempt without reexecution');
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,live_service_calls:0,page_errors:errors},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls},null,2));throw error;}
finally{if(browser)await browser.close();child?.kill();await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
