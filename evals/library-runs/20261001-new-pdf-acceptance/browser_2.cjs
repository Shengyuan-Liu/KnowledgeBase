/* Inspect actual persisted answers in a visible browser without generating answers. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('../../../frontend/node_modules/playwright');
const ROOT=__dirname, BASE='http://127.0.0.1:8787';
const read=name=>JSON.parse(fs.readFileSync(path.join(ROOT,name),'utf8'));
const calls=()=>fs.readFileSync(path.join(ROOT,'server-observations.jsonl'),'utf8').trim().split('\n').map(JSON.parse).filter(x=>x.kind==='sdk_start').length;
const report={at:new Date().toISOString(),headless:false,checks:[],console:[],network:[],provider_calls_before:calls(),history_selection:'The product has no conversation picker. The harness sets only the real persisted conversation ID in the existing localStorage key, then reloads the unmodified product. This verifies restore and switch-by-ID, not an end-user history picker.'};
const rows=Object.fromEntries(['lecture-overfitting','retriever-training-hop','income-period-basis'].map(id=>[id,read(id+'-planned.json')]));
function save(){fs.writeFileSync(path.join(ROOT,'browser-result-2.json'),JSON.stringify(report,null,2)+'\n');}
(async()=>{
  assert(!fs.existsSync(path.join(ROOT,'browser-result-2.json')));
  const browser=await chromium.launch({headless:false}); report.browser=await browser.version();
  try {
    for (const width of [1440,390]) {
      const context=await browser.newContext({viewport:{width,height:1000},recordHar:{path:path.join(ROOT,`browser2-${width}.har`),content:'embed'}});
      await context.tracing.start({screenshots:true,snapshots:true,sources:true});
      const page=await context.newPage();page.setDefaultTimeout(15000);
      page.on('console',m=>{if(['error','warning'].includes(m.type()))report.console.push({width,type:m.type(),text:m.text()});});
      page.on('pageerror',e=>report.console.push({width,type:'pageerror',text:e.message}));
      page.on('requestfailed',r=>report.network.push({width,url:r.url(),method:r.method(),failure:r.failure()}));
      page.on('response',r=>{if(r.url().includes('/api/'))report.network.push({width,url:r.url(),method:r.request().method(),status:r.status()});});
      await page.goto(BASE);
      async function check(id,fn){const start=Date.now();try{const detail=await fn();report.checks.push({id,width,status:'passed',seconds:(Date.now()-start)/1000,detail});}catch(e){report.checks.push({id,width,status:e.message.includes('B5 blocked:')?'blocked':'failed',seconds:(Date.now()-start)/1000,error:e.message});await page.screenshot({path:path.join(ROOT,`retry-${width}-${id}-failure.png`)});}save();}
      async function load(id){
        const row=rows[id];assert.equal(row.status,'completed');
        await page.evaluate(cid=>localStorage.setItem('knowledgebase.conversationId',cid),row.answer.conversation_id);
        const received=page.waitForResponse(r=>r.url().endsWith('/api/conversations/'+row.answer.conversation_id)&&r.status()===200);
        await page.reload();const history=await (await received).json();const latest=history.messages.at(-1);
        await page.getByRole('article',{name:'Assistant answer'}).waitFor();
        assert.equal(await page.locator('div[class*="answerText"]').innerText(),row.answer.answer);
        assert.equal(latest.content,row.answer.answer);assert.deepEqual(latest.retrieval,row.saved_message.retrieval);assert.deepEqual(latest.sources,row.saved_message.sources);
        return row;
      }
      async function cite(row,source){
        await page.getByRole('button',{name:`View source ${source.source_id}: ${source.file_name}`,exact:true}).first().click();
        const card=page.locator(`[data-source-id="${source.source_id}"]`);await card.waitFor({state:'visible'});
        assert.equal(await card.locator('strong').first().innerText(),source.file_name);
        assert.equal(await card.locator('blockquote').first().innerText(),source.text);
        return card;
      }
      async function pdf(card,num,file,tag){
        await card.getByRole('link',{name:`Open page ${num}`,exact:true}).click();
        await page.locator(`canvas[aria-label="Original PDF page ${num}"][data-rendered="true"]`).waitFor({state:'visible'});
        assert.match(await page.getByRole('dialog',{name:file,exact:true}).innerText(),new RegExp(`Page ${num} of `));
        await page.screenshot({path:path.join(ROOT,`retry-${width}-${tag}.png`)});
      }
      let lecture,lectureSource;
      await check('B1',async()=>{
        lecture=await load('lecture-overfitting');lectureSource=lecture.answer.sources.find(s=>s.file_name==='decision-trees.pdf'&&/\[\d+\]/.test(lecture.answer.answer)&&lecture.answer.answer.includes(`[${s.source_id}]`));assert(lectureSource);
        await cite(lecture,lectureSource);await page.screenshot({path:path.join(ROOT,`retry-${width}-lecture-evidence.png`)});
        await load('lecture-overfitting');await cite(lecture,lectureSource);
        return {source_id:lectureSource.source_id,file:lectureSource.file_name,excerpt_matches:true,refresh_matches:true};
      });
      await check('B2',async()=>{await pdf(page.locator(`[data-source-id="${lectureSource.source_id}"]`),35,'decision-trees.pdf','lecture-page35');assert(await page.getByText('Page 35 of 51',{exact:true}).isVisible());return {physical_page:35,pages:51,visual_review:'pending screenshot inspection'};});
      await check('B3',async()=>{
        await page.getByRole('button',{name:'Next page',exact:true}).click();await page.locator('canvas[aria-label="Original PDF page 36"][data-rendered="true"]').waitFor({state:'visible'});await page.screenshot({path:path.join(ROOT,`retry-${width}-lecture-page36.png`)});
        await page.getByRole('button',{name:'Previous page',exact:true}).click();await page.locator('canvas[aria-label="Original PDF page 35"][data-rendered="true"]').waitFor({state:'visible'});
        await page.getByRole('button',{name:'Close PDF',exact:true}).click();await pdf(page.locator(`[data-source-id="${lectureSource.source_id}"]`),35,'decision-trees.pdf','lecture-reopened35');await page.getByRole('button',{name:'Close PDF',exact:true}).click();return {path:[35,36,35,'closed',35]};
      });
      await check('B4',async()=>{
        const row=await load('retriever-training-hop');const cited=row.answer.sources.filter(s=>row.answer.answer.includes(`[${s.source_id}]`));const details=[];
        for(const file of ['rag-paper.pdf','dpr-paper.pdf']){
          const source=cited.find(s=>s.file_name===file);assert(source,`No cited ${file}`);const card=await cite(row,source);const pages=[...new Set(source.pdf.regions.map(r=>r.page_index+1))];const num=pages.includes(3)?3:pages[0];await pdf(card,num,file,`hop-${file}-page${num}`);await page.getByRole('button',{name:'Close PDF',exact:true}).click();
          details.push({file,source_id:source.source_id,pages});if(width===390)await page.getByRole('button',{name:'Close evidence',exact:true}).click();
        }return details;
      });
      await check('B5',async()=>{
        const row=await load('income-period-basis');const sources=row.answer.sources.filter(s=>row.answer.answer.includes(`[${s.source_id}]`));assert(sources.length>0,'B5 blocked: financial answer has no cited sources after incorrect refusal');const details=[];
        for(const source of sources){
          const card=await cite(row,source);const pages=[...new Set([...source.pdf.regions,...source.pdf.supplements.flatMap(s=>s.regions)].map(r=>r.page_index+1))];
          for(const num of pages){await pdf(card,num,source.file_name,`income-source${source.source_id}-page${num}`);if(num===8){await page.getByRole('button',{name:'Previous page',exact:true}).click();await page.locator('canvas[aria-label="Original PDF page 7"][data-rendered="true"]').waitFor({state:'visible'});await page.screenshot({path:path.join(ROOT,`retry-${width}-income-source${source.source_id}-header7.png`)});}await page.getByRole('button',{name:'Close PDF',exact:true}).click();}
          details.push({source_id:source.source_id,pages});if(width===390)await page.getByRole('button',{name:'Close evidence',exact:true}).click();
        }return details;
      });
      await check('B6',async()=>{
        const details=[];
        for(const id of ['lecture-overfitting','retriever-training-hop','lecture-overfitting','retriever-training-hop']){
          const row=await load(id);await page.reload();await page.getByRole('article',{name:'Assistant answer'}).waitFor();assert.equal(await page.locator('div[class*="answerText"]').innerText(),row.answer.answer);
          const source=row.answer.sources.find(s=>row.answer.answer.includes(`[${s.source_id}]`));if(source)await cite(row,source);
          const plan=page.getByText('Search plan',{exact:true});await plan.click();await page.screenshot({path:path.join(ROOT,`retry-${width}-${id}-history.png`)});
          details.push({case:id,conversation_id:row.answer.conversation_id,answer_sources_trace_equal:true});
        }return {restorations:details,selection_method:report.history_selection};
      });
      await context.tracing.stop({path:path.join(ROOT,`browser2-${width}-trace.zip`)});await context.close();
    }
  } finally {report.provider_calls_after=calls();report.no_extra_provider_calls=report.provider_calls_after===report.provider_calls_before;save();await browser.close();}
  console.log(`${report.checks.filter(c=>c.status==='passed').length} passed; ${report.checks.filter(c=>c.status==='failed').length} failed browser checks; additional SDK calls ${report.provider_calls_after-report.provider_calls_before}.`);
  if(report.checks.some(c=>c.status==='failed'))process.exitCode=1;
})().catch(e=>{report.fatal=e.message;save();console.error(e);process.exitCode=1;});
