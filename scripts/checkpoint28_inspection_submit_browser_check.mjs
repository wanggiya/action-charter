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
let apiPort,child,browser,stalePlanner=false; const calls=[],errors=[],cases=[];
const frontend=createServer(async(req,res)=>{
 try {
  if(req.url.startsWith('/api/')) {
   if(stalePlanner&&req.url==='/api/v1/health') {
    res.writeHead(200,{'Content-Type':'application/json'});
    res.end(JSON.stringify({planner_contract_revision:'capability-pilot-v1',inspection_on_send_revision:'bounded-local-v2'}));return;
   }
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
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--planning-task-fixture','--csv-discovery-fixture'],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'false',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});
 let stderr='';child.stderr.on('data',data=>stderr+=data);
 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error(`API startup timeout: ${stderr}`)),20000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exited ${code}: ${stderr}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
 const send=async(message)=>{await page.getByRole('textbox',{name:'Message Planner'}).fill(message);await page.locator('.planner-composer button[type=submit]').click();await page.waitForFunction(()=>document.querySelector('.planner-composer button[type=submit]')?.textContent?.includes('Send'),{},{timeout:30000});};
 const executionCalls=()=>calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='start').length;
 const authorizationCalls=()=>calls.filter(call=>call.path==='/api/v1/workflow/authorize').length;
 await page.goto(origin);
 const message='Inspect sample_orders.csv. Return row count and column names. No writes.';
 const countRuns=async()=>{try{return (await readdir(resolve(root,'workflow-state/interface-runs'))).filter(name=>name.endsWith('.json')).length;}catch{return 0;}};
 const modelCalls=async()=>{try{return (await readFile(resolve(root,'model-calls.jsonl'),'utf8')).trim().split('\n').filter(Boolean).length;}catch{return 0;}};
 const setting=page.getByRole('switch',{name:'Inspect on send',exact:true});
 const openPlanner=async()=>{if(!await page.getByRole('textbox',{name:'Message Planner'}).isVisible())await page.getByRole('button',{name:'Planner agent',exact:true}).click();};
 const toggleMode=async(on)=>{await page.getByRole('button',{name:'Conversation settings',exact:true}).click();await setting.waitFor();if((await setting.getAttribute('aria-checked'))!==String(on))await setting.click();await page.keyboard.press('Escape');};
 const plannerPosts=()=>calls.filter(call=>call.method==='POST'&&['turn','submit'].includes(call.action)&&['/api/v1/planner/submit','/api/v1/planner/conversation'].includes(call.path)).length;
 const postsBefore=plannerPosts();stalePlanner=true;
 await send(message);
 await page.getByText(/Startup must show Planner contract revision: inspection-source-v2/).waitFor();
 assert.equal(plannerPosts(),postsBefore);assert.equal(await countRuns(),0);
 stalePlanner=false;
 cases.push('Old Planner contract blocks submission before model calls or execution');
 await send(message);
 await page.locator('[data-operation-skill="inspect_csv"]').waitFor();
 assert.equal(await countRuns(),0);
 assert.equal(await modelCalls(),0);
 await page.getByText('Exact inspection workflow · no model call',{exact:true}).waitFor();
 cases.push('Default OFF sends a proposal without a run');
 await toggleMode(true);
 await page.getByRole('button',{name:'New chat',exact:false}).click();
 await page.getByRole('button',{name:'Conversation settings',exact:true}).click();
 assert.equal(await setting.getAttribute('aria-checked'),'true');await page.keyboard.press('Escape');
 await send(message);
 await page.locator('.results-workspace .outcome-step').first().waitFor({timeout:30000});
 assert.equal(await countRuns(),1);
 assert.equal(authorizationCalls(),0);
 assert.equal(executionCalls(),0); // dispatch is internal to the explicit submission
 assert.equal((await readdir(resolve(root,'data/output'))).length,0);
 const first=JSON.parse(await readFile(resolve(root,'workflow-state/interface-runs',(await readdir(resolve(root,'workflow-state/interface-runs'))).find(name=>name.endsWith('.json'))),'utf8'));
 assert.equal(first.status,'completed');assert.equal(first.steps[0].outcome.row_count,6);
 cases.push('One send with automatic skills produces a recorded CSV outcome, no Authorize or Execute');
 await openPlanner();
 await page.getByRole('combobox',{name:'Saved planning conversation',exact:true}).waitFor();
 assert.equal(await page.locator('.planner-dialogue footer').textContent().then(text=>text.includes('Current plan saved')),false);
 for(const size of [{width:1600,height:1000},{width:1100,height:760}]){
  await page.setViewportSize(size);
  const picker=await page.locator('.planner-session-picker').boundingBox();
  const footer=await page.locator('.planner-dialogue footer').boundingBox();
  assert.ok(picker&&footer&&picker.y+picker.height<=footer.y,'Chat selector and composer footer must not overlap');
 }
 await page.setViewportSize({width:1600,height:1000});
 cases.push('Outcome keeps the chat selector separate from the footer without a duplicate saved-plan title');

 const submits=calls.filter(call=>call.path==='/api/v1/planner/submit'&&call.action==='submit').length;
 await page.reload();await page.getByRole('textbox',{name:'Message Planner'}).waitFor();
 await page.locator('[data-operation-skill="inspect_csv"]').waitFor();
 assert.equal(await countRuns(),1);
 assert.equal(calls.filter(call=>call.path==='/api/v1/planner/submit'&&call.action==='submit').length,submits);
 cases.push('Reload restores scope without submitting or running again');
 await openPlanner();await page.getByRole('button',{name:'New chat',exact:false}).click();
 await send('CSV task inspection sample_orders.csv, select order_id and region to a fresh CSV. Do not execute.');
 await page.locator('[data-operation-skill="select_csv_columns"]').waitFor();
 assert.equal(await countRuns(),1);assert.equal((await readdir(resolve(root,'data/output'))).length,0);
 assert.equal(await page.locator('.top-actions .execute-button').isDisabled(),true);
 cases.push('Mode ON keeps complete write proposals and never runs their inspection prefix');
 await page.getByRole('button',{name:'New chat',exact:false}).click();
 let dropped=false;
 await page.route('**/api/v1/planner/submit',async route=>{
   const body=route.request().postDataJSON();
   if(body.action==='submit'&&!dropped){dropped=true;await route.fetch();await route.abort('failed');}else await route.continue();
 });
 await send(message);
 await page.getByRole('button',{name:'Check last submission · no retry',exact:true}).waitFor();
 await page.getByRole('button',{name:'Check last submission · no retry',exact:true}).click();
 await page.locator('.results-workspace .outcome-step').first().waitFor({timeout:30000});
 assert.equal(await countRuns(),2);
 await page.unroute('**/api/v1/planner/submit');
 cases.push('Lost response reconciles the original recorded run without another submission');
 await openPlanner();await toggleMode(false);await page.getByRole('button',{name:'New chat',exact:false}).click();
 await send(message);await page.locator('[data-operation-skill="inspect_csv"]').waitFor();
 assert.equal(await countRuns(),2);
 cases.push('Switch OFF restores proposal-only sending across chats');
 await toggleMode(true);
 for(const [name,skill] of [['sample_points.geojson','inspect_vector'],['sample_dem.tif','inspect_raster']]){
  await page.getByRole('button',{name:'New chat',exact:false}).click();
  await send(name.endsWith('.csv')?message:`Inspect ${name}. Return CRS. No writes.`);
  await page.locator(`[data-operation-skill="${skill}"]`).waitFor();
  await page.locator('.results-workspace .outcome-step').first().waitFor({timeout:30000});
  const runs=await readdir(resolve(root,'workflow-state/interface-runs'));
  const values=await Promise.all(runs.filter(name=>name.endsWith('.json')).map(async name=>JSON.parse(await readFile(resolve(root,'workflow-state/interface-runs',name),'utf8'))));
  const matching=values.find(run=>run.steps[0]?.skill_id===skill);
  assert.equal(matching?.status,'completed');
  const outcome=matching.steps[0].outcome;
  assert.equal(outcome.source,`data/input/${name}`);
  if(skill==='inspect_vector'){
   assert.equal(outcome.layers[0].crs,'EPSG:4326');
   assert.ok(outcome.layers[0].feature_count>0);
   assert.ok(outcome.spatial_preview);
  }else{
   assert.equal(outcome.crs,'EPSG:4326');
   assert.ok(outcome.width>0&&outcome.height>0);
  }
  await openPlanner();
 }
 assert.equal(await countRuns(),4);
 assert.equal(authorizationCalls(),0);assert.equal(executionCalls(),0);
 cases.push('Vector and raster send open recorded spatial outcomes without Authorize or Execute');
 const sameChat=await page.evaluate(()=>localStorage.getItem('actioncharter:planner-conversation:v1'));
 for(const [name,skill] of [['sample_points.geojson','inspect_vector'],['sample_dem.tif','inspect_raster'],['sample_orders.csv','inspect_csv']]){
  await send(name.endsWith('.csv')?message:`Inspect ${name}. Return CRS. No writes.`);
  await page.locator(`[data-operation-skill="${skill}"]`).waitFor();
  await page.waitForFunction(skill=>document.querySelector('.results-workspace .result-operation-heading')?.textContent?.includes(skill),skill==='inspect_csv'?'Inspect CSV table':skill==='inspect_vector'?'Inspect vector dataset':'Inspect raster dataset',{timeout:30000});
  assert.equal(await page.evaluate(()=>localStorage.getItem('actioncharter:planner-conversation:v1')),sameChat);
 }
 assert.equal(await countRuns(),7);
 cases.push('One chat switches GeoJSON → TIFF → CSV and automatically shows each new operation Outcome');
 const countBeforeHistory=await countRuns();
 const postsBeforeHistory=plannerPosts();
 const historyFiles=await readdir(resolve(root,'workflow-state/interface-runs'));
 const historyRecords=await Promise.all(historyFiles.filter(name=>name.endsWith('.json')).map(async name=>JSON.parse(await readFile(resolve(root,'workflow-state/interface-runs',name),'utf8'))));
 const earlierRaster=historyRecords.filter(run=>run.conversation_id===sameChat&&run.steps[0]?.skill_id==='inspect_raster').sort((a,b)=>b.started_at.localeCompare(a.started_at))[0];
 assert.ok(earlierRaster);
 await page.getByRole('button',{name:'Execution History',exact:true}).click();
 const history=page.getByRole('region',{name:'Saved workflow runs',exact:true});
 await history.getByRole('button',{name:'Workflow runs · cancellation and recovery',exact:true}).waitFor();
 const rasterCard=history.locator(`[data-history-run="${earlierRaster.run_id}"]`);
 await rasterCard.waitFor();
 assert.match(await rasterCard.textContent(),/sample_dem.tif/);
 assert.match(await rasterCard.textContent(),/Inspect raster dataset/);
 await rasterCard.getByRole('button',{name:'View outcome',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.results-workspace .result-operation-heading')?.textContent?.includes('Inspect raster dataset'));
 await page.locator('.results-provenance summary').click();
 assert.match(await page.locator('.results-provenance').textContent(),new RegExp(earlierRaster.run_id));
 assert.match(await page.locator('.results-provenance').textContent(),/data\/input\/sample_dem.tif/);
 assert.equal(await countRuns(),countBeforeHistory);
 assert.equal(plannerPosts(),postsBeforeHistory);
 await page.getByRole('button',{name:'Outcome',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.results-workspace .result-operation-heading')?.textContent?.includes('Inspect CSV table'));
 assert.equal(await countRuns(),countBeforeHistory);
 cases.push('Execution History directly lists named saved runs and reopens TIFF evidence without replacing the current CSV workflow or executing');
 await page.getByRole('button',{name:'Execution History',exact:true}).click();
 await page.getByRole('button',{name:'Workflow runs · cancellation and recovery',exact:true}).click();
 await page.getByRole('heading',{name:'Workflow runs',exact:true}).waitFor();
 assert.equal(await countRuns(),countBeforeHistory);
 cases.push('Workflow run management is directly accessible at the top of Execution History');



 await openPlanner();
 await page.getByRole('button',{name:'New chat',exact:false}).click();
 const beforeLarge=await countRuns();
 await writeFile(resolve(root,'hold-discovery'),'hold only in temporary fixture');
 await send('Inspect large_orders.csv. Return row count and column names. No writes.');
 await page.getByText('Characteristics ready · verifying full file…',{exact:true}).waitFor({timeout:30000});
 const liveFiles=await readdir(resolve(root,'workflow-state/interface-runs'));
 const liveRecords=await Promise.all(liveFiles.filter(name=>name.endsWith('.json')).map(async name=>JSON.parse(await readFile(resolve(root,'workflow-state/interface-runs',name),'utf8'))));
 const largeRun=liveRecords.find(run=>run.steps[0]?.arguments.path==='data/input/large_orders.csv');
 assert.equal(largeRun.status,'running');assert.equal(largeRun.steps[0].outcome.row_count,null);
 assert.equal(largeRun.steps[0].outcome.source_sha256,undefined);
 await page.getByRole('tab',{name:'Table',exact:true}).click();
 assert.match(await page.locator('.results-workspace').textContent(),/001/);
 assert.equal(await page.getByRole('button',{name:'Explore complete CSV',exact:true}).count(),0);
 await rm(resolve(root,'hold-discovery'));
 await page.getByText('Complete CSV scan · SHA-256 recorded',{exact:true}).waitFor({timeout:30000});
 const completedLarge=JSON.parse(await readFile(resolve(root,'workflow-state/interface-runs',largeRun.run_id+'.json'),'utf8'));
 const {createHash}=await import('node:crypto');
 assert.equal(completedLarge.steps[0].outcome.row_count,12000);
 assert.equal(completedLarge.steps[0].outcome.source_sha256,createHash('sha256').update(await readFile(resolve(root,'data/input/large_orders.csv'))).digest('hex'));
 assert.equal(await countRuns(),beforeLarge+1);
 assert.equal(authorizationCalls(),0);assert.equal(executionCalls(),0);
 await page.reload();
 await page.getByRole('button',{name:'Outcome',exact:true}).click();
 await page.getByText('Complete CSV scan · SHA-256 recorded',{exact:true}).waitFor({timeout:30000});
 assert.equal(await countRuns(),beforeLarge+1);
 cases.push('Large CSV shows provisional characteristics and sample before hashing, then exact counts and SHA-256; reload never repeats the run');

 await openPlanner();
 await page.getByRole('button',{name:'New chat',exact:false}).click();
 const beforeSpatial=await countRuns();
 await writeFile(resolve(root,'hold-discovery'),'temporary spatial progress gate');
 await send('Inspect large_terrain.tif. Return dimensions, bands and CRS. No writes.');
 await page.getByText('Characteristics ready · verifying full file…',{exact:true}).waitFor({timeout:30000});
 assert.match(await page.locator('.discovery-status').textContent(),/2048 × 2048/);
 await page.getByRole('tab',{name:'Map',exact:true}).click();
 await page.getByText(/This source exceeds the bounded viewer/).waitFor();
 await page.getByRole('tab',{name:'Overview',exact:true}).click();
 await rm(resolve(root,'hold-discovery'));
 await page.getByText('Spatial metadata · package SHA-256 recorded',{exact:true}).waitFor({timeout:30000});
 const spatialRecords=await Promise.all((await readdir(resolve(root,'workflow-state/interface-runs'))).filter(name=>name.endsWith('.json')).map(async name=>JSON.parse(await readFile(resolve(root,'workflow-state/interface-runs',name),'utf8'))));
 const spatialRun=spatialRecords.find(run=>run.steps[0]?.arguments.path==='data/input/large_terrain.tif');
 assert.equal(spatialRun.status,'completed');
 const componentHash=createHash('sha256').update(await readFile(resolve(root,'data/input/large_terrain.tif'))).digest('hex');
 assert.equal(spatialRun.steps[0].outcome.source_manifest['data/input/large_terrain.tif'],componentHash);
 assert.equal(spatialRun.steps[0].outcome.discovery.bytes_hashed,(await readFile(resolve(root,'data/input/large_terrain.tif'))).length);
 await page.reload();
 await page.getByRole('button',{name:'Outcome',exact:true}).click();
 await page.getByText('Spatial metadata · package SHA-256 recorded',{exact:true}).waitFor({timeout:30000});
 assert.equal(await countRuns(),beforeSpatial+1);
 assert.equal(authorizationCalls(),0);assert.equal(executionCalls(),0);
 cases.push('Large TIFF shows preliminary dimensions before package hashing; bounded Map limit is explicit and reload preserves results without replay');

 await openPlanner();await page.getByRole('button',{name:'New chat',exact:false}).click();
 const beforeBatch=await countRuns(),beforeBatchModels=await modelCalls();
 await send('Inspect sample_orders.csv and sample_dem.tif. Return metadata. No writes.');
 const batchPicker=page.locator('.results-workspace').getByRole('combobox',{name:'Operation result',exact:true});
 await page.waitForFunction(()=>document.querySelector('select[aria-label="Operation result"]')?.options.length===2);
 await batchPicker.selectOption('step_2');
 await page.getByText('Spatial metadata · package SHA-256 recorded',{exact:true}).waitFor({timeout:30000});
 await page.getByRole('tab',{name:'Overview',exact:true}).click();
 assert.match(await page.locator('.raster-metadata').textContent(),/GTiff/);
 await batchPicker.selectOption('step_1');
 await page.getByText('Complete CSV scan · SHA-256 recorded',{exact:true}).waitFor();
 assert.equal(await countRuns(),beforeBatch+1);assert.equal(await modelCalls(),beforeBatchModels);
 assert.equal(authorizationCalls(),0);assert.equal(executionCalls(),0);
 await page.reload();await page.getByRole('button',{name:'Outcome',exact:true}).click();
 await batchPicker.waitFor();
 assert.equal(await batchPicker.locator('option').count(),2);
 assert.equal(await countRuns(),beforeBatch+1);
 cases.push('Exact CSV/TIFF batch has two selectable recorded outcomes, zero model calls and no extra run after reload');

 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,page_errors:errors,live_service_calls:0},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls},null,2));throw error;}
finally{await browser?.close();child?.kill('SIGTERM');await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
