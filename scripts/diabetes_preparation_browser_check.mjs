#!/usr/bin/env node
// Actual shared backend and temporary CSV files; deterministic model proposal only.
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,writeFile,readdir,rm,mkdir,copyFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve,dirname,extname,isAbsolute} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const repo=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-diabetes-preparation-'));
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
 await mkdir(resolve(root,'data/input/test'),{recursive:true});
 for(const file of ['diabetic_sample_5000.csv','IDS_mapping.csv'])await copyFile(resolve(repo,'data/input/test',file),resolve(root,'data/input/test',file));
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--diabetes-decoding-fixture'],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'true',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});
 let stderr='';child.stderr.on('data',data=>stderr+=data);
 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error(`API startup timeout: ${stderr}`)),20000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exited ${code}: ${stderr}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
 await page.goto(origin);
 await page.getByRole('textbox',{name:'Message Planner'}).fill('Prepare the real diabetes sample: inspect readiness, select declared fields, decode the supplied admission/discharge/source codebook, and aggregate by age and readmitted. Preserve all encounters and original codes. No database work.');
 await page.locator('.planner-composer button[type=submit]').click();
 await page.locator('[data-operation-node="planned_step_3"]').waitFor({timeout:20000});
 assert.equal(await page.locator('[data-operation-skill="decode_csv_codes"]').count(),1);
 await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
 await page.locator('.workflow-authorization-form textarea').fill('Exact copies of the supplied sample/codebook in a temporary test project only.');
 await page.locator('.workflow-authorization-form button[type=submit]').click();
 await page.locator('.authorization-duration').waitFor();
 assert.deepEqual(await readdir(resolve(root,'data/output')),[]);
 await page.locator('.workflow-review-panel .execute-button').click();
 await page.locator('.results-workspace .outcome-step').first().waitFor({timeout:30000});
 await page.getByLabel('Operation result',{exact:true}).selectOption('step_1');
 await page.getByRole('tab',{name:'Groups',exact:true}).click();
 await page.getByLabel('Explore group by',{exact:true}).selectOption('age');
 await page.getByLabel('Explore split by',{exact:true}).selectOption('gender');
 await page.getByRole('button',{name:'Run analysis',exact:true}).click();
 const cross=page.getByRole('region',{name:'Cross-tab table',exact:true});
 await cross.waitFor({timeout:30000});
 const source=await readFile(resolve(root,'data/input/test/diabetic_sample_5000.csv'),'utf8');
 // These source fields have no embedded CSV quoting; independent oracle reads every row.
 const lines=source.trim().split(/\r?\n/),headers=lines.shift().split(',');
 const ai=headers.indexOf('age'),gi=headers.indexOf('gender'),expected=new Map(),genders=new Set();
 for(const line of lines){const cells=line.split(',');genders.add(cells[gi]);const key=JSON.stringify([cells[ai],cells[gi]]);expected.set(key,(expected.get(key)??0)+1);}
 const horizontal=(await cross.locator('thead th').allTextContents()).slice(1,-1);
 assert.deepEqual(horizontal,[...genders].sort());
 for(const row of await cross.locator('tbody tr').all()){
  const cells=await row.locator('th,td').allTextContents();
  for(let j=0;j<horizontal.length;j++)assert.equal(Number(cells[j+1].replaceAll(',','')),expected.get(JSON.stringify([cells[0],horizontal[j]]))??0);
 }
 assert.equal(await cross.locator('tfoot td').last().innerText(),'5,000');
 await page.getByLabel('Cross-tab cell values',{exact:true}).selectOption('row');
 assert.ok((await cross.locator('tbody td').allTextContents()).some(v=>v.endsWith('%')));
 await page.screenshot({path:'/tmp/actioncharter-real-diabetes-age-gender.png'});
 cases.push('Age vertical / gender horizontal: every cell reconciles with all 5,000 source rows; row percentages available');
 await page.getByRole('button',{name:'Result chart',exact:true}).click();
 await page.getByLabel('Explore group chart measure',{exact:true}).selectOption('count');
 await page.getByLabel('Explore group chart type',{exact:true}).selectOption('3d-column');
 const three=page.getByRole('img',{name:'3D columns: age / gender',exact:true});
 const marks=three.locator('[data-chart-value]');assert.equal(await marks.count(),expected.size);
 let threeTotal=0;
 for(const mark of await marks.all()){
  const key=JSON.stringify([await mark.getAttribute('data-3d-row'),await mark.getAttribute('data-3d-column')]);
  const count=Number(await mark.getAttribute('data-chart-value'));assert.equal(count,expected.get(key));threeTotal+=count;
 }
 assert.equal(threeTotal,5000);
 await three.scrollIntoViewIfNeeded();
 await page.screenshot({path:'/tmp/actioncharter-real-diabetes-3d.png'});
 cases.push('3D age/gender columns preserve every source count and reconcile to 5,000');

 const files=await readdir(resolve(root,'data/output'));
 assert.deepEqual(files.sort(),['diabetes_trial_01_decoded.csv','diabetes_trial_01_groups.csv','diabetes_trial_01_selected.csv']);
 await page.getByRole('button',{name:'Flow graph',exact:true}).click();
 await page.locator('[data-operation-node="planned_step_3"]').click();
 const result=page.locator('.inspector .operation-result');
 await result.getByRole('heading',{name:'Validation passed',exact:true}).waitFor();
 const coverage=result.getByRole('region',{name:'Codebook mapping coverage',exact:true});
 assert.ok((await coverage.innerText()).includes('5000 mapped · 0 unmapped'),await coverage.innerText());
 assert.equal(await coverage.locator('dl>div').count(),3);
 assert.ok((await result.innerText()).includes('original codes retained'));
 await page.screenshot({path:'/tmp/actioncharter-real-diabetes-decoding.png'});
 await page.reload();
 await page.locator('[data-operation-node="planned_step_3"]').waitFor();
 await page.locator('[data-operation-node="planned_step_3"]').click();
 await page.locator('.inspector .operation-result').getByRole('heading',{name:'Validation passed',exact:true}).waitFor();
 assert.equal(calls.filter(c=>c.path==='/api/v1/workflow/runs'&&c.action==='start').length,1);
 cases.push('Real 5,000-row source and supplied sectioned codebook: explicit authorization, actual preparation/aggregation, visible coverage, history restoration without rerun');
 assert.deepEqual(errors,[]);
 cases.push('Authorization alone produces no execution, data output or live database request');
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,model_fixture_only:true,real_data:true,live_database_calls:0,page_errors:errors},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls},null,2));throw error;}
finally{if(browser)await browser.close();child?.kill();await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
