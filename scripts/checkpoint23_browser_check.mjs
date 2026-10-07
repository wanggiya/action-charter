#!/usr/bin/env node
// Production-browser regression with intercepted API fixtures. No real backend calls.
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile, rename } from 'node:fs/promises';
import { resolve, dirname, extname, isAbsolute } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = resolve(process.env.ACTIONCHARTER_BROWSER_RESULTS ?? '/tmp/actioncharter-ui-review/results');
const provider = process.env.ACTIONCHARTER_PLAYWRIGHT_MODULE ?? 'playwright';
const { chromium } = await import(isAbsolute(provider) ? pathToFileURL(provider).href : provider);
const ids = ['inspect_vector','inspect_raster','convert_vector','convert_raster','load_vector_to_postgis','validate_postgis_layer','generate_report','export_snakemake_workflow','verify_snakemake_export'];
const catalog = { schema_version:'1.0', skills:ids.map(id=>({id,kind:'inspection',access:['convert_vector','convert_raster','load_vector_to_postgis','generate_report','export_snakemake_workflow'].includes(id)?'artifact_write':'read_only',approval_required:['convert_vector','convert_raster','load_vector_to_postgis','generate_report','export_snakemake_workflow'].includes(id),validation_required:['convert_vector','convert_raster','load_vector_to_postgis','export_snakemake_workflow'].includes(id)})),skill_count:ids.length,catalog_validated:true,execution_performed:false };
const digest = 'e'.repeat(64);
let current = {schema_version:'1.0',status:'planned_not_saved',agent_id:'planner',model:'UI fixture · no real operations',original_request:'Inspect sample_points.geojson and propose a local conversion.',allowed_skill_ids:ids,context_references:[],warnings:[],plan_sha256:digest,plan_saved:false,approval_performed:false,execution_performed:false,plan:{schema_version:'1.0',status:'planned',summary:'UI regression fixture',steps:[{step_id:'step_1',skill:'inspect_vector',purpose:'Inspect the fixture metadata',arguments:{path:'data/input/sample_points.geojson'},requires_approval:false,validation_required:false,expected_artifacts:[]},{step_id:'step_2',skill:'convert_vector',purpose:'Propose conversion of the exact fixture',arguments:{path:'data/input/sample_points.geojson',target_path:'data/output/browser-fixture.gpkg'},requires_approval:true,validation_required:true,expected_artifacts:[]}],assumptions:[],risks:[],execution_performed:false,validation_performed:false}};
let completed = null;
const calls = [], cases = [], errors = [];
const dist = resolve(root,'interface/dist');
const server = createServer(async (req,res)=>{
  try {
    const pathname = decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    let path = resolve(dist,'.'+pathname);
    if (!path.startsWith(dist+'/')) path = resolve(dist,'index.html');
    if (!pathname.startsWith('/assets/')) path = resolve(dist,'index.html');
    const data = await readFile(path);
    res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'})[extname(path)]??'application/octet-stream');
    res.end(data);
  } catch { res.writeHead(404); res.end(); }
});
await new Promise(done=>server.listen(0,'127.0.0.1',done));
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
try {
  await mkdir(output,{recursive:true});
  browser = await chromium.launch({headless:true,args:['--no-sandbox']});
  const page = await browser.newPage({viewport:{width:1600,height:1000}});
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{
    const request = route.request(), url = new URL(request.url());
    if (url.origin !== origin) return route.abort();
    if (!url.pathname.startsWith('/api/')) return route.continue();
    const body = request.postDataJSON() ?? {};
    calls.push({path:url.pathname,action:body.action});
    let payload, status=200;
    if(url.pathname==='/api/v1/planner-skills') payload=catalog;
    else if(url.pathname==='/api/v1/planner/conversation') payload=body.action==='list'?{conversations:[],approval_performed:false,execution_performed:false}:{conversation_id:body.conversation_id,revision:0,messages:[],planner_result:current,proposal_changed:false,selected_skill_ids:[],supported_skill_ids:ids,approval_performed:false,execution_performed:false};
    else if(url.pathname==='/api/v1/plans/save-generated') {current={...current,...body.planner_result,plan_sha256:body.confirmed_plan_sha256};payload={schema_version:'1.0',status:'stored',plan_filename:`planner-plan.${current.plan_sha256}.json`,plan_sha256:current.plan_sha256,plan_saved:true,plan_modified:false,approval_performed:false,execution_performed:false};}
    else if(url.pathname==='/api/v1/plans/validate-edit') {current={...current,...body.planner_result,plan_sha256:'b'.repeat(64)};payload=current;}
    else if(url.pathname==='/api/v1/plans') payload={schema_version:'1.0',status:'inspected',plans:[],plan_count:0,files_modified:false,execution_performed:false};
    else if(url.pathname==='/api/v1/workflow/prepare') payload={schema_version:'1.0',plan_filename:`planner-plan.${current.plan_sha256}.json`,plan_sha256:current.plan_sha256,recipe_filename:`fixture.${digest}.json`,recipe_sha256:digest,review_sha256:'a'.repeat(64),steps:current.plan.steps,approval_required_step_ids:current.plan.steps.filter(s=>s.requires_approval).map(s=>s.step_id),write_step_ids:current.plan.steps.filter(s=>s.requires_approval).map(s=>s.step_id),execution_available:true,execution_performed:false};
    else if(url.pathname==='/api/v1/workflow/authorize') payload={schema_version:'1.0',review_sha256:'a'.repeat(64),plan_approval_filename:'approval-20261007t000000z-1234abcd.json',recipe_approval_filename:null,approval_recorded:true,execution_performed:false};
    else if(url.pathname==='/api/v1/workflow/execute') {completed={schema_version:'1.0',workflow_kind:'snakemake_export',run_id:'d'.repeat(32),plan_filename:`planner-plan.${current.plan_sha256}.json`,plan_sha256:current.plan_sha256,started_at:'2026-10-07T00:00:00Z',finished_at:'2026-10-07T00:00:01Z',status:'completed',approval_recorded:true,execution_performed:true,step_results:current.plan.steps.map(s=>({step_id:s.step_id,skill_id:s.skill,status:'reused_completed',validation_performed:true,outcome:{source_attempt:'c'.repeat(64),reused:true,source_attempt_content:'Recorded source fixture content'},validation_outcome:{passed:true}}))};payload=completed;}
    else if(url.pathname==='/api/v1/inspection-runs') payload={records:completed?[completed]:[],execution_performed:false};
    else if(url.pathname==='/api/v1/executions') payload={schema_version:'1.0',attempts:[],attempt_count:0,inventory_truncated:false,execution_performed:false};
    else {status=404;payload={error:'Not provided by isolated browser fixture'};}
    return route.fulfill({status,contentType:'application/json',body:JSON.stringify(payload)});
  });
  await page.goto(origin);
  await page.getByRole('button',{name:'Open conversation plan',exact:true}).click();
  await page.locator('[data-operation-node="planned_step_1"]').waitFor();
  await page.getByRole('button',{name:'Add',exact:true}).click();
  const picker=page.getByRole('dialog',{name:'Add operation'});
  const choices=await picker.locator('.operation-picker-results button').allTextContents();
  assert.deepEqual(choices.slice(0,2),['Export to Snakemake','Verify Snakemake package']);
  const headerBefore=await picker.locator('.operation-picker-header').boundingBox();
  const exportBefore=await picker.getByRole('button',{name:'Export to Snakemake',exact:true}).boundingBox();
  await picker.locator('.operation-picker-results').evaluate(el=>el.scrollTop=el.scrollHeight);
  const headerAfter=await picker.locator('.operation-picker-header').boundingBox();
  const exportAfter=await picker.getByRole('button',{name:'Export to Snakemake',exact:true}).boundingBox();
  assert.equal(headerBefore.y,headerAfter.y);
  assert(exportAfter.y<exportBefore.y,'Featured operations must scroll with results');
  await picker.getByRole('textbox',{name:'Search operations'}).fill('snake make');
  assert.equal(await picker.locator('.operation-picker-results button').count(),2);
  await picker.getByRole('button',{name:'Close add operation panel'}).click();
  cases.push('Add: Snakemake first, results scroll, header pinned, searchable and closable');
  const node=page.locator('[data-operation-node="planned_step_2"]');
  const before=await node.boundingBox();
  const viewport=await page.locator('.canvas-window').evaluate(el=>({left:el.scrollLeft,top:el.scrollTop}));
  await page.mouse.move(before.x+before.width/2,before.y+before.height/2);
  await page.mouse.down();
  await page.mouse.move(before.x+before.width/2+50,before.y+before.height/2+35,{steps:30});
  await page.waitForTimeout(100);
  const during=await node.boundingBox();
  assert(Math.abs(during.x-before.x-50)<2 && Math.abs(during.y-before.y-35)<2, JSON.stringify({before,during,style:await node.evaluate(el=>({transform:el.style.transform,computed:getComputedStyle(el).transform,classes:el.className})),hit:await page.evaluate(({x,y})=>document.elementFromPoint(x,y)?.outerHTML.slice(0,300),{x:before.x+before.width/2,y:before.y+before.height/2})}));
  await page.mouse.up();
  await page.waitForTimeout(150);
  const after=await node.boundingBox();
  assert(Math.abs(after.x-during.x)<2 && Math.abs(after.y-during.y)<2);
  assert.deepEqual(await page.locator('.canvas-window').evaluate(el=>({left:el.scrollLeft,top:el.scrollTop})),viewport);
  cases.push('Drag: preview follows pointer, release preserves position and viewport');
  await page.getByRole('button',{name:'Add',exact:true}).click();
  await page.getByRole('button',{name:'Export to Snakemake',exact:true}).click();
  await page.locator('[data-operation-node="planned_step_4"]').waitFor();
  const draft=page.locator('[data-operation-node="planned_step_4"]');
  const draftBefore=await draft.boundingBox();
  await page.mouse.move(draftBefore.x+draftBefore.width/2,draftBefore.y+draftBefore.height/2);
  await page.mouse.down();
  await page.mouse.move(draftBefore.x+draftBefore.width/2+30,draftBefore.y+draftBefore.height/2+20,{steps:20});
  await page.mouse.up();
  await page.waitForTimeout(100);
  const draftAfter=await draft.boundingBox();
  assert(Math.abs(draftAfter.x-draftBefore.x-30)<2 && Math.abs(draftAfter.y-draftBefore.y-20)<2,'Edited graph must not auto-fit during drag or release');
  await page.getByRole('button',{name:'Validate and save edits',exact:true}).click();
  await page.getByRole('button',{name:'Validate and save edits',exact:true}).waitFor({state:'hidden'});
  cases.push('Draft graph: Add export adds verification, stable drag, validate/save preserves workflow');
  await page.getByRole('button',{name:'Switch to vertical layout',exact:true}).click();
  await page.waitForTimeout(80);
  const vertical=await draft.boundingBox();
  await page.mouse.move(vertical.x+vertical.width/2,vertical.y+10);
  await page.mouse.down();
  await page.mouse.move(vertical.x+vertical.width/2+20,vertical.y+10+20,{steps:20});
  await page.mouse.up();
  await page.waitForTimeout(80);
  const verticalAfter=await draft.boundingBox();
  assert(Math.abs(verticalAfter.x-vertical.x-20)<2 && Math.abs(verticalAfter.y-vertical.y-20)<2,JSON.stringify({vertical,verticalAfter,hit:await page.evaluate(({x,y})=>document.elementFromPoint(x,y)?.outerHTML.slice(0,350),{x:vertical.x+vertical.width/2,y:vertical.y+10}),style:await draft.evaluate(el=>({left:el.style.left,top:el.style.top,transform:el.style.transform}))}));
  await page.mouse.move(verticalAfter.x+verticalAfter.width/2,verticalAfter.y+10);
  await page.mouse.down();
  await page.mouse.move(verticalAfter.x+verticalAfter.width/2-20,verticalAfter.y+10-20,{steps:10});
  await page.keyboard.press('Escape');
  await page.mouse.up();
  const cancelled=await draft.boundingBox();
  assert(Math.abs(cancelled.x-verticalAfter.x)<2 && Math.abs(cancelled.y-verticalAfter.y)<2,'Escape must cancel the drag without committing layout');
  await page.getByRole('button',{name:'Switch to horizontal layout',exact:true}).click();
  cases.push('Vertical drag and Escape cancellation preserve the expected positions');

  await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
  await page.locator('.workflow-review-panel').waitFor();
  const leftWrong = await page.locator('.workflow-review-panel h2,.workflow-review-panel p,.workflow-review-panel label,.workflow-review-panel input,.workflow-review-panel textarea,.workflow-review-panel dt,.review-step-link>small,.review-step-dependencies').evaluateAll(els=>els.filter(el=>getComputedStyle(el).textAlign!=='left').map(el=>({tag:el.tagName,text:el.textContent.slice(0,60),align:getComputedStyle(el).textAlign})));
  const rightWrong = await page.locator('.workflow-review-panel dd,.review-step-link>strong,.review-step-gates').evaluateAll(els=>els.filter(el=>getComputedStyle(el).textAlign!=='right').map(el=>({tag:el.tagName,text:el.textContent.slice(0,60),align:getComputedStyle(el).textAlign})));
  assert.deepEqual(leftWrong,[],'Narrative, step labels and parameter labels must align left');
  assert.deepEqual(rightWrong,[],'Operation names, values and gates must align right');
  const rows = await page.locator('.workflow-review-panel ol>li').evaluateAll(cards=>cards.map(card=>{
    const edge=card.getBoundingClientRect().right-parseFloat(getComputedStyle(card).paddingRight)-parseFloat(getComputedStyle(card).borderRightWidth);
    return [...card.querySelectorAll('.review-step-link>strong,dd,.review-step-gates')].map(el=>({text:el.textContent.slice(0,30),delta:Math.abs(el.getBoundingClientRect().right-edge),tag:el.tagName,rect:el.getBoundingClientRect().toJSON(),parentRect:el.parentElement.getBoundingClientRect().toJSON(),parentDisplay:getComputedStyle(el.parentElement).display,columns:getComputedStyle(el.parentElement).gridTemplateColumns,dlDisplay:getComputedStyle(el.closest('dl')??el.parentElement).display}));
  }).flat());
  assert(rows.every(row=>row.delta<1.5),JSON.stringify(rows));
  assert.equal(await page.locator('.workflow-review-panel dd').first().evaluate(el=>getComputedStyle(el).textTransform),'none');
  await page.locator('.workflow-authorization-form textarea').fill('Authorize only this isolated browser fixture.');
  await page.locator('.workflow-authorization-form button[type=submit]').click();
  await page.locator('.authorization-duration').waitFor();
  assert(await page.locator('.authorization-duration').evaluate(el=>getComputedStyle(el).fontWeight)>=700);
  await page.screenshot({path:resolve(output,'authorization.png')});
  const actions=await page.locator('.workflow-decision-actions>button').evaluateAll(els=>els.map(el=>({top:el.getBoundingClientRect().top,type:el.getAttribute('type')})));
  assert.equal(actions.length,2); assert(Math.abs(actions[0].top-actions[1].top)<1);
  assert(await page.locator('.workflow-decision-actions').evaluate(el=>{const row=el.getBoundingClientRect(),panel=el.closest('.workspace-right-panel').getBoundingClientRect();return row.top>=panel.top && row.bottom<=panel.bottom;}),'Authorization must not scroll away from the action row'); assert.deepEqual(actions.map(a=>a.type),['submit','button']);
  cases.push('Authorization: mixed paired alignment reaches card edges; duration emphasized; actions on one row');
  for (const text of ['black','white']) {
    await page.getByRole('button',{name:'Settings',exact:true}).click();
    await page.getByLabel('Interface style').selectOption('filled');
    await page.getByLabel('Solid-fill text color').selectOption(text);
    await page.getByRole('button',{name:'Close settings'}).click();
    assert.equal(await page.locator('.workflow-review-panel p').first().evaluate(el=>getComputedStyle(el).textAlign),'left');
    assert(await page.locator('.workflow-review-panel dd').evaluateAll(els=>els.every(el=>getComputedStyle(el).textAlign==='right' && getComputedStyle(el).maxWidth==='none')));
  }
  await page.getByRole('button',{name:'Settings',exact:true}).click();
  await page.getByLabel('Interface style').selectOption('outline');
  await page.getByRole('button',{name:'Close settings'}).click();
  cases.push('Outline and both solid text materials preserve mixed review alignment');
  await page.locator('.workflow-review-panel .execute-button').click();
  await page.locator('.workflow-outcome-panel article').first().waitFor();
  const right=await page.locator('.workflow-outcome-panel dd').evaluateAll(els=>els.every(el=>getComputedStyle(el).textAlign==='right'));
  assert(right);
  await page.screenshot({path:resolve(output,'outcome.png')});
  cases.push('Outcome: source attempt and reused information values align right');
  await page.getByRole('button',{name:'Close outcome'}).click();
  await page.setViewportSize({width:900,height:800});
  await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
  assert(await page.locator('.workflow-review-panel').isVisible());
  await page.screenshot({path:resolve(output,'narrow-review.png')});
  cases.push('Narrow viewport: review remains accessible');
  await page.reload();
  await page.getByRole('button',{name:'Open conversation plan',exact:true}).click();
  await page.locator('[data-operation-node="planned_step_4"]').waitFor();
  await page.getByRole('button',{name:'Execution History',exact:true}).click();
  await page.getByRole('button',{name:'View outcome',exact:true}).click();
  await page.locator('.workflow-outcome-panel article').first().waitFor();
  assert.equal(calls.filter(call=>call.path==='/api/v1/workflow/execute').length,1,'Recovery must not rerun operations');
  cases.push('Refresh: conversation-plan recovery and history outcome reopen without execution');
  assert.equal(calls.filter(call=>call.path==='/api/v1/workflow/authorize').length,1,'Execute must not resubmit authorization');
  assert.deepEqual(errors,[]);
  await writeFile(resolve(output,'RESULTS.json'),JSON.stringify({status:'PASS',cases,api_fixture_only:true,live_gis_calls:0,page_errors:errors,api_calls:calls},null,2));
  try { await rename(resolve(output,'FAILURE.json'),resolve(output,'PREVIOUS_FAILURE.json')); } catch { /* No prior failure. */ }
  console.log(JSON.stringify({status:'PASS',cases,output,live_gis_calls:0}));
} catch(error) {
  await mkdir(output,{recursive:true});
  await writeFile(resolve(output,'FAILURE.json'),JSON.stringify({error:String(error),cases,page_errors:errors},null,2));
  throw error;
} finally {
  await browser?.close();
  await new Promise(done=>server.close(done));
}
