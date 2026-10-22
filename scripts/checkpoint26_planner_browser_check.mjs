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
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-cp26-planner-'));
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
 }catch(error){if(res.headersSent||res.destroyed){res.destroy();}else{res.writeHead(500);res.end(String(error));}}
});
await new Promise(done=>frontend.listen(0,'127.0.0.1',done));
const origin=`http://127.0.0.1:${frontend.address().port}`;
try{
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--recipe-runs-fixture'],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'true',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});
 let stderr='';child.stderr.on('data',data=>stderr+=data);
 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error(`API startup timeout: ${stderr}`)),20000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exited ${code}: ${stderr}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());


 page.setDefaultTimeout(20000);
 const state=()=>page.evaluate(async()=>{const conversation_id=localStorage.getItem('actioncharter:planner-conversation:v1');return (await fetch('/api/v1/planner/conversation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'read',conversation_id})})).json();});
 const send=async(message)=>{await page.getByRole('textbox',{name:'Message Planner'}).fill(message);await page.locator('.planner-composer button[type=submit]').click();await page.waitForFunction(()=>document.querySelector('.planner-composer button[type=submit]')?.textContent?.includes('Send'));};
 const authorize=async()=>{await page.getByRole('button',{name:'Authorize',exact:true}).first().click();await page.locator('.workflow-authorization-form textarea').fill('Only the reviewed temporary CSV fixture outputs.');await page.locator('.workflow-authorization-form button[type=submit]').click();await page.locator('.authorization-duration').waitFor();};
 await page.goto(origin);
 await page.getByRole('button',{name:'Conversation settings',exact:true}).click();
 await page.getByRole('switch',{name:'Chat memory'}).waitFor();
 await page.getByRole('button',{name:'Close conversation settings',exact:true}).click();
 await send('Clean sample_orders.csv: keep region and amount, and replace missing regions with Unknown.');
 await page.locator('[data-operation-node="planned_step_2"]').waitFor();
 let chat=await state();
 const originalSha=chat.planner_result.plan_sha256;
 const originalTargets=chat.planner_result.plan.steps.map(s=>s.arguments.target_path);
 assert.equal(new Set(originalTargets).size,2);
 assert(originalTargets.every(p=>/^data\/output\/result_[a-f0-9]{32}\.csv$/.test(p)));
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 cases.push('One natural-language request discovers a recipe, binds semantic parameters and allocates fresh CSV paths without forms');
 // Exercise camera and node motion against the real mounted graph.
 const canvas=page.locator('.canvas-window');
 await page.getByRole('button',{name:'Flow graph',exact:true}).click();
 await page.getByRole('button',{name:'Fit entire graph',exact:true}).click();
 const cameraBefore=await canvas.evaluate(el=>{const r=el.getBoundingClientRect();const x=el.clientWidth*.45,y=el.clientHeight*.45;return {x,y,clientX:r.left+el.clientLeft+x,clientY:r.top+el.clientTop+y,scale:new DOMMatrixReadOnly(getComputedStyle(el.querySelector('.canvas')).transform).a,left:el.scrollLeft,top:el.scrollTop};});
 const startsBeforeMotion=calls.filter(c=>c.action==='start').length;
 await page.mouse.move(cameraBefore.clientX,cameraBefore.clientY);
 await page.mouse.wheel(0,-180);
 await page.waitForFunction(()=>!document.querySelector('.canvas-window').classList.contains('is-zooming'));
 const cameraAfter=await canvas.evaluate(el=>({scale:new DOMMatrixReadOnly(getComputedStyle(el.querySelector('.canvas')).transform).a,left:el.scrollLeft,top:el.scrollTop,transition:getComputedStyle(el.querySelector('.canvas')).transitionDuration}));
 assert(cameraAfter.scale>cameraBefore.scale);
 const expectedLeft=Math.max(0,Math.min((cameraBefore.left+cameraBefore.x)*cameraAfter.scale/cameraBefore.scale-cameraBefore.x,await canvas.evaluate(el=>el.scrollWidth-el.clientWidth)));
 assert(Math.abs(cameraAfter.left-expectedLeft)<2,JSON.stringify({cameraBefore,cameraAfter,expectedLeft}));
 assert.equal(cameraAfter.transition,'0s');
 // Small trackpad deltas must not cause the old fixed eight-percent jump.
 await canvas.dispatchEvent('wheel',{deltaY:-1,clientX:cameraBefore.clientX,clientY:cameraBefore.clientY});
 await page.waitForFunction(()=>!document.querySelector('.canvas-window').classList.contains('is-zooming'));
 const fineScale=await canvas.locator('.canvas').evaluate(el=>new DOMMatrixReadOnly(getComputedStyle(el).transform).a);
 assert(fineScale>cameraAfter.scale && fineScale-cameraAfter.scale<.01);
 const moving=page.locator('[data-operation-node="planned_step_1"]');
 await moving.scrollIntoViewIfNeeded();
 const bounds=await moving.boundingBox();
 const hit=await page.evaluate(({x,y})=>{const element=document.elementFromPoint(x,y);return {node:element?.closest('[data-operation-node]')?.getAttribute('data-operation-node'),html:element?.outerHTML.slice(0,250)};},{x:bounds.x+bounds.width*.5,y:bounds.y+bounds.height*.5});
 assert.equal(hit.node,'planned_step_1',JSON.stringify({hit,bounds}));
 const initialPosition=await moving.evaluate(el=>({left:parseFloat(el.style.left),top:parseFloat(el.style.top)}));
 await page.mouse.move(bounds.x+bounds.width*.5,bounds.y+bounds.height*.5);
 await page.mouse.down();
 await page.mouse.move(bounds.x+bounds.width*.5+35,bounds.y+bounds.height*.5+18,{steps:12});
 await page.waitForFunction(()=>document.querySelector('.flow-node.is-dragging')?.style.transform.includes('translate3d'));
 await page.mouse.up();
 const finalPosition=await moving.evaluate(el=>({left:parseFloat(el.style.left),top:parseFloat(el.style.top),dragging:el.classList.contains('is-dragging')}));
 assert(finalPosition.left>initialPosition.left && !finalPosition.dragging);
 assert.equal((await state()).planner_result.plan_sha256,originalSha);
 assert.equal(calls.filter(c=>c.action==='start').length,startsBeforeMotion);
 const recipeMaterial=await page.getByRole('button',{name:'Reusable recipes',exact:true}).evaluate(el=>getComputedStyle(el).backgroundImage);
 assert(recipeMaterial.includes('linear-gradient'));
 const rightMaterials=await page.locator('.top-actions>button, .top-actions .execute-button, .top-actions .authorize-button').evaluateAll(buttons=>buttons.map(el=>({name:el.textContent.trim(),gradient:getComputedStyle(el).backgroundImage,opacity:getComputedStyle(el).opacity,disabled:el.disabled})));
 assert(rightMaterials.length>=5,JSON.stringify(rightMaterials));
 assert(rightMaterials.every(b=>b.gradient.includes('linear-gradient')),JSON.stringify(rightMaterials));
 assert(rightMaterials.filter(b=>b.disabled).every(b=>b.opacity==='1'));

 cases.push('Cursor-anchored proportional wheel zoom, fractional node drag and recipe outline gradient preserve workflow semantics without execution');
 await page.getByRole('button',{name:'Planner agent',exact:true}).click();

 await page.getByRole('button',{name:'Reusable recipes',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Reusable recipes'});
 await dialog.getByRole('button',{name:/^Select columns and fill missing cells/}).click();
 assert.equal(await dialog.getByLabel(/^columns/).isVisible(),false);
 await dialog.getByText('More actions',{exact:true}).click();
 await dialog.getByRole('button',{name:'Discuss this template',exact:true}).click();
 await page.getByRole('textbox',{name:'Message Planner'}).waitFor();
 assert((await page.getByRole('textbox',{name:'Message Planner'}).inputValue()).includes('Select columns and fill missing cells'));
 cases.push('Recipe catalog routes into Planner; JSON bindings stay in a collapsed advanced inspector');
 await send('Make this current workflow reusable.');
 const candidate=page.getByRole('region',{name:'Reusable recipe candidate'});
 await candidate.getByRole('button',{name:'Register tested recipe',exact:true}).waitFor();
 chat=await state();
 assert.equal(chat.planner_result.plan_sha256,originalSha);
 assert.equal(chat.recipe_candidate.critic.conclusion,'supported');
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 await candidate.getByRole('button',{name:'Register tested recipe',exact:true}).click();
 await candidate.getByRole('button',{name:'Recipe registered',exact:true}).waitFor();
 const beforeReload=await readFile(resolve(root,'model-calls.jsonl'),'utf8');
 await page.reload();
 await page.locator('[data-operation-node="planned_step_2"]').waitFor();
 await page.getByRole('button',{name:'Recipe registered',exact:true}).waitFor();
 assert.equal(await readFile(resolve(root,'model-calls.jsonl'),'utf8'),beforeReload);
 assert(!beforeReload.includes('builder'));
 cases.push('Chat delegates recipe authoring to Planner and Critic, registers once and restores candidate/workflow without another model call');
 await authorize();
 assert((await page.locator('.workflow-review-panel .execute-button').evaluate(el=>getComputedStyle(el).backgroundImage)).includes('linear-gradient'));
 await page.locator('.workflow-review-panel .execute-button').click();
 await page.locator('.workflow-outcome-panel .outcome-step').first().waitFor();
 await page.locator('.results-workspace').getByRole('tab',{name:'Checks',exact:true}).click();
 await page.locator('.workflow-outcome-panel .critic-outcome').getByText('Recorded operations completed and their reported validation is available.',{exact:true}).waitFor();
 assert.equal((await readdir(resolve(root,'data/output'))).length,2);
 const cleaned=await readFile(resolve(root,originalTargets[1]),'utf8');
 assert(cleaned.startsWith('region,amount\n')&&cleaned.includes('Unknown,30'));
 cases.push('Backend executes and validates real CSV outputs, then Critic assesses them without frontend-managed validation');
 await page.getByRole('button',{name:'Planner agent',exact:true}).click();
 await send('Also group by region and sum amount.');
 await page.locator('[data-operation-node="planned_step_3"]').waitFor();
 chat=await state();
 const revisedTargets=chat.planner_result.plan.steps.map(s=>s.arguments.target_path);
 assert(revisedTargets.every(p=>!originalTargets.includes(p)));
 assert.equal(new Set(revisedTargets).size,3);
 assert.equal((await readdir(resolve(root,'data/output'))).length,2);
 assert.equal(await page.getByRole('region',{name:'Reusable recipe candidate'}).count(),0);
 await authorize();
 await page.locator('.workflow-review-panel .execute-button').click();
 await page.locator('.workflow-outcome-panel .outcome-step').first().waitFor();
 await page.getByLabel('Operation result',{exact:true}).selectOption('step_3');
 const csv=await readFile(resolve(root,revisedTargets[2]),'utf8');
 const rows=csv.trim().split('\n').slice(1).map(line=>{const [region,total]=line.split(',');return [region,Number(total)];});
 assert.deepEqual(Object.fromEntries(rows),{Unknown:30,north:35,south:40});
 assert.equal((await readdir(resolve(root,'data/output'))).length,5);
 assert.equal(await readFile(resolve(root,originalTargets[1]),'utf8'),cleaned);
 cases.push('A conversational addition expands beyond the recipe, refreshes occupied automatic targets and requires fresh authority without overwriting old outputs');
 await page.reload();
 await page.locator('[data-operation-node="planned_step_3"]').waitFor();
 assert.equal(calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='start').length,2);
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,live_service_calls:0,page_errors:errors},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls:calls.slice(-25)},null,2));throw error;}
finally{if(browser)await browser.close();child?.kill();await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
