// Isolated M1 Settings/API/CLI journey; fake model endpoint and ephemeral browser profile.
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve,dirname,extname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const repo=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-m1-browser-'));
const testEgress=process.argv.includes('--egress');let expectedSyntheticCalls=2;
await writeFile(resolve(root,'actioncharter.workspace.json'),JSON.stringify({version:1,state_root:resolve(root,'state')}));
const key='SYNTHETIC_M1_BROWSER_KEY';
const providerCalls=[],apiCalls=[],errors=[];let apiPort,api,browser;
const provider=createServer(async(req,res)=>{
 res.setHeader('Content-Type','application/json');providerCalls.push({method:req.method,path:req.url});
 if(req.url.startsWith('/api/')){res.end(JSON.stringify({models:[{name:'fixture:small',size:1}]}));return;}
 if(req.headers.authorization!==`Bearer ${key}`){res.writeHead(401);res.end('{}');return;}
 if(req.method==='GET'){res.end(JSON.stringify({data:[{id:'fixture:small'},{id:'fixture:other'}]}));return;}
 const chunks=[];for await(const part of req)chunks.push(part);const body=JSON.parse(Buffer.concat(chunks));
 assert.equal(body.messages.length,1);assert.ok(body.messages[0].content.startsWith('Return only this JSON'));
 if(body.response_format?.type==='json_schema'){res.writeHead(400);res.end(JSON.stringify({error:'response_format json_schema unsupported'}));return;}
 res.end(JSON.stringify({choices:[{message:{content:'{"ok":true}'}}],usage:{prompt_tokens:3,completion_tokens:2}}));
});
await new Promise(done=>provider.listen(0,'127.0.0.1',done));
const frontend=createServer(async(req,res)=>{try{
 if(req.url.startsWith('/api/')){
  const chunks=[];for await(const part of req)chunks.push(part);const body=Buffer.concat(chunks);
  apiCalls.push({method:req.method,url:req.url,action:body.length?JSON.parse(body).action:null});
  const response=await fetch(`http://127.0.0.1:${apiPort}${req.url}`,{method:req.method,headers:{'Content-Type':'application/json'},...(req.method==='POST'?{body}:{})});
  const text=await response.text();assert.ok(!text.includes(key));res.writeHead(response.status,{'Content-Type':'application/json'});res.end(text);return;
 }
 const path=new URL(req.url,'http://localhost').pathname;
 const file=path.startsWith('/assets/')?resolve(repo,'interface/dist','.'+path):resolve(repo,'interface/dist/index.html');
 res.setHeader('Content-Type',({'.js':'text/javascript','.css':'text/css','.html':'text/html'})[extname(file)]??'application/octet-stream');res.end(await readFile(file));
 }catch(error){res.writeHead(500);res.end('Fixture request failed');errors.push(String(error));}});
await new Promise(done=>frontend.listen(0,'127.0.0.1',done));
const origin=`http://127.0.0.1:${frontend.address().port}`;
process.env.PLAYWRIGHT_BROWSERS_PATH=resolve(repo,'interface/.playwright-browsers');
process.env.LD_LIBRARY_PATH=[resolve(repo,'interface/.browser-system-libs/runtime/usr/lib',process.arch==='arm64'?'aarch64-linux-gnu':'x86_64-linux-gnu'),process.env.LD_LIBRARY_PATH].filter(Boolean).join(':');
const {chromium}=await import(pathToFileURL(resolve(repo,'interface/node_modules/playwright/index.mjs')).href);
try{
 const env={...process.env};for(const name of Object.keys(env))if(name.startsWith('GEOAGENT_')&&name.endsWith('_ROOT'))delete env[name];
 Object.assign(env,{PYTHONPATH:resolve(repo,'src'),ACTIONCHARTER_STATE_ROOT:resolve(root,'state'),MODEL_NAME:'fixture:small',MODEL_BASE_URL:`http://127.0.0.1:${provider.address().port}/v1`,M1_BROWSER_KEY:key,ENABLE_WRITE_TOOLS:'false',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',GEOSERVER_BASE_URL:'http://127.0.0.1:1',INTERFACE_FRONTEND_ORIGIN:origin});
 api=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--planning-task-fixture',...(testEgress?['--model-gateway-fixture']:[])],{cwd:repo,env});
 let error='';api.stderr.on('data',v=>error+=v);
 apiPort=await new Promise((done,reject)=>{let out='';const timer=setTimeout(()=>reject(new Error(error)),20000);api.stdout.on('data',v=>{out+=v;if(out.includes('\n')){clearTimeout(timer);done(JSON.parse(out.split('\n')[0]).port);}});api.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exit ${code}: ${error}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.setDefaultTimeout(20000);page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
 await page.goto(origin);await page.getByRole('button',{name:'Settings',exact:true}).click();
 await page.getByLabel('Model provider',{exact:true}).waitFor();
 assert.ok(await page.getByRole('button',{name:'Check compatibility',exact:true}).isDisabled());
 await page.getByText('The local profile uses launcher settings.',{exact:false}).waitFor();
 assert.ok((await page.getByLabel('Model provider',{exact:true}).locator('option:checked').textContent()).includes('launcher settings'));
 assert.equal(providerCalls.filter(v=>v.method==='POST').length,0);
 await page.getByText('Add or replace a provider',{exact:true}).click();
 assert.ok(await page.getByRole('button',{name:'Save provider',exact:true}).isDisabled());
 await page.getByText('Enter a profile ID to enable Save provider.',{exact:true}).waitFor();
 await page.getByLabel('Provider profile ID',{exact:true}).fill('fixture-proxy');
 await page.getByLabel('Provider endpoint',{exact:true}).fill('');
 assert.ok(await page.getByRole('button',{name:'Save provider',exact:true}).isDisabled());
 await page.getByText('Enter an endpoint to enable Save provider.',{exact:true}).waitFor();
 await page.getByLabel('Provider endpoint',{exact:true}).fill(`http://127.0.0.1:${provider.address().port}/v1`);
 await page.getByLabel('Provider default model',{exact:true}).fill('fixture:small');
 await page.getByLabel('Provider kind',{exact:true}).selectOption('gateway');
 await page.getByLabel('Provider data allowance',{exact:true}).selectOption('raw');
 await page.getByLabel('Provider credential reference',{exact:true}).fill('env:M1_BROWSER_KEY');
 await page.getByLabel('Provider profile ID',{exact:true}).fill('local');
 await page.getByRole('button',{name:'Save provider',exact:true}).click();
 await page.getByText('The ID local is reserved for launcher settings.',{exact:false}).waitFor();
 assert.equal(apiCalls.filter(v=>v.url==='/api/v1/providers/save').length,0);
 await page.getByLabel('Provider profile ID',{exact:true}).fill('fixture-proxy');
 await page.route('**/api/v1/providers/save',route=>route.fulfill({status:409,contentType:'application/json',body:'{"error":"Provider settings changed; refresh before applying"}'}),{times:1});
 await page.getByRole('button',{name:'Save provider',exact:true}).click();
 await page.locator('.model-provider-editor').getByRole('alert').filter({hasText:'Provider settings changed'}).waitFor();
 await page.getByRole('button',{name:'Save provider',exact:true}).click();
 await page.getByText('Provider saved.',{exact:false}).waitFor();
 // A second saved profile may use the identical endpoint and credential reference.
 await page.getByLabel('Provider profile ID',{exact:true}).fill('fixture-alias');
 await page.getByRole('button',{name:'Save provider',exact:true}).click();
 await page.getByText('Provider saved.',{exact:false}).waitFor();
 await page.getByLabel('Model provider',{exact:true}).locator('option[value="fixture-alias"]').waitFor({state:'attached'});
 assert.equal(providerCalls.filter(v=>v.method==='POST').length,0);
 await page.getByLabel('Model provider',{exact:true}).selectOption('fixture-proxy');
 assert.ok(await page.getByRole('button',{name:'Check compatibility',exact:true}).isDisabled());
 await page.getByText('Click Use provider to apply the chosen profile',{exact:false}).waitFor();
 await page.getByRole('button',{name:'Use provider',exact:true}).click();
 await page.getByText('Provider selected for new requests.',{exact:false}).waitFor();
 await page.getByRole('button',{name:'Check compatibility',exact:true}).click();
 await page.getByText('Synthetic check passed: json_object.',{exact:false}).waitFor();
 assert.equal(providerCalls.filter(v=>v.method==='POST').length,2);
 await page.getByLabel('Provider model',{exact:true}).selectOption('fixture:other');
 await page.getByRole('button',{name:'Use selected model',exact:true}).click();
 await page.getByText('Model selected for new requests.',{exact:false}).waitFor();
 await page.reload();await page.getByRole('button',{name:'Settings',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('select[aria-label="Model provider"]')?.value==='fixture-proxy');
 assert.equal(await page.getByLabel('Provider model',{exact:true}).inputValue(),'fixture:other');
 assert.ok(!(await page.content()).includes(key));
 await page.locator('.model-service-settings').evaluate(el=>{const panel=el.closest('.settings-workspace');panel.scrollTop+=el.getBoundingClientRect().top-panel.getBoundingClientRect().top-110;});
 assert.ok((await page.getByRole('button',{name:'Use provider',exact:true}).boundingBox()).height>=32);
 await page.screenshot({path:'/tmp/actioncharter-m1-settings.png'});
 const cli=await new Promise((done,reject)=>{const p=spawn(resolve(repo,'.venv/bin/python'),['-m','geoagent_harness.apps.cli.main','models','profiles','--project-root',root],{cwd:repo,env});let out='',err='';p.stdout.on('data',v=>out+=v);p.stderr.on('data',v=>err+=v);p.on('exit',code=>code===0?done(JSON.parse(out)):reject(new Error(err)));});
 assert.equal(cli.selected_profile,'fixture-proxy');assert.ok(!JSON.stringify(cli).includes(key));
 if(testEgress){
  await page.getByText('Add or replace a provider',{exact:true}).click();
  await page.getByLabel('Provider profile ID',{exact:true}).fill('fixture-restricted');
  await page.getByLabel('Provider endpoint',{exact:true}).fill(`http://127.0.0.1:${provider.address().port}/v1`);
  await page.getByLabel('Provider default model',{exact:true}).fill('fixture:small');
  await page.getByLabel('Provider credential reference',{exact:true}).fill('env:M1_BROWSER_KEY');
  await page.getByLabel('Provider data allowance',{exact:true}).selectOption('none');
  await page.getByRole('button',{name:'Save provider',exact:true}).click();
  await page.getByText('Provider saved.',{exact:false}).waitFor();
  await page.getByLabel('Model provider',{exact:true}).selectOption('fixture-restricted');
  await page.getByRole('button',{name:'Use provider',exact:true}).click();
  await page.getByText('Active provider: fixture-restricted · Effective data allowance: none',{exact:true}).waitFor();
  await page.getByRole('button',{name:'Check compatibility',exact:true}).click();
  await page.getByText('Synthetic check passed: json_object.',{exact:false}).waitFor();
  expectedSyntheticCalls=4;
  assert.equal(providerCalls.filter(v=>v.method==='POST').length,expectedSyntheticCalls);
  await page.getByRole('button',{name:'Close settings',exact:true}).click();
  if(!await page.getByRole('textbox',{name:'Message Planner'}).isVisible())await page.getByRole('button',{name:'Planner agent',exact:true}).click();
  const blocked=page.waitForResponse(r=>r.url().endsWith('/api/v1/planner/submit')&&r.request().method()==='POST'&&r.request().postDataJSON()?.action==='submit');
  await page.getByRole('textbox',{name:'Message Planner'}).fill('Explain what a read-only inspection of sample_orders.csv would establish. Propose only inspection, without execution.');
  await page.locator('.planner-composer button[type=submit]').click();
  const blockedResponse=await blocked;assert.equal(blockedResponse.status(),403);
  const rejection=await blockedResponse.json();assert.equal(rejection.code,'model_data_class_blocked');
  assert.ok(rejection.retry_guidance.includes('allowance')&&!rejection.retry_guidance.includes('HTTP 404'));
  assert.equal(providerCalls.filter(v=>v.method==='POST').length,expectedSyntheticCalls);
  await page.getByRole('button',{name:'View request diagnostics',exact:true}).click();
  const call=page.locator('.request-diagnostics details').filter({has:page.locator('dt').filter({hasText:'Required data class'})}).first();
  await call.locator('summary').first().click();
  await call.getByText('Not attempted',{exact:true}).waitFor();
  await call.getByText('fixture-restricted',{exact:true}).waitFor();
  await call.getByText('blocked',{exact:true}).waitFor();
  assert.ok(!(await page.content()).includes(key));
  await page.screenshot({path:'/tmp/actioncharter-m2-blocked.png'});
  await page.getByRole('button',{name:'Settings',exact:true}).click();
 }
 await page.getByLabel('Model provider',{exact:true}).selectOption('local');await page.getByRole('button',{name:'Use provider',exact:true}).click();
 await page.getByText('Provider selected for new requests.',{exact:false}).waitFor();
 assert.equal(await page.getByLabel('Provider model',{exact:true}).inputValue(),'fixture:small');
 assert.equal(providerCalls.filter(v=>v.method==='POST').length,expectedSyntheticCalls);
 assert.equal(apiCalls.filter(v=>v.method==='POST'&&(/workflow\/(authorize|execute)$/.test(v.url)||(v.url==='/api/v1/workflow/runs'&&['start','cancel','resume','retry'].includes(v.action))||(v.url==='/api/v1/planner/conversation'&&v.action==='turn')||(v.url==='/api/v1/planner/submit'&&v.action==='submit'))).length,testEgress?1:0);
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'passed',profile_persisted:true,shared_endpoint_profiles:true,inline_save_errors:true,disabled_check_explained:true,cli_parity:true,synthetic_calls:expectedSyntheticCalls,egress_block_verified:testEgress,workflow_calls:0,page_errors:0,secret_leaks:0}));
}finally{
 if(browser)await browser.close();if(api){api.kill('SIGTERM');await new Promise(done=>api.once('exit',done));}
 await new Promise(done=>frontend.close(done));await new Promise(done=>provider.close(done));await rm(root,{recursive:true,force:true});
}
