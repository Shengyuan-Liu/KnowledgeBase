/* Complete visual checks after the first scripts' selector and navigation-wait errors. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('../../../frontend/node_modules/playwright');
const ROOT=__dirname,BASE='http://127.0.0.1:8787';
const read=n=>JSON.parse(fs.readFileSync(path.join(ROOT,n),'utf8'));
const calls=()=>fs.readFileSync(path.join(ROOT,'server-observations.jsonl'),'utf8').split('\n').filter(Boolean).map(JSON.parse).filter(x=>x.kind==='sdk_start').length;
const report={at:new Date().toISOString(),reason:'Attempt 1 expected the wrong ready attribute value. Attempt 2 page-36 screenshots caught Loading page after a stale ready flag. This read-only check waits for changed canvas pixels and then readiness; no product changes or answer reruns.',before:calls(),checks:[],console:[],network:[]};
(async()=>{const browser=await chromium.launch({headless:false});report.browser=await browser.version();try{
 for(const width of [1440,390]){
  const context=await browser.newContext({viewport:{width,height:1000},recordHar:{path:path.join(ROOT,`navigation-${width}.har`),content:'embed'}});const page=await context.newPage();await page.goto(BASE);
  page.on('pageerror',e=>report.console.push({width,message:e.message}));page.on('response',r=>{if(r.url().includes('/api/'))report.network.push({width,url:r.url(),method:r.request().method(),status:r.status()});});
  const canvas=()=>page.locator('canvas');
  async function rendered(num,old=null){await page.waitForFunction(({num,old})=>{const c=document.querySelector(`canvas[aria-label="Original PDF page ${num}"]`);return c&&c.dataset.rendered==='true'&&!c.hidden&&(!old||c.toDataURL()!==old);},{num,old});}
  async function snap(tag){await page.screenshot({path:path.join(ROOT,`visual-${width}-${tag}.png`)});const raw=await canvas().evaluate(c=>c.toDataURL());fs.writeFileSync(path.join(ROOT,`visual-${width}-${tag}-canvas.png`),Buffer.from(raw.split(',')[1],'base64'));}
  async function load(id){const row=read(id+'-planned.json');await page.evaluate(cid=>localStorage.setItem('knowledgebase.conversationId',cid),row.answer.conversation_id);await page.reload();await page.getByRole('article',{name:'Assistant answer'}).waitFor();return row;}
  async function open(source,num){await page.getByRole('button',{name:`View source ${source.source_id}: ${source.file_name}`,exact:true}).first().click();await page.locator(`[data-source-id="${source.source_id}"]`).getByRole('link',{name:`Open page ${num}`,exact:true}).click();await rendered(num);}
  let row=await load('lecture-overfitting');await open(row.answer.sources[0],35);await snap('lecture35');
  let old=await canvas().evaluate(c=>c.toDataURL());await page.getByRole('button',{name:'Next page',exact:true}).click();await rendered(36,old);await snap('lecture36');
  old=await canvas().evaluate(c=>c.toDataURL());await page.getByRole('button',{name:'Previous page',exact:true}).click();await rendered(35,old);await snap('lecture35-return');await page.getByRole('button',{name:'Close PDF',exact:true}).click();
  await page.locator('[data-source-id="1"]').getByRole('link',{name:'Open page 35',exact:true}).click();await rendered(35);await snap('lecture35-reopen');report.checks.push({width,id:'B2-B3',status:'passed',path:[35,36,35,'closed',35],pixels_changed:true});
  row=await load('retriever-training-hop');
  for(const [file,num] of [['rag-paper.pdf',5],['dpr-paper.pdf',3]]){const source=row.answer.sources.find(s=>s.file_name===file&&row.answer.answer.includes(`[${s.source_id}]`));await open(source,num);await snap(`${file}-page${num}`);await page.getByRole('button',{name:'Close PDF',exact:true}).click();if(width===390)await page.getByRole('button',{name:'Close evidence',exact:true}).click();report.checks.push({width,id:'B4',file,page:num,source_id:source.source_id,status:'passed',visual_review:'pending complete canvas inspection'});}
  await context.close();
 }
}finally{report.after=calls();report.no_extra_provider_calls=report.before===report.after;fs.writeFileSync(path.join(ROOT,'browser-navigation-result.json'),JSON.stringify(report,null,2)+'\n');await browser.close();}
console.log(`${report.checks.length} passed navigation checks; additional SDK calls ${report.after-report.before}.`);
})().catch(e=>{report.error=e.message;fs.writeFileSync(path.join(ROOT,'browser-navigation-result.json'),JSON.stringify(report,null,2)+'\n');console.error(e);process.exitCode=1;});
