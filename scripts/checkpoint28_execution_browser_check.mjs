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
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-execution-'));
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
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--planning-task-fixture'],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'false',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});
 let stderr='';child.stderr.on('data',data=>stderr+=data);
 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error(`API startup timeout: ${stderr}`)),20000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exited ${code}: ${stderr}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
 const send=async(message)=>{await page.getByRole('textbox',{name:'Message Planner'}).fill(message);await page.locator('.planner-composer button[type=submit]').click();await page.waitForFunction(()=>document.querySelector('.planner-composer button[type=submit]')?.textContent?.includes('Send'),{},{timeout:30000});};
 const executionCalls=()=>calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='start').length;
 const authorizationCalls=()=>calls.filter(call=>call.path==='/api/v1/workflow/authorize').length;
 await page.goto(origin);
 await send('Read-only CSV inspection sample_orders.csv. Return row count and column names. No writes.');
 await page.locator('[data-operation-skill="inspect_csv"]').waitFor();
 assert.equal(await page.getByRole('button',{name:'Authorize',exact:true}).count(),0);
 assert.equal(await page.getByRole('switch',{name:'⚠ Allow writes',exact:true}).getAttribute('aria-checked'),'false');
 await page.locator('.top-actions .execute-button').click();
 await page.locator('.results-workspace .outcome-step').first().waitFor();
 assert.equal(executionCalls(),1);assert.equal(authorizationCalls(),0);
 assert.equal((await readdir(resolve(root,'data/output'))).length,0);
 cases.push('One header Execute click runs read-only CSV with writes OFF and no authorization');
 await page.getByRole('button',{name:'Planner agent',exact:true}).click();
 await page.getByRole('button',{name:'New chat',exact:false}).click();
 await send('Vector task inspection sample_points.geojson. Return CRS and feature count. No writes.');
 await page.locator('[data-operation-skill="inspect_vector"]').waitFor();
 assert.equal(await page.getByRole('button',{name:'Authorize',exact:true}).count(),0);
 await page.locator('.top-actions .execute-button').click();
 await page.locator('.results-workspace .outcome-step').first().waitFor();
 assert.equal(executionCalls(),2);assert.equal(authorizationCalls(),0);
 cases.push('One header Execute click runs vector inspection with no write permission or authorization');
 await page.getByRole('button',{name:'Planner agent',exact:true}).click();
 await send('CSV task inspection sample_orders.csv, select order_id and region to a fresh CSV. Do not execute.');
 await page.locator('[data-operation-skill="select_csv_columns"]').waitFor();
 assert.equal(await page.locator('.top-actions .execute-button').isDisabled(),true);
 assert.equal(executionCalls(),2);
 cases.push('Write workflow cannot Execute before write availability and authorization');
 await page.getByRole('switch',{name:'⚠ Allow writes',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('[aria-labelledby="toolbar-write-label"]')?.getAttribute('aria-checked')==='true');
 assert.equal(await page.locator('.top-actions .execute-button').isDisabled(),true);
 await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
 await page.locator('.workflow-authorization-form textarea').fill('Only fresh temporary CSV output.');
 await page.locator('.workflow-authorization-form button[type=submit]').click();
 await page.locator('.authorization-duration').waitFor();
 assert.equal(authorizationCalls(),1);assert.equal(executionCalls(),2);
 assert.equal((await readdir(resolve(root,'data/output'))).length,0);
 await page.locator('.top-actions .execute-button').click();
 await page.locator('.results-workspace .outcome-step').first().waitFor();
 assert.equal(executionCalls(),3);
 assert((await readFile(resolve(root,'data/output/task_identity.csv'),'utf8')).startsWith('order_id,region'));
 cases.push('Allow writes, Authorize and Execute remain separate for a validated CSV write');
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,page_errors:errors,live_service_calls:0},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls},null,2));throw error;}
finally{await browser?.close();child?.kill('SIGTERM');await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
