import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import http from 'node:http';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {extract} from './capture.mjs';
import {extractFaq,renderNode} from './capture-faq.mjs';
import {unionCoverage,locateSources,retrievalMetrics,percentile,summarize,readSSE} from './metrics.mjs';
import {ask} from './run.mjs';
import {grade} from './grade.mjs';
import {validate} from './validate.mjs';

test('extracts all hidden tabs, preserves code line breaks and removes navigation',()=>{
  const {body}=extract('<nav>outside</nav><main><h1>Example</h1><div role="tablist">tabs</div><div role="tabpanel"><pre class="language-js"><code><span class="token-line">one()<br></span><span class="token-line">two()<br></span></code></pre></div><div role="tabpanel" hidden><pre><code>hidden example</code></pre></div><button>Copy</button></main>','https://example.org/');
  assert(body.includes('one()\ntwo()'));assert(body.includes('hidden example'));assert(!body.includes('outside'));assert(!body.includes('Copy'));assert(!body.includes('tabs'));
});
test('expands merged cells and preserves row boundaries inside bold table wrappers',()=>{
  const {body}=extract('<main><h1>Prices</h1><strong><table><tr><td>Kind</td><td colspan="2">Models</td></tr><tr><td rowspan="2">Input</td><td>A<br>B</td><td>1</td></tr><tr><td>C</td><td>2</td></tr></table></strong></main>','https://example.org/');
  assert(body.includes('| Kind | Models | Models |\n| --- | --- | --- |'));
  assert(body.includes('| Input | A  <br>B | 1 |'));assert(body.includes('| Input | C | 2 |'));assert(!body.includes('**|'));
});
test('parses the FAQ data literal without executing source code',()=>{
  const data={zh:{categories:[]},en:{categories:[{id:'4',questions:[{id:'one'}]}]}};
  const script=`throw new Error('must not run'); const data=JSON.parse(${JSON.stringify(JSON.stringify(data))});`;
  assert.deepEqual(extractFaq(script),[{id:'one'}]);
  assert.equal(renderNode({type:'link',url:'https://example.org',children:[{type:'text',value:'source'}]}),'[source](https://example.org)');
});
test('overlap never double counts and full coverage can combine chunks',()=>{
  assert.equal(unionCoverage(10,20,[[8,15],[13,18]]),.8);
  assert.equal(unionCoverage(10,20,[[8,15],[15,25]]),1);
  assert.equal(unionCoverage(10,20,[]),0);
});
test('Unicode offsets use code points and ambiguous repeats are not guessed',()=>{
  const docs=new Map([['x.txt',{file:'x',text:'A😀BC repeat repeat'}]]);
  const located=locateSources([{file_name:'x.txt',text:'BC'},{file_name:'x.txt',text:'repeat'}],docs);
  assert.equal(located[0].start_offset,2);assert.equal(located[0].end_offset,4);
  assert.equal(located[1].offset_status,'ambiguous');assert.equal(located[1].file,'x');
  const row={answerable:true,evidence:[{file:'x',start_offset:2,end_offset:4}]};
  assert.equal(retrievalMetrics(row,located).annotated_char_recall,null);
  assert.equal(retrievalMetrics(row,[located[0]]).annotated_char_recall,1);
  assert.equal(retrievalMetrics({...row,answerable:false},located),null);
});
test('failure denominators and unmeasured quality stay explicit',()=>{
  const report=summarize([{status:'ok',latency_seconds:2,retrieval:null},{status:'error',latency_seconds:10}],4);
  assert.equal(report.completion_rate,.5);assert.equal(report.successful_requests_per_second,.25);
  assert.equal(report.timing_seconds.end_to_end.p95,2);assert.equal(report.answer_accuracy,null);
  assert.equal(percentile([], .95),null);assert.equal(percentile([3,1,2],.5),2);
});
test('fragmented SSE and split UTF-8 decode to complete events',async()=>{
  const bytes=new TextEncoder().encode('event: answer_delta\r\ndata: {"delta":"😀"}\r\n\r\n');
  const body=new ReadableStream({start(controller){for(const byte of bytes)controller.enqueue(new Uint8Array([byte]));controller.close();}});
  const events=[];await readSSE(new Response(body),(e,d)=>events.push([e,d]));
  assert.deepEqual(events,[['answer_delta',{delta:'😀'}]]);
});
test('truncated SSE frame fails instead of becoming a successful answer',async()=>{
  await assert.rejects(()=>readSSE(new Response('event: complete\ndata: {}'),()=>{}),/Incomplete_SSE_frame/);
});
test('HTTP adapter records completion and rejects EOF without complete',async()=>{
  let mode='complete';
  const server=http.createServer(async(req,res)=>{
    let body='';for await(const chunk of req)body+=chunk;const {request_id}=JSON.parse(body);
    res.writeHead(200,{'Content-Type':'text/event-stream'});
    const send=(event,data)=>res.write(`event: ${event}\ndata: ${JSON.stringify({request_id,...data})}\n\n`);
    send('start',{});send('sources',{sources:[]});send('answer_delta',{delta:'Answer'});
    if(mode==='complete')send('complete',{answer:'Answer',sources:[],conversation_id:'c1',message_id:1});
    res.end();
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  try {
    const url=`http://127.0.0.1:${server.address().port}`,c={id:'test',question:'Q',answerable:false};
    const ok=await ask(url,c,new Map());assert.equal(ok.status,'ok');assert(ok.ttft_seconds!==null);assert(ok.sources_seconds<=ok.ttft_seconds);
    mode='truncated';const error=await ask(url,c,new Map());assert.equal(error.status,'error');assert.equal(error.error_type,'Missing_complete_event');
  }finally{await new Promise(resolve=>server.close(resolve));}
});
test('human grading refuses stale answers, incomplete ratings and duplicate reviews',()=>{
  const answer={case_id:'a',repetition:0,status:'ok',answer:'A'};
  const c={id:'a',answerable:true,category:'semantic',expected_answer_points:['A']};
  const review={case_id:'a',repetition:0,answer_sha256:createHash('sha256').update('A').digest('hex'),point_scores:[2],groundedness:2,citation_support:2,abstention:null,reviewer:'test',notes:'Verified A against the retrieved source.',issues:[]};
  assert.equal(grade([answer],[c],[]).overall_pass_rate,null);
  assert.equal(grade([answer,{case_id:'b',status:'error'}],[c],[review]).overall_pass_rate,.5);
  assert.throws(()=>grade([answer],[c],[{...review,answer_sha256:'wrong'}]),/Changed answer/);
  assert.throws(()=>grade([answer],[c],[{...review,point_scores:[null]}]),/Invalid scores/);
  assert.throws(()=>grade([answer],[c],[review,review]),/duplicate/);
});
test('all frozen documents and evaluation cases validate offline',()=>{
  const result=validate();assert.equal(result.documents,89);assert.equal(result.single_turn_cases,320);assert.equal(result.conversation_turns,36);
});

test('CLI records isolated ingestion, repeated queries and graded output against a fake HTTP service',async()=>{
  const temporary=await fs.mkdtemp(path.join(os.tmpdir(),'deepseek-eval-test-'));
  const inventory=[];
  const server=http.createServer(async(req,res)=>{
    const chunks=[];for await(const chunk of req)chunks.push(chunk);const body=Buffer.concat(chunks).toString();
    if(req.url==='/api/files'&&req.method==='GET'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify(inventory));return;}
    if(req.url==='/api/files'&&req.method==='POST'){
      const file={file_id:`file-${inventory.length}`,file_name:body.match(/filename="([^"]+)"/)[1],status:'ready'};
      inventory.push(file);res.writeHead(201,{'Content-Type':'application/json'});res.end(JSON.stringify(file));return;
    }
    const {request_id}=JSON.parse(body);res.writeHead(200,{'Content-Type':'text/event-stream'});
    for(const [event,data] of [['sources',{sources:[]}],['answer_delta',{delta:'Fixture answer'}],['complete',{answer:'Fixture answer',sources:[],conversation_id:'c',message_id:1}]])res.write(`event: ${event}\ndata: ${JSON.stringify({request_id,...data})}\n\n`);
    res.end();
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const exec=promisify(execFile),url=`http://127.0.0.1:${server.address().port}`;
  const tool=new URL('./run.mjs',import.meta.url).pathname;
  try {
    const ingestion=path.join(temporary,'ingestion'),run=path.join(temporary,'run');
    await exec(process.execPath,[tool,'ingest','--base-url',url,'--out',ingestion]);
    assert.equal(inventory.length,89);
    await assert.rejects(()=>exec(process.execPath,[tool,'ingest','--base-url',url,'--out',path.join(temporary,'duplicate')]),/empty isolated instance/);
    const first=(await fs.readFile(new URL('../cases.jsonl',import.meta.url),'utf8')).split('\n')[0];
    const casesPath=path.join(temporary,'cases.jsonl');await fs.writeFile(casesPath,first+'\n');
    await exec(process.execPath,[tool,'run','--base-url',url,'--out',run,'--ingestion',path.join(ingestion,'ingestion.json'),'--cases',casesPath,'--repeat','2','--concurrency','2']);
    const metrics=JSON.parse(await fs.readFile(path.join(run,'metrics.json')));
    assert.equal(metrics.attempts,2);assert.equal(metrics.successful,2);assert.equal(metrics.answer_accuracy,null);
    const reviews=JSON.parse(await fs.readFile(path.join(run,'review-template.json')));
    for(const review of reviews)Object.assign(review,{point_scores:review.point_scores.map(()=>0),groundedness:0,citation_support:0,abstention:null,reviewer:'offline-fixture',notes:'The synthetic fixture answer supplies none of the expected facts.',issues:['Fixture-only incorrect answer']});
    const reviewPath=path.join(temporary,'reviews.json');await fs.writeFile(reviewPath,JSON.stringify(reviews));
    await exec(process.execPath,[new URL('./grade.mjs',import.meta.url).pathname,run,reviewPath]);
    const output=(await fs.readdir(run)).find(name=>name.startsWith('quality-'));
    assert.equal(JSON.parse(await fs.readFile(path.join(run,output))).overall_pass_rate,0);
  }finally{await new Promise(resolve=>server.close(resolve));await fs.rm(temporary,{recursive:true,force:true});}
});
