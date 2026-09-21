import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const evals=path.resolve(base,'..'),corpus=path.join(evals,'materials/deepseek');
const sha=data=>createHash('sha256').update(data).digest('hex');
const json=file=>JSON.parse(fs.readFileSync(file,'utf8'));
const lines=file=>fs.readFileSync(file,'utf8').trim().split('\n').map(JSON.parse);
export function validate() {
  const manifest=json(path.join(corpus,'manifest.json')),texts=new Map(),files=new Set();
  assert.equal(manifest.failures.length,0);
  assert.equal(sha(fs.readFileSync(path.join(corpus,'sitemap.xml'))),manifest.sitemap_sha256);
  for(const doc of manifest.documents) {
    assert(!files.has(doc.file));files.add(doc.file);
    const md=fs.readFileSync(path.join(corpus,doc.file)),txt=fs.readFileSync(path.join(corpus,doc.txt_file));
    assert(md.equals(txt),`MD/TXT mismatch: ${doc.id}`);
    assert.equal(sha(md),doc.sha256,doc.id);assert.equal(md.length,doc.bytes,doc.id);
    const text=new TextDecoder('utf-8',{fatal:true}).decode(md);
    assert.equal([...text].length,doc.characters,doc.id);
    assert(text.startsWith('# '));assert(text.includes(`Source: ${doc.source_url}`));
    assert(!/\p{Script=Han}/u.test(text),`Non-English text: ${doc.id}`);
    assert(!/^Loading\.\.\.$/m.test(text),`UI residue: ${doc.id}`);
    assert(!/[ \t]+$/m.test(text),`Trailing whitespace: ${doc.id}`);
    assert(!/<table[ >]/.test(text),`Unconverted table: ${doc.id}`);
    const fences=text.split('\n').filter(line=>/^```/.test(line));assert.equal(fences.length%2,0,`Unbalanced fences: ${doc.id}`);
    texts.set(`materials/deepseek/${doc.txt_file}`,text);
  }
  const accounted=new Set([...manifest.documents.map(d=>d.source_url),...manifest.exclusions.map(e=>e.url)]);
  for(const url of manifest.discovered_urls)assert(accounted.has(url),`Unaccounted URL: ${url}`);
  const cases=lines(path.join(base,'cases.jsonl')),ids=new Set(),questions=new Set(),families=new Map();
  let evidenceCount=0;
  function check(test,track=true) {
    assert.equal(test.corpus_id,manifest.corpus_id);
    assert(test.question.trim()&&test.expected_answer_points.length);
    assert(!/\p{Script=Han}/u.test(test.question));
    if(track){assert(!ids.has(test.id),test.id);ids.add(test.id);assert(!questions.has(test.question),test.question);questions.add(test.question);}
    assert(test.answerable?test.evidence.length>0:test.evidence.length===0);
    const covered=new Set();
    for(const ref of [...test.evidence,...(test.context_evidence||[])]) {
      const text=texts.get(ref.file);assert(text,ref.file);
      assert.equal([...text].slice(ref.start_offset,ref.end_offset).join(''),ref.quote,test.id);
      assert.equal([...text].slice(0,ref.start_offset).join('').split('\n').length,ref.line,test.id);
      assert.equal([...text].slice(0,ref.end_offset).join('').split('\n').length,ref.end_line,test.id);
      assert(fs.existsSync(path.join(evals,ref.md_file)));
      assert(ref.quote.trim().length>0);
      for(const point of ref.supports_answer_points){assert(point>=1&&point<=test.expected_answer_points.length);covered.add(point);}
      evidenceCount++;
    }
    if(test.answerable)assert.equal(covered.size,test.expected_answer_points.length,`Unmapped answer point: ${test.id}`);
    if(track){if(families.has(test.family_id))assert.equal(families.get(test.family_id),test.split);families.set(test.family_id,test.split);}
  }
  cases.forEach(test=>check(test));
  for(const split of ['dev','test'])assert.deepEqual(lines(path.join(base,`${split}.jsonl`)),cases.filter(test=>test.split===split));
  const conversations=lines(path.join(base,'conversations.jsonl'));
  conversations.forEach(s=>{assert(s.turns.length>1);s.turns.forEach(t=>{check(t,false);assert.equal(cases.find(c=>c.id===t.source_case_id).split,'dev');});});
  const latency=lines(path.join(base,'latency-cases.jsonl'));
  for(const test of latency)assert.deepEqual(test,cases.find(c=>c.id===test.id));
  const coverage=json(path.join(base,'coverage.json'));assert.equal(coverage.total_cases,cases.length);
  const summary={status:'passed',corpus_id:manifest.corpus_id,documents:manifest.documents.length,
    corpus_bytes:manifest.documents.reduce((sum,d)=>sum+d.bytes,0),single_turn_cases:cases.length,
    categories:coverage.by_category,splits:coverage.by_split,conversation_scenarios:conversations.length,
    conversation_turns:conversations.reduce((n,s)=>n+s.turns.length,0),latency_cases:latency.length,
    checked_evidence_spans:evidenceCount,documents_with_case_references:coverage.documents.filter(d=>d.case_ids.length).length,
    duplicate_pages:manifest.documents.filter(d=>d.duplicate_of).map(d=>({id:d.id,duplicate_of:d.duplicate_of})),
    checks:['All captured-source hashes and byte counts','All MD/TXT byte-identical pairs','All discovered URLs captured or explicitly excluded','UTF-8 and English-only corpus text','Markdown table conversion and code-fence balance','Unique case IDs and questions','Every answer point mapped to source evidence','Exact Unicode offsets and line numbers for every evidence span','Identical family split assignment','Conversation and latency fixture integrity'],
    scope:'Offline artifact validation only. No live RAG accuracy, latency, token or cost measurements were performed.'};
  fs.writeFileSync(path.join(base,'validation.json'),JSON.stringify(summary,null,2)+'\n');
  return summary;
}
if(process.argv[1]===fileURLToPath(import.meta.url))console.log(JSON.stringify(validate(),null,2));
