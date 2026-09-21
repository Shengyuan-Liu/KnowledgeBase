import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const cases=fs.readFileSync(path.join(base,'cases.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const byId=new Map(cases.map(c=>[c.id,c]));
const scenarios=[
  ['files',['file-upload-semantic','file-upload-limit-semantic','file-expiry-semantic'],[null,'How big can that upload be, and how long can it take?','Can I make it expire automatically, or keep it permanently?']],
  ['reasoning',['thinking-default-semantic','ignored-sampling-semantic','cot-with-tools-semantic'],[null,'In that mode, do randomness and repetition penalties have an effect?','If I also use tools in that mode, must I resend earlier reasoning, even when no function ran?']],
  ['cache',['cache-default-semantic','cache-counters-semantic','cache-randomness-semantic'],[null,'Which response counters tell me whether that reused context?','Does that make the generated answer identical each time?']],
  ['json',['json-setup-semantic','json-truncation-semantic','strict-object-semantic'],[null,'What should I do if that JSON ends halfway through or comes back blank?','Now switch to strict tool schemas: may object fields be optional or allow extra properties?']],
  ['balance',['balance-api-semantic','balance-priority-semantic','unanswerable-personal-balance'],[null,'If it contains both granted and topped-up credit, which is spent first?','So what is my own dollar balance right now?']],
  ['vision',['vision-url-semantic','vision-reuse-semantic','vision-dimension-semantic'],[null,'What alternative supports a larger image and avoids resending its bytes?','If I send 15 images in one request, what is the per-side pixel limit?']],
  ['responses',['responses-stream-end-semantic','responses-state-semantic','responses-parallel-semantic'],[null,'Can that same API resume state using a previous response identifier?','Does that API honor a request to disable parallel tool calls?']],
  ['rate',['concurrency-values-semantic','concurrency-account-semantic','concurrency-expansion-semantic'],[null,'Can I multiply those limits by creating more API keys under the same account?','How do I request a higher allowance, and does expansion cost extra?']],
  ['refund',['faq-balance-validity','faq-refund-policy','unanswerable-refund-arrival'],[null,'How would I refund an unused part of that balance for online payment versus a corporate transfer?','On which exact day will my own refund arrive?']],
  ['prefix',['prefix-setup-semantic','fim-purpose-semantic','fim-limit-semantic'],[null,'What if I know both the beginning and ending and need the missing middle instead?','What output cap and base address apply to that gap-filling feature?']],
  ['integration',['integration-detail-6','integration-detail-16','integration-detail-20'],[null,'Switch to Oh My Pi: where does its custom model configuration go?','And where is the corresponding Linux/macOS configuration file for Pi itself?']],
  ['history',['history-news260821','vision-token-cap-semantic','conflict-pro-routing'],[null,'What cap does the current captured Vision guide give instead?','Changing topics: what do the pricing table, September 10 announcement and Change Log say about V4 Pro routing after September 14?']]
];
const conversations=scenarios.map(([name,ids,questions])=>({id:`conversation-${name}`,corpus_id:cases[0].corpus_id,split:'development',
  purpose:'Evaluate reference resolution, topic switching, fresh retrieval, and refusal without inventing account state.',
  turns:ids.map((id,i)=>{
    const original=byId.get('ds-'+id);if(!original)throw new Error(id);
    if(original.split!=='dev')throw new Error(`Development conversation reuses reserved case: ${original.id}`);
    return {...original,id:`ds-conversation-${name}-${i+1}`,source_case_id:original.id,split:'development',
      category:'multi_turn',question:questions[i]||original.question,standalone_reference_question:original.question};
  })}));
fs.writeFileSync(path.join(base,'conversations.jsonl'),conversations.map(c=>JSON.stringify(c)).join('\n')+'\n');
const representative=[];
for(const category of [...new Set(cases.map(c=>c.category))]) representative.push(...cases.filter(c=>c.category===category&&c.split==='dev').slice(0,6));
fs.writeFileSync(path.join(base,'latency-cases.jsonl'),representative.map(c=>JSON.stringify(c)).join('\n')+'\n');
fs.writeFileSync(path.join(base,'workloads.json'),JSON.stringify({schema_version:1,corpus_id:cases[0].corpus_id,
  latency_cases:representative.length,conversation_scenarios:conversations.length,conversation_turns:conversations.reduce((n,c)=>n+c.turns.length,0),
  workloads:[
    {id:'quality-dev',cases:'dev.jsonl',repeat:1,concurrency:1,purpose:'Development diagnosis by category; human-grade each successful answer.'},
    {id:'quality-frozen-test',cases:'test.jsonl',repeat:1,concurrency:1,purpose:'Reserved family split. Do not tune on these answers; public-doc/model pretraining overlap is not excluded.'},
    {id:'latency-first-pass',cases:'latency-cases.jsonl',repeat:1,concurrency:1,purpose:'First pass after a fresh app process and completed ingestion; provider cache state is unknown.'},
    {id:'latency-repeat',cases:'latency-cases.jsonl',repeat:5,concurrency:1,purpose:'Repeated-question timings in the same running instance, fresh conversation for every request.'},
    {id:'load-2',cases:'latency-cases.jsonl',repeat:3,concurrency:2,purpose:'Two independent conversations in flight. Compare throughput, tails, failures, and correctness with concurrency 1.'},
    {id:'load-4',cases:'latency-cases.jsonl',repeat:3,concurrency:4,purpose:'Four independent conversations in flight; diagnostic stress, not a production capacity claim.'},
    {id:'multi-turn',cases:'conversations.jsonl',repeat:1,concurrency:1,purpose:'36 turns across 12 isolated conversations; turns within a conversation are sequential.'}
  ],
  required_run_metadata:['corpus and cases hashes','app code revision','answer, embedding and resolver model identifiers','chunk size and overlap','top_k','history limit','machine and network','run start/end','cache-state description','timeout','concurrency','repeat','reviewer'],
  never_infer:['accuracy from retrieval distance','provider cache hits from low latency','cost or model tokens from character counts','server retrieval duration from client sources-ready time']},null,2)+'\n');
console.log(`Built ${conversations.length} conversations and ${representative.length} latency cases.`);
