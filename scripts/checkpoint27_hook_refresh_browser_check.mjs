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
const root=await mkdtemp(resolve(tmpdir(),'actioncharter-hook-refresh-'));
const provider=process.env.ACTIONCHARTER_PLAYWRIGHT_MODULE??resolve(repo,'interface/node_modules/playwright/index.mjs');
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(repo,'interface/.playwright-browsers');
const browserLibArchitecture=process.arch==='arm64'?'aarch64-linux-gnu':'x86_64-linux-gnu';
process.env.LD_LIBRARY_PATH=[resolve(repo,'interface/.browser-system-libs/runtime/usr/lib',browserLibArchitecture),process.env.LD_LIBRARY_PATH].filter(Boolean).join(':');
const {chromium}=await import(isAbsolute(provider)?pathToFileURL(provider).href:provider);
let apiPort,child,browser,vite; let nextHook=false; const calls=[],errors=[],cases=[];
const frontend=createServer(async(req,res)=>{
 try {
  if(req.url.startsWith('/api/')) {
   const chunks=[];for await(const chunk of req)chunks.push(chunk);
   calls.push({method:req.method,path:req.url,action:req.method==='POST'?JSON.parse(Buffer.concat(chunks).toString()).action:undefined});
   const response=await fetch(`http://127.0.0.1:${apiPort}${req.url}`,{method:req.method,headers:{'Content-Type':'application/json'},...(req.method==='POST'?{body:Buffer.concat(chunks)}:{})});
   res.writeHead(response.status,{'Content-Type':'application/json'});res.end(await response.text());return;
  }
  if(vite){vite.middlewares(req,res);return;}
  const pathname=new URL(req.url,'http://localhost').pathname;
  const file=pathname.startsWith('/assets/')?resolve(repo,'interface/dist','.'+pathname):resolve(repo,'interface/dist/index.html');
  const content=await readFile(file);res.setHeader('Content-Type',({'.js':'text/javascript','.css':'text/css','.html':'text/html'})[extname(file)]??'application/octet-stream');res.end(content);
 }catch(error){res.writeHead(500);res.end(String(error));}
});
await new Promise(done=>frontend.listen(0,'127.0.0.1',done));
const origin=`http://127.0.0.1:${frontend.address().port}`;
try{
 child=spawn(resolve(repo,'.venv/bin/python'),[resolve(repo,'scripts/checkpoint24_fixture_api.py'),'--root',root,'--calculation-fixture','--critic-graph-fixture'],{cwd:repo,env:{PATH:process.env.PATH,PYTHONPATH:resolve(repo,'src'),ENABLE_WRITE_TOOLS:'true',ALLOW_OVERWRITE:'false',MODEL_NAME:'fixture',MODEL_BASE_URL:'http://127.0.0.1:1/v1',POSTGRES_HOST:'127.0.0.1',POSTGRES_PORT:'1',POSTGRES_PASSWORD_FILE:resolve(root,'missing-secret'),GEOSERVER_BASE_URL:'http://127.0.0.1:1',GEOSERVER_PASSWORD_FILE:resolve(root,'missing-geoserver-secret'),INTERFACE_FRONTEND_ORIGIN:origin}});
 let stderr='';child.stderr.on('data',data=>stderr+=data);
 apiPort=await new Promise((done,reject)=>{let output='';const timer=setTimeout(()=>reject(new Error(`API startup timeout: ${stderr}`)),20000);child.stdout.on('data',data=>{output+=data;if(output.includes('\n')){clearTimeout(timer);done(JSON.parse(output.split('\n')[0]).port);}});child.on('exit',code=>{clearTimeout(timer);reject(new Error(`API exited ${code}: ${stderr}`));});});
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const hookPath=resolve(repo,'interface/src/lib/use-plan-run.ts');
 const source=await readFile(hookPath,'utf8');
 const start=source.indexOf('  useEffect(()=>{',source.indexOf('  const run='));
 const end=source.indexOf('  return {run,',start);
 assert(start>0&&end>start,'Must locate the added polling hook');
 const oldSource=source.slice(0,start)+source.slice(end);
 const {createServer:createVite}=await import(pathToFileURL(resolve(repo,'interface/node_modules/vite/dist/node/index.js')).href);
 vite=await createVite({configFile:resolve(repo,'interface/vite.config.ts'),root:resolve(repo,'interface'),
   cacheDir:resolve(root,'vite-cache'),server:{middlewareMode:true,hmr:{server:frontend}},
   plugins:[{name:'fixture-hook-upgrade',enforce:'pre',load(id){if(id.split('?')[0]===hookPath)return nextHook?source:oldSource;}}]});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});
 page.on('pageerror',error=>errors.push(error.message));
 page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
 await page.goto(origin);
 await page.getByRole('textbox',{name:'Message Planner'}).fill('Inspect sample_orders.csv. Calculate doubled as amount multiplied by 2. Save to a fresh CSV. Do not execute yet.');
 await page.locator('.planner-composer button[type=submit]').click();
 await page.locator('[data-operation-node="planned_step_2"]').waitFor({timeout:30000});
 const chat=await page.evaluate(()=>localStorage.getItem('actioncharter:planner-conversation:v1'));
 await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
 await page.locator('.workflow-authorization-form textarea').waitFor();
 cases.push('Development render opens exact authorization without executing');
 // Simulate an imported hook gaining an effect, without editing the workspace.
 nextHook=true;
 const navigated=page.waitForEvent('load',{timeout:15000});
 vite.watcher.emit('change',hookPath);
 await navigated;
 await page.locator('[data-operation-node="planned_step_2"]').waitFor({timeout:30000});
 assert.equal(await page.evaluate(()=>localStorage.getItem('actioncharter:planner-conversation:v1')),chat);
 await page.getByRole('button',{name:'Authorize',exact:true}).first().click();
 await page.locator('.workflow-authorization-form textarea').fill('Temporary fixture only; no execution requested.');
 await page.locator('.workflow-authorization-form button[type=submit]').click();
 await page.locator('.authorization-duration').waitFor({timeout:15000});
 assert.equal(calls.filter(call=>call.path==='/api/v1/workflow/runs'&&call.action==='start').length,0);
 assert.equal((await readdir(resolve(root,'data/output'))).length,0);
 assert.deepEqual(errors,[]);
 cases.push('Hook upgrade reloads safely, restores the saved chat/workflow and permits exact authorization with no hook warning or execution');
 console.log(JSON.stringify({status:'PASS',cases,actual_backend:true,development_vite:true,model_fixture_only:true,page_errors:errors},null,2));
}catch(error){console.error(error);console.error(JSON.stringify({cases,errors,calls},null,2));throw error;}
finally{if(browser)await browser.close();await vite?.close();child?.kill();await new Promise(done=>frontend.close(done));await rm(root,{recursive:true,force:true});}
