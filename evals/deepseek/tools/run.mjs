import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash,randomUUID} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {locateSources,retrievalMetrics,summarize,readSSE} from './metrics.mjs';
const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const corpus=path.resolve(base,'../materials/deepseek');
const sha=value=>createHash('sha256').update(value).digest('hex');
const write=(name,value)=>fs.writeFile(name,JSON.stringify(value,null,2)+'\n');

export async function ask(baseUrl,testCase,documents,timeoutMs=180000,conversationId=null) {
  const started=performance.now(), request_id=randomUUID();let complete,ttft=null,sourcesTime=null,failure=null,completedAt=null;
  const seconds=()=> (performance.now()-started)/1000;
  try {
    const response=await fetch(baseUrl+'/api/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({question:testCase.question,request_id,conversation_id:conversationId}),signal:AbortSignal.timeout(timeoutMs)});
    await readSSE(response,(event,data)=>{
      if(data.request_id!==request_id)throw new Error('Mismatched_request_id');
      if(event==='sources'&&sourcesTime===null)sourcesTime=seconds();
      if(event==='answer_delta'&&data.delta?.length&&ttft===null)ttft=seconds();
      if(event==='error')failure='SSE_error';
      if(event==='complete'){complete=data;completedAt=seconds();}
    });
    if(failure || !complete)throw new Error(failure || 'Missing_complete_event');
    const sources=locateSources(complete.sources,documents);
    const exact=testCase.exact_answer_tokens||[];
    return {case_id:testCase.id,status:'ok',question:testCase.question,answer:complete.answer,sources,
      conversation_id:complete.conversation_id,message_id:complete.message_id,retrieval_question:complete.retrieval_question,
      citation_check:complete.citation_check,latency_seconds:completedAt,ttft_seconds:ttft,sources_seconds:sourcesTime,
      retrieval:retrievalMetrics(testCase,sources),exact_token_coverage:exact.length?exact.filter(t=>complete.answer.includes(t)).length/exact.length:null};
  }catch(error) {
    const allowed=/^(HTTP_\d+|SSE_error|Missing_complete_event|Mismatched_request_id|Incomplete_SSE_frame)$/;
    return {case_id:testCase.id,status:'error',error_type:allowed.test(error.message)?error.message:error.name,
      latency_seconds:seconds(),ttft_seconds:ttft,sources_seconds:sourcesTime};
  }
}

async function main() {
  const [command,...raw]=process.argv.slice(2);const args={};
  for(let i=0;i<raw.length;i+=2){if(!raw[i].startsWith('--')||raw[i+1]===undefined)throw new Error('Options require --name value pairs');args[raw[i].slice(2)]=raw[i+1];}
  if(!['ingest','run','conversation'].includes(command)||!args['base-url']||!args.out)throw new Error('Usage: node run.mjs ingest|run|conversation --base-url URL --out NEW_DIRECTORY [--ingestion FILE] [--cases FILE] [--repeat N] [--concurrency N] [--timeout-ms N] [--config FILE]');
  const baseUrl=args['base-url'].replace(/\/$/,'');
  const manifestBytes=await fs.readFile(path.join(corpus,'manifest.json'));
  const manifest=JSON.parse(manifestBytes);
  const documents=new Map();
  for(const doc of manifest.documents) {
    const bytes=await fs.readFile(path.join(corpus,doc.txt_file));
    if(sha(bytes)!==doc.sha256)throw new Error(`Corpus changed: ${doc.id}`);
    documents.set(path.basename(doc.txt_file),{file:`materials/deepseek/${doc.txt_file}`,text:bytes.toString()});
  }
  const filesResponse=await fetch(baseUrl+'/api/files');
  if(!filesResponse.ok)throw new Error(`File inventory HTTP ${filesResponse.status}`);
  const inventory=await filesResponse.json();
  const out=path.resolve(args.out);
  if(command==='ingest') {
    if(inventory.length)throw new Error('Ingestion requires an empty isolated instance; no existing data is deleted.');
    await fs.mkdir(out,{recursive:false});
    const record={corpus_id:manifest.corpus_id,manifest_sha256:sha(manifestBytes),base_url:baseUrl,started_at:new Date().toISOString(),status:'running',documents:[]};
    const start=performance.now();
    await write(path.join(out,'ingestion.json'),record);
    try {
      for(const doc of manifest.documents) {
        const started=performance.now(),form=new FormData();
        form.append('file',new Blob([await fs.readFile(path.join(corpus,doc.txt_file))],{type:'text/plain'}),path.basename(doc.txt_file));
        const response=await fetch(baseUrl+'/api/files',{method:'POST',body:form,signal:AbortSignal.timeout(Number(args['timeout-ms']||600000))});
        if(!response.ok)throw new Error(`Upload_HTTP_${response.status}`);
        const result=await response.json();
        if(result.status!=='ready')throw new Error('Upload_not_ready');
        record.documents.push({...result,sha256:doc.sha256,bytes:doc.bytes,latency_seconds:(performance.now()-started)/1000});
        await write(path.join(out,'ingestion.json'),record);
        console.log(`Indexed ${record.documents.length}/${manifest.documents.length}: ${doc.id}`);
      }
      record.status='complete';
    }catch(error){record.status='failed';record.error_type=error.name;throw error;}
    finally{record.elapsed_seconds=(performance.now()-start)/1000;await write(path.join(out,'ingestion.json'),record);}
    return;
  }
  if(!args.ingestion)throw new Error('--ingestion must identify the completed ingestion.json');
  const ingestion=JSON.parse(await fs.readFile(args.ingestion));
  if(ingestion.status!=='complete'||ingestion.manifest_sha256!==sha(manifestBytes)||ingestion.base_url!==baseUrl)throw new Error('Ingestion identity does not match this instance and corpus');
  if(inventory.length!==ingestion.documents.length||inventory.some(file=>file.status!=='ready'||!ingestion.documents.some(d=>d.file_id===file.file_id&&d.file_name===file.file_name)))throw new Error('Live file inventory differs from the recorded corpus');
  const casesPath=path.resolve(args.cases || path.join(base,command==='conversation'?'conversations.jsonl':'dev.jsonl'));
  const caseBytes=await fs.readFile(casesPath);
  const tests=caseBytes.toString().trim().split('\n').map(JSON.parse);
  if(tests.flatMap(test=>test.turns||[test]).some(test=>test.corpus_id!==manifest.corpus_id))throw new Error('Cases belong to a different corpus');
  const repeat=Number(args.repeat||1),concurrency=Number(args.concurrency||1),timeout=Number(args['timeout-ms']||180000);
  if(![repeat,concurrency,timeout].every(n=>Number.isInteger(n)&&n>0))throw new Error('repeat, concurrency and timeout-ms must be positive integers');
  await fs.mkdir(out,{recursive:false});
  const run={started_at:new Date().toISOString(),status:'running',command,base_url:baseUrl,repeat,concurrency,
    manifest_sha256:sha(manifestBytes),cases_sha256:sha(caseBytes),timeout_ms:timeout,
    client_git_revision:execFileSync('git',['rev-parse','HEAD']).toString().trim(),
    client_dirty:Boolean(execFileSync('git',['status','--porcelain']).toString().trim()),
    server_configuration:args.config?JSON.parse(await fs.readFile(args.config)):null,
    note:'Server identity/settings are user-supplied, not independently attested by this HTTP client.'};
  await write(path.join(out,'run.json'),run);
  await fs.writeFile(path.join(out,'cases.jsonl'),caseBytes);
  await fs.writeFile(path.join(out,'manifest.json'),manifestBytes);
  const jobs=Array.from({length:repeat},(_,repetition)=>tests.map(test=>({test,repetition}))).flat();
  const rows=[];let cursor=0;
  // Serialize file writes even when several HTTP requests finish together.
  let pendingWrite=Promise.resolve();
  const append=row=>{rows.push(row);pendingWrite=pendingWrite.then(()=>fs.appendFile(path.join(out,'answers.jsonl'),JSON.stringify(row)+'\n'));return pendingWrite;};
  const started=performance.now();
  await Promise.all(Array.from({length:concurrency},async()=>{
    while(cursor<jobs.length) {
      const {test,repetition}=jobs[cursor++];
      const turns=command==='conversation'?test.turns:[test];let conversationId=null;
      for(const [turnIndex,turn] of turns.entries()) {
        const row=await ask(baseUrl,turn,documents,timeout,conversationId);
        Object.assign(row,{repetition,category:turn.category,split:turn.split,recorded_at:new Date().toISOString()});
        if(command==='conversation')Object.assign(row,{scenario_id:test.id,turn_index:turnIndex+1});
        await append(row);
        console.log(`${row.case_id}: ${row.status}`);
        if(row.status!=='ok'&&command==='conversation') {
          for(const skipped of turns.slice(turnIndex+1))await append({case_id:skipped.id,status:'blocked',error_type:'Previous_turn_failed',scenario_id:test.id,repetition,category:skipped.category});
          break;
        }
        if(command==='conversation')conversationId=row.conversation_id;
      }
    }
  }));
  run.status='complete';run.elapsed_seconds=(performance.now()-started)/1000;run.completed_at=new Date().toISOString();
  await write(path.join(out,'run.json'),run);
  const report=summarize(rows,run.elapsed_seconds);
  report.by_category=Object.fromEntries([...new Set(rows.map(r=>r.category))].map(category=>[category,summarize(rows.filter(r=>r.category===category),null)]));
  await write(path.join(out,'metrics.json'),report);
  const flatTests=new Map(tests.flatMap(t=>command==='conversation'?t.turns:[t]).map(t=>[t.id,t]));
  await write(path.join(out,'review-template.json'),rows.filter(r=>r.status==='ok').map(row=>({case_id:row.case_id,repetition:row.repetition,answer_sha256:sha(row.answer),
    point_scores:flatTests.get(row.case_id).expected_answer_points.map(()=>null),groundedness:null,citation_support:null,abstention:null,reviewer:null,notes:'',issues:[]})));
  console.log(`Saved ${rows.length} records to ${out}; factual quality remains ungraded.`);
}
if(process.argv[1]===fileURLToPath(import.meta.url))await main();
