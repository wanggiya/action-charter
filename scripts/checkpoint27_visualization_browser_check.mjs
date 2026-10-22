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
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-visualization-'));
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
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--calculation-fixture','--visualization-fixture'],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'true',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});
 let stderr='';child.stderr.on('data',data=>stderr+=data);
 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error(`API startup timeout: ${stderr}`)),20000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exited ${code}: ${stderr}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
 const visualization=page.locator('.inspector .recorded-visualization');
 const operations=page.getByRole('region',{name:'Workflow operations'});
 const generate=async(message)=>{
   await page.getByRole('textbox',{name:'Message Planner'}).fill(message);
   await page.locator('.planner-composer button[type=submit]').click();
   await page.locator('[data-operation-node="planned_step_1"]').waitFor({timeout:20000});
 };
 const closeOutcome=async()=>{
   await page.locator('.workflow-outcome-panel .outcome-step').first().waitFor({timeout:30000});
   await page.getByRole('button',{name:'Close outcome',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('[data-critic-node]')?.getAttribute('data-critic-state')==='Reviewed');
 };
 await page.goto(origin);
 await generate('Inspect sample_orders.csv. Calculate doubled as amount multiplied by 2, preserve original columns and propagate missing values. Save to a fresh CSV. Do not execute yet.');
 await operations.getByRole('button',{name:/Calculate table columns/}).click();
 assert.equal(await visualization.count(),0);
 cases.push('Proposals do not invent charts or map geometry');
 await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
 await page.locator('.workflow-authorization-form textarea').fill('Only fresh temporary CSV fixture outputs.');
 await page.locator('.workflow-authorization-form button[type=submit]').click();
 await page.locator('.authorization-duration').waitFor();
 await page.locator('.workflow-review-panel .execute-button').click();
 await closeOutcome();
 await operations.getByRole('button',{name:/Calculate table columns/}).click();
 const modelCalls=await readFile(resolve(root,'model-calls.jsonl'),'utf8');
 const starts=calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='start').length;
 await visualization.getByText('Chart recorded data',{exact:true}).click();
 assert.equal(await visualization.locator('.recorded-chart').count(),1,await visualization.innerText());
 await visualization.getByLabel('Value',{exact:true}).selectOption('doubled');
 await visualization.getByLabel('Category',{exact:true}).selectOption('region');
 assert.deepEqual(await visualization.locator('[data-chart-value]').evaluateAll(nodes=>nodes.map(node=>Number(node.getAttribute('data-chart-value')))),[20,40,80,10,60]);
 assert((await visualization.textContent()).includes('1 omitted'));
 assert((await visualization.textContent()).includes('no grouping or totals'));
 cases.push('Actual calculated CSV produces correct per-row bars, source/run identity and an explicit missing-value/sample boundary');
 await visualization.getByRole('combobox',{name:'Chart',exact:true}).selectOption('scatter');
 await visualization.getByLabel('X axis',{exact:true}).selectOption('amount');
 assert.equal(await visualization.locator('svg circle').count(),5);
 assert.equal(await readFile(resolve(root,'model-calls.jsonl'),'utf8'),modelCalls);
 assert.equal(calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='start').length,starts);
 cases.push('Scatter selection and opening charts add no model calls or executions');
 await visualization.screenshot({path:'/tmp/actioncharter-recorded-chart.png'});
 const outputs=await readdir(resolve(root,'data/output'));
 await writeFile(resolve(root,'data/output',outputs[0]),'amount,doubled\n999,1998\n');
 await page.reload();
 await operations.getByRole('button',{name:/Calculate table columns/}).click();
 await visualization.getByText('Chart recorded data',{exact:true}).click();
 await visualization.getByLabel('Value',{exact:true}).selectOption('doubled');
 assert.deepEqual(await visualization.locator('[data-chart-value]').evaluateAll(nodes=>nodes.map(node=>Number(node.getAttribute('data-chart-value')))),[20,40,80,10,60]);
 cases.push('Reload restores the recorded values even if the current output file changes; no silent file reread');
 let projectedMode='bounded';
 const boundedResponse=async route=>{
   if(route.request().postDataJSON().action!=='read'){await route.continue();return;}
   const response=await route.fetch();const record=await response.json();
   const step=record.steps.find(step=>step.skill_id==='calculate_csv_columns');
   if(step)step.outcome={...step.outcome,columns:['category','value'],row_count:1000,
     preview:Array.from({length:30},(_,i)=>({category:i===0?'<img src=x onerror=alert(1)>':`row ${i}`,value:projectedMode==='mixed'?'not numeric':String(i-10)}))};
   await route.fulfill({response,json:record});
 };
 await page.route('**/api/v1/workflow/runs',boundedResponse);
 await page.getByRole('button',{name:'Refresh recorded results',exact:true}).click();
 await visualization.getByText('Chart recorded data',{exact:true}).click();
 assert.equal(await visualization.locator('[data-chart-value]').count(),20);
 assert.equal(await visualization.locator('img').count(),0);
 assert((await visualization.textContent()).includes('20 preview rows'));
 assert((await visualization.locator('svg').textContent()).includes('<img src=x'));
 assert((await visualization.textContent()).includes('1000 recorded rows'));
 await visualization.getByRole('combobox',{name:'Chart',exact:true}).selectOption('pie');
 assert((await visualization.textContent()).includes('require non-negative values and a positive total'));
 assert.equal(await visualization.locator('svg').count(),0);
 await visualization.getByRole('combobox',{name:'Chart',exact:true}).selectOption('box');
 assert((await visualization.locator('svg title').textContent()).includes('-10, -5.25, -0.5, 4.25, 9'));
 await visualization.getByRole('combobox',{name:'Chart',exact:true}).selectOption('summary');
 assert((await visualization.locator('.chart-summary').textContent()).includes('Maximum9'));
 cases.push('Signed data refuses pie rendering and produces the expected linear quartiles and signed summary statistics');
 projectedMode='mixed';
 await page.getByRole('button',{name:'Refresh recorded results',exact:true}).click();
 await visualization.getByText('Chart recorded data',{exact:true}).click();
 assert((await visualization.textContent()).includes('No chartable numeric column'));
 assert.equal(await visualization.locator('svg').count(),0);
 await visualization.getByRole('button',{name:'Count categories',exact:true}).click();
 await visualization.getByLabel('Category',{exact:true}).selectOption('value');
 await visualization.getByRole('combobox',{name:'Chart',exact:true}).selectOption('donut');
 assert.equal(await visualization.locator('svg path[fill-rule=evenodd]').count(),1);
 assert.equal(await visualization.locator('svg [data-chart-value="20"]').count(),1);
 cases.push('Text-only category counts produce a single complete donut ring with an explicit sampled scope');
 await page.unroute('**/api/v1/workflow/runs',boundedResponse);
 cases.push('Read-response boundary fixtures cap chart rows, render HTML-looking labels literally and explain unsupported mixed text');
 await page.getByRole('button',{name:'Planner agent',exact:true}).click();
 await page.getByRole('button',{name:'New chat',exact:true}).click();
 assert.equal(await visualization.count(),0);
 await writeFile(resolve(root,'vector-visualization'),'fixture only');
 await generate('Inspect sample_points.geojson. Return feature count, fields and CRS. No writes.');
 await operations.getByRole('button',{name:/Inspect vector dataset/}).click();
 assert.equal(await visualization.count(),0);
 await page.getByRole('button',{name:'Execute',exact:true}).first().click();
 await closeOutcome();
 await operations.getByRole('button',{name:/Inspect vector dataset/}).click();
 await visualization.getByText('Map recorded geometry',{exact:true}).click();
 assert.equal(await visualization.getByRole('img',{name:'Recorded WGS84 point map'}).locator('circle').count(),2);
 assert((await visualization.textContent()).includes('2 features shown'));
 assert((await visualization.textContent()).includes('CRS'));
 assert((await visualization.locator('svg').textContent()).includes('-71.0589, 42.3601'));
 await visualization.screenshot({path:'/tmp/actioncharter-recorded-map.png'});
 await writeFile(resolve(root,'data/input/sample_points.geojson'),'source removed after inspection');
 await page.reload();
 await operations.getByRole('button',{name:/Inspect vector dataset/}).click();
 await visualization.getByText('Map recorded geometry',{exact:true}).click();
 assert.equal(await visualization.locator('svg circle').count(),2);
 cases.push('Actual vector inspection saves known WGS84 points; an offline map restores without reading a changed source');
 const legacyResponse=async route=>{
   if(route.request().postDataJSON().action!=='read'){await route.continue();return;}
   const response=await route.fetch();const record=await response.json();
   for(const step of record.steps??[])if(step.skill_id==='inspect_vector'&&step.outcome)delete step.outcome.spatial_preview;
   await route.fulfill({response,json:record});
 };
 await page.route('**/api/v1/workflow/runs',legacyResponse);
 await page.getByRole('button',{name:'Refresh recorded results',exact:true}).click();
 await visualization.getByText('Map recorded geometry',{exact:true}).click();
 assert.equal(await visualization.locator('svg').count(),0);
 assert((await visualization.textContent()).includes('Older runs must not inherit geometry'));
 await page.unroute('**/api/v1/workflow/runs',legacyResponse);
 cases.push('A legacy read-response fixture without saved geometry shows unavailable rather than borrowing current-file geometry');
 await page.getByRole('button',{name:'Planner agent',exact:true}).click();
 await page.getByRole('button',{name:'New chat',exact:true}).click();
 await writeFile(resolve(root,'data/input/sample_points.geojson'),JSON.stringify({type:'FeatureCollection',crs:{type:'name',properties:{name:'EPSG:3857'}},features:[{type:'Feature',properties:{},geometry:{type:'Point',coordinates:[100000,100000]}}]}));
 await generate('Inspect sample_points.geojson. Return feature count, fields and CRS. No writes.');
 await page.getByRole('button',{name:'Execute',exact:true}).first().click();
 await closeOutcome();
 await operations.getByRole('button',{name:/Inspect vector dataset/}).click();
 await visualization.getByText('Map recorded geometry',{exact:true}).click();
 assert.equal(await visualization.locator('svg').count(),0);
 assert((await visualization.textContent()).includes('requires declared WGS84'));
 cases.push('Actual projected-CRS inspection remains valid while the point map honestly reports unsupported CRS without reprojection');
 assert.deepEqual(errors,[]);
 assert.equal(calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='start').length,3);
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,live_service_calls:0,page_errors:errors},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls},null,2));throw error;}
finally{if(browser)await browser.close();child?.kill();await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
