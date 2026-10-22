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
 await writeFile(resolve(root,'data/input/sample_orders.csv'),'order_id,region,amount\n'+Array.from({length:1500},(_,i)=>`${String(i+1).padStart(4,'0')},${i===0?'<img src=x onerror=alert(1)>':'north'},${i===2?'':i+1}`).join('\n')+'\n');
 await page.goto(origin);
 await send('Inspect sample_orders.csv. Return row count and column names. No writes.');
 await page.locator('[data-operation-skill="inspect_csv"]').waitFor();
 await page.locator('.top-actions .execute-button').click();
 const results=page.locator('.results-workspace');
 await results.locator('.outcome-step').waitFor();
 await results.getByRole('tab',{name:'Table',exact:true}).click();
 const beforeModels=(await readFile(resolve(root,'model-calls.jsonl'),'utf8')).trim().split('\n').length;
 await results.getByRole('button',{name:'Explore complete CSV',exact:true}).click();
 const explorer=results.getByRole('region',{name:'Complete CSV exploration'});
 await explorer.getByText('1500 matching / 1500 recorded rows · 25 rows in this page',{exact:true}).waitFor();
 await explorer.getByText('Column profiles · complete verified source',{exact:true}).click();
 assert((await explorer.textContent()).includes('numeric-compatible text'));
 assert.equal(await results.locator('img').count(),0);
 cases.push('Explicit full-result query verifies source, profiles the complete file and preserves literal data');
 await explorer.getByText('Filter and sort complete CSV',{exact:true}).click();
 await explorer.getByLabel('Complete CSV filter column',{exact:true}).selectOption('amount');
 await explorer.getByLabel('Complete CSV filter condition',{exact:true}).selectOption('ge');
 await explorer.getByLabel('Complete CSV filter type',{exact:true}).selectOption('number');
 await explorer.getByLabel('Complete CSV filter value',{exact:true}).fill('1200');
 await explorer.getByLabel('Complete CSV sort column',{exact:true}).selectOption('amount');
 await explorer.getByLabel('Complete CSV sort type',{exact:true}).selectOption('number');
 await explorer.getByLabel('Complete CSV sort order',{exact:true}).selectOption('descending');
 await explorer.getByRole('button',{name:'Apply to complete CSV',exact:true}).click();
 await explorer.getByText('301 matching / 1500 recorded rows · 25 rows in this page',{exact:true}).waitFor();
 await results.getByRole('button',{name:'Select result row 1500',exact:true}).click();
 assert((await results.locator('.result-data-table tbody tr').first().textContent()).includes('1500'));
 await explorer.getByRole('button',{name:'Next verified page',exact:true}).click();
 await results.getByRole('button',{name:'Select result row 1475',exact:true}).waitFor();
 cases.push('Numeric filtering/sorting reaches beyond the old preview and server paging retains original row identities');
 await results.getByRole('tab',{name:'Chart',exact:true}).click();
 await results.getByLabel('Category',{exact:true}).selectOption('region');
 await results.getByLabel('Value',{exact:true}).selectOption('amount');
 await results.getByLabel('Chart aggregation',{exact:true}).selectOption('sum');
 await results.getByRole('button',{name:'Analyze verified CSV',exact:true}).click();
 await results.getByText(/301 source rows/).first().waitFor();
 assert((await results.textContent()).includes('Complete hash-verified matching rows'));
 const queryResponses=await page.request.post(`${origin}/api/v1/workflow/runs`,{data:{action:'list'}});
 const recorded=(await queryResponses.json()).records[0];
 const proof=await page.request.post(`${origin}/api/v1/workflow/runs`,{data:{action:'explore',run_id:recorded.run_id,confirmed_plan_sha256:recorded.plan_sha256,conversation_id:recorded.conversation_id,step_id:'step_1',query:{filters:[{column:'amount',operator:'ge',value_type:'number',value:1200}]},analysis:{group_by:'region',value:'amount',aggregation:'sum'}}});
 assert.equal((await proof.json()).chart_analysis.preview[0].value,406350);
 assert.equal((await readFile(resolve(root,'model-calls.jsonl'),'utf8')).trim().split('\n').length,beforeModels);
 cases.push('Chart totals cover all matching rows, not the displayed page; direct controls require no model call');
 await page.getByRole('button',{name:'Planner agent',exact:true}).click();
 await send('Show total amount by region as a bar chart.');
 await results.getByRole('tab',{name:'Chart',selected:true}).waitFor();
 await results.getByText(/1500 source rows/).first().waitFor();
 const inventory=await page.request.post(`${origin}/api/v1/workflow/runs`,{data:{action:'list'}});
 const records=(await inventory.json()).records;
 assert.equal(records.length,1);assert.equal(records[0].plan_sha256,recorded.plan_sha256);
 assert.equal(authorizationCalls(),0);
 cases.push('Planner opens a typed recorded-result chart without replacing the workflow or executing another run');
 const afterViewReads=calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='explore').length;
 await results.getByRole('button',{name:'Close outcome',exact:true}).click();
 await page.getByRole('button',{name:'Outcome',exact:true}).click();
 await results.locator('.outcome-step').waitFor();
 assert.equal(calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='explore').length,afterViewReads);
 await page.getByRole('button',{name:'Planner agent',exact:true}).click();
 await send('Show total amount by region as a bar chart.');
 await results.getByText(/1500 source rows/).first().waitFor();
 assert.equal(calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='explore').length,afterViewReads+1);
 cases.push('Reopening results does not reread artifacts; a new explicit view request applies exactly once');

 await results.getByRole('tab',{name:'Table',exact:true}).click();
 await writeFile(resolve(root,'data/input/sample_orders.csv'),'order_id,region,amount\nchanged,other,999\n');
 await results.getByRole('button',{name:'Explore complete CSV',exact:true}).click();
 await results.getByRole('alert').filter({hasText:'Artifact changed since execution'}).first().waitFor();
 assert((await results.textContent()).includes('saved snapshot'));
 assert.equal((await readdir(resolve(root,'data/output'))).length,0);
 cases.push('Changed artifacts reject with a visible finding and retain the recorded snapshot');
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,page_errors:errors,live_service_calls:0},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls},null,2));throw error;}
finally{await browser?.close();child?.kill('SIGTERM');await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
