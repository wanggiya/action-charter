// Synthetic diagnostics records through the real API/UI, isolated browser state.
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {mkdtemp,writeFile,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve,dirname,extname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const repo=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-usage-browser-'));
const chat='a'.repeat(32),submission='d'.repeat(32),workflow='c'.repeat(32);
await writeFile(resolve(root,'actioncharter.workspace.json'),JSON.stringify({version:1,state_root:resolve(root,'state')}));
let api,apiPort,browser;const errors=[],actions=[];
const frontend=createServer(async(req,res)=>{try{
 if(req.url.startsWith('/api/')){
  const chunks=[];for await(const part of req)chunks.push(part);const body=Buffer.concat(chunks);
  actions.push({url:req.url,action:body.length?JSON.parse(body).action:null});
  const response=await fetch(`http://127.0.0.1:${apiPort}${req.url}`,{method:req.method,headers:{'Content-Type':'application/json'},...(req.method==='POST'?{body}:{})});
  res.writeHead(response.status,{'Content-Type':'application/json'});res.end(await response.text());return;
 }
 const path=new URL(req.url,'http://localhost').pathname;
 const file=path.startsWith('/assets/')?resolve(repo,'interface/dist','.'+path):resolve(repo,'interface/dist/index.html');
 res.setHeader('Content-Type',({'.js':'text/javascript','.css':'text/css','.html':'text/html'})[extname(file)]??'application/octet-stream');res.end(await readFile(file));
}catch(error){errors.push(String(error));res.writeHead(500);res.end('Fixture server error');}});
await new Promise(done=>frontend.listen(0,'127.0.0.1',done));
const origin=`http://127.0.0.1:${frontend.address().port}`;
const env={...process.env};for(const key of Object.keys(env))if(key.startsWith('GEOAGENT_')&&key.endsWith('_ROOT'))delete env[key];
Object.assign(env,{PYTHONPATH:resolve(repo,'src'),MODEL_NAME:'fixture:one',MODEL_BASE_URL:'http://127.0.0.1:1/v1',ENABLE_WRITE_TOOLS:'false',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',GEOSERVER_BASE_URL:'http://127.0.0.1:1',INTERFACE_FRONTEND_ORIGIN:origin});
const python=async(code,...args)=>await new Promise((done,reject)=>{
 const p=spawn(resolve(repo,'.venv/bin/python'),['-c',code,...args],{cwd:repo,env});let out='',err='';p.stdout.on('data',v=>out+=v);p.stderr.on('data',v=>err+=v);p.on('exit',n=>n===0?done(out):reject(new Error(err)));
});
try{
 api=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--planning-task-fixture'],{cwd:repo,env});
 apiPort=await new Promise((done,reject)=>{let out='',err='';const timer=setTimeout(()=>reject(new Error(err||'API startup timeout')),20000);api.stderr.on('data',v=>err+=v);api.stdout.on('data',v=>{out+=v;if(out.includes('\n')){clearTimeout(timer);done(JSON.parse(out.split('\n')[0]).port);}});api.on('exit',n=>{clearTimeout(timer);reject(new Error(`API exit ${n}: ${err}`));});});
 const post=async(path,body)=>{const r=await fetch(`http://127.0.0.1:${apiPort}${path}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await r.json();assert.ok(r.ok,JSON.stringify(data));return data;};
 await post('/api/v1/planner/conversation',{action:'turn',conversation_id:chat,message:'Read-only CSV inspection of sample_orders.csv.',allowed_skill_ids:['inspect_csv'],use_history:false});
 await python(`import sys
from pathlib import Path
from geoagent_harness.platform.model_gateway.telemetry import store
root=Path(sys.argv[1]);chat='a'*32;parent='b'*32
resources=lambda seconds:{'elapsed_seconds':seconds,'process_cpu_seconds':0,'api_rss_sampled_peak_bytes':None,'system_available_min_bytes':None}
base={'conversation_id':chat,'started_at':'2026-11-16T10:00:00+00:00','status':'completed','error_code':None}
store(root,'turn',{**base,'id':parent,'submission_id':'d'*32,'workflow_run_id':'c'*32,'workflow_status':'completed','observed_model_calls':4,'resources':resources(100)})
for identity,input,output,role,status,error,dispatch,seconds in [('e',11,7,'planner','completed',None,'attempted',1),('f',13,5,'critic','completed',None,'attempted',2),('1',None,None,'planner','failed','model_timeout','attempted',3),('2',None,None,'planner','failed','model_data_class_blocked','not_attempted',0)]:
 store(root,'call',{**base,'id':identity*32,'parent_id':parent,'model':'fixture:two' if role=='critic' else 'fixture:one','provider_profile_id':'secondary' if role=='critic' else 'local','role':role,'phase':'outcome_review' if role=='critic' else 'planner_generation','prompt_tokens':input,'completion_tokens':output,'status':status,'error_code':error,'network_dispatch':dispatch,'resources':resources(seconds)})`,root);
 const initial=await post('/api/v1/planner/diagnostics',{conversation_id:chat});
 process.env.PLAYWRIGHT_BROWSERS_PATH=resolve(repo,'interface/.playwright-browsers');
 process.env.LD_LIBRARY_PATH=[resolve(repo,'interface/.browser-system-libs/runtime/usr/lib',process.arch==='arm64'?'aarch64-linux-gnu':'x86_64-linux-gnu'),process.env.LD_LIBRARY_PATH].filter(Boolean).join(':');
 const {chromium}=await import(pathToFileURL(resolve(repo,'interface/node_modules/playwright/index.mjs')).href);
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1500,height:1000}});page.setDefaultTimeout(20000);page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
 await page.goto(origin);await page.getByLabel('Saved planning conversation').selectOption(chat);
 await page.locator('.request-diagnostics > summary').click();
 const usage=page.getByRole('region',{name:'Reported model tokens'});
 await usage.getByText('2 of 3 calls reported both counts',{exact:false}).waitFor();
 assert.deepEqual(await usage.locator('.usage-token-grid strong').allTextContents(),['24','12']);
 await page.locator('.request-diagnostics').evaluate(el=>{el.scrollTop=0;});
 const panelBox=await page.locator('.request-diagnostics').boundingBox();
 const tokenBox=await usage.locator('.usage-token-grid strong').first().boundingBox();
 assert.ok(tokenBox.y>=panelBox.y&&tokenBox.y+tokenBox.height<=panelBox.y+panelBox.height,'Token figures must be visible without scrolling');
 assert.ok(!(await usage.innerText()).includes('Total'));
 await usage.getByLabel('Usage scope').selectOption('submission:'+submission);
 assert.deepEqual(await usage.locator('.usage-token-grid strong').allTextContents(),['24','12']);
 await usage.getByLabel('Usage scope').selectOption('workflow:'+workflow);
 await usage.getByText('Timing and call outcomes',{exact:true}).click();
 await usage.getByText('6.00 s · 3 timed calls',{exact:true}).waitFor();
 await usage.getByText('completed',{exact:true}).waitFor();
 await usage.getByText('By role and model',{exact:true}).click();
 await usage.getByText('fixture:two',{exact:false}).waitFor();
 await usage.getByText('Timing and call outcomes',{exact:true}).click();
 await usage.getByText('By role and model',{exact:true}).click();
 await page.locator('.request-diagnostics').evaluate(el=>{el.scrollTop=0;});
 await page.screenshot({path:'/tmp/actioncharter-reported-model-usage.png'});
 const response=page.waitForResponse(r=>r.url().endsWith('/api/v1/planner/diagnostics'));
 await page.getByRole('button',{name:'Refresh diagnostics',exact:true}).click();await response;
 assert.deepEqual((await post('/api/v1/planner/diagnostics',{conversation_id:chat})).records,initial.records);
 const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Export diagnostics JSON',exact:true}).click();
 const download=await downloadPromise;const exported=JSON.parse(await readFile(await download.path(),'utf8'));
 assert.deepEqual(exported.reported_model_usage,initial.reported_model_usage);
 // A previous API can omit the additive summary without causing schema failure.
 const legacy=async route=>{const r=await route.fetch();const data=await r.json();delete data.reported_model_usage;await route.fulfill({response:r,json:data});};
 await page.route('**/api/v1/planner/diagnostics',legacy);
 await page.getByRole('button',{name:'Refresh diagnostics',exact:true}).click();
 await page.getByText('Reported model-token summary is unavailable from this API version.',{exact:false}).waitFor();
 await page.unroute('**/api/v1/planner/diagnostics',legacy);
 await page.getByRole('button',{name:'New chat',exact:true}).click();
 await page.locator('.request-diagnostics > summary').click();
 await page.getByText('No model calls recorded for this scope.',{exact:true}).waitFor();
 // A failed first send must show a reason and preserve it across refresh.
 await page.getByRole('textbox',{name:'Message Planner'}).fill('Inspect sample_orders.csv and suggest useful analysis questions based on its columns. Do not write files or modify any database. diagnostics_timeout_fixture');
 await page.locator('.planner-composer button[type=submit]').click();
 const failure=page.locator('.intent-error');
 await failure.getByText('Shared model request timed out',{exact:false}).waitFor();
 const errorBox=await failure.boundingBox();
 assert.ok(errorBox&&errorBox.y>=0&&errorBox.y<1000,'Failure reason must be visible without finding an off-screen panel');
 const sendsBeforeRefresh=actions.filter(a=>a.url==='/api/v1/planner/submit'&&a.action==='submit').length;
 await page.reload();
 await page.locator('.planner-submission-notice').getByText('The Planner model did not finish before its configured timeout.',{exact:false}).waitFor();
 assert.equal(actions.filter(a=>a.url==='/api/v1/planner/submit'&&a.action==='submit').length,sendsBeforeRefresh,'Reopening a failure must not resend it');
 assert.equal(actions.filter(a=>/workflow\/(authorize|execute)$/.test(a.url)||(a.url==='/api/v1/workflow/runs'&&['start','resume','retry','cancel'].includes(a.action))).length,0);
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'passed',evidence_kind:'fixture',shared_api:true,partial_usage:true,three_scopes:true,legacy_api_compatible:true,chat_isolation:true,export:true,read_does_not_write:true,first_send_reason:true,reason_survives_refresh:true,no_replay:true,workflow_actions:0,page_errors:0}));
}finally{
 if(browser)await browser.close();if(api){api.kill('SIGTERM');await new Promise(done=>api.once('exit',done));}
 await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});
}
