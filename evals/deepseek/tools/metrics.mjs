export const mean = values => values.length ? values.reduce((a,b)=>a+b,0)/values.length : null;
export function percentile(values, p) {
  if (!values.length) return null;
  const sorted = [...values].sort((a,b)=>a-b);
  return sorted[Math.max(0,Math.ceil(p*sorted.length)-1)];
}

export function unionCoverage(start,end,intervals) {
  let cursor=start,total=0;
  for(const [left,right] of intervals.map(([a,b])=>[Math.max(a,start),Math.min(b,end)]).filter(([a,b])=>b>a).sort((a,b)=>a[0]-b[0])) {
    total+=Math.max(0,right-Math.max(cursor,left));cursor=Math.max(cursor,right);
  }
  return total/(end-start);
}

export function locateSources(sources, documents) {
  return sources.map(source=>{
    const doc=documents.get(source.file_name);
    if(!doc) return {...source,offset_status:'unknown_document'};
    const start=doc.text.indexOf(source.text);
    if(!source.text || start<0) return {...source,file:doc.file,offset_status:'text_not_found'};
    if(doc.text.indexOf(source.text,start+1)>=0) return {...source,file:doc.file,offset_status:'ambiguous'};
    return {...source,file:doc.file,offset_status:'unique',start_offset:[...doc.text.slice(0,start)].length,end_offset:[...doc.text.slice(0,start+source.text.length)].length};
  });
}

export function retrievalMetrics(testCase,sources) {
  if(!testCase.answerable) return null;
  const goldFiles=new Set(testCase.evidence.map(e=>e.file));
  const first=sources.findIndex(s=>goldFiles.has(s.file));
  const uncertain=sources.some(s=>s.offset_status!=='unique');
  const recall=uncertain?null:testCase.evidence.map(e=>unionCoverage(e.start_offset,e.end_offset,sources.filter(s=>s.file===e.file).map(s=>[s.start_offset,s.end_offset])));
  return {document_mrr:first<0?0:1/(first+1),
    annotated_char_recall:recall?mean(recall):null,
    full_evidence_recall:recall?mean(recall.map(x=>Number(x===1))):null,
    all_evidence_retrieved:recall?Number(recall.every(x=>x===1)):null,
    source_offset_uncertainty:uncertain};
}

export function summarize(rows,elapsedSeconds) {
  const ok=rows.filter(r=>r.status==='ok');
  const values=key=>ok.map(r=>r[key]).filter(v=>typeof v==='number');
  const timing=key=>({n:values(key).length,p50:percentile(values(key),.5),p95:percentile(values(key),.95),p99:percentile(values(key),.99)});
  const retrieval={};
  for(const key of ['document_mrr','annotated_char_recall','full_evidence_recall','all_evidence_retrieved']) {
    const scores=ok.map(r=>r.retrieval?.[key]).filter(v=>typeof v==='number');
    retrieval[key]={n:scores.length,mean:mean(scores)};
  }
  const tokenRows=ok.filter(r=>r.exact_token_coverage!==null && r.exact_token_coverage!==undefined);
  return {attempts:rows.length,successful:ok.length,failed:rows.length-ok.length,
    completion_rate:rows.length?ok.length/rows.length:null,elapsed_seconds:elapsedSeconds,
    successful_requests_per_second:elapsedSeconds>0?ok.length/elapsedSeconds:null,
    timing_seconds:{end_to_end:timing('latency_seconds'),first_answer_text:timing('ttft_seconds'),sources_ready:timing('sources_seconds')},
    retrieval,exact_token_coverage:{n:tokenRows.length,mean:mean(tokenRows.map(r=>r.exact_token_coverage))},
    answer_accuracy:null,groundedness:null,citation_support:null,abstention_accuracy:null,token_usage:null,cost_usd:null,
    caveats:['Quality requires separate evidence-backed human grading. Exact-token coverage is a lexical diagnostic, not correctness.',
      'Sources-ready time includes HTTP, queueing and pre-generation work; it is not pure retrieval latency.',
      'Time to first answer text is measured from request dispatch, not first SSE keep-alive/start event.',
      'Latency quantiles use nearest rank and successful requests only; failures stay in completion-rate denominator.',
      'This client cannot observe exact provider tokens, charges, server-only stage timings, or CPU/memory use.']};
}

export async function readSSE(response,onEvent) {
  if(!response.ok) throw new Error(`HTTP_${response.status}`);
  const decoder=new TextDecoder();let buffer='';
  const emit=frame=>{
    let event='message';const data=[];
    for(const line of frame.split(/\r?\n/)) {
      if(line.startsWith('event:'))event=line.slice(6).trim();
      if(line.startsWith('data:'))data.push(line.slice(5).trimStart());
    }
    if(data.length)onEvent(event,JSON.parse(data.join('\n')));
  };
  for await(const chunk of response.body) {
    buffer+=decoder.decode(chunk,{stream:true});
    let separator;
    while((separator=/\r?\n\r?\n/.exec(buffer))) {
      emit(buffer.slice(0,separator.index));buffer=buffer.slice(separator.index+separator[0].length);
    }
  }
  buffer+=decoder.decode();
  // A nonempty residual frame means transport ended before frame termination.
  if(buffer.trim())throw new Error('Incomplete_SSE_frame');
}
