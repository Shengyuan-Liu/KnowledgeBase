import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {mean} from './metrics.mjs';
const hash=text=>createHash('sha256').update(text).digest('hex');
export function grade(answers,cases,reviews) {
  const byCase=new Map(cases.flatMap(c=>c.turns||[c]).map(c=>[c.id,c]));
  const key=row=>`${row.case_id}:${row.repetition}`;
  const byAnswer=new Map(answers.map(a=>[key(a),a]));
  const seen=new Set(),scored=[];
  const score=value=>Number.isInteger(value)&&value>=0&&value<=2;
  for(const review of reviews) {
    const id=key(review),answer=byAnswer.get(id),test=byCase.get(review.case_id);
    if(seen.has(id)||!answer||answer.status!=='ok'||!test)throw new Error(`Invalid/duplicate review identity: ${id}`);
    seen.add(id);
    if(review.answer_sha256!==hash(answer.answer))throw new Error(`Changed answer: ${id}`);
    if(!Array.isArray(review.point_scores)||review.point_scores.length!==test.expected_answer_points.length||!review.point_scores.every(score)||!score(review.groundedness))throw new Error(`Invalid scores: ${id}`);
    if(test.answerable ? (!score(review.citation_support)||review.abstention!==null) : (!(review.citation_support===null||score(review.citation_support))||!score(review.abstention)))throw new Error(`Invalid citation/abstention rating: ${id}`);
    if(!review.reviewer?.trim()||!review.notes?.trim()||!Array.isArray(review.issues))throw new Error(`Missing reviewer/evidence notes: ${id}`);
    const pass=review.point_scores.every(x=>x===2)&&review.groundedness===2&&(review.citation_support===null||review.citation_support===2)&&(review.abstention===null||review.abstention===2);
    scored.push({case_id:review.case_id,repetition:review.repetition,category:test.category,answerable:test.answerable,
      answer_point_score:mean(review.point_scores)/2,groundedness:review.groundedness/2,citation_support:review.citation_support===null?null:review.citation_support/2,
      abstention:review.abstention===null?null:review.abstention/2,pass,reviewer:review.reviewer});
  }
  const successful=answers.filter(a=>a.status==='ok').length,pending=successful-scored.length;
  const aggregate=rows=>{
    const metric=(key,filter=()=>true)=>{const values=rows.filter(filter).map(r=>r[key]).filter(v=>typeof v==='number');return {n:values.length,mean:mean(values)};};
    return {graded:rows.length,answer_point_accuracy:metric('answer_point_score',r=>r.answerable),groundedness:metric('groundedness'),citation_support:metric('citation_support'),abstention_score:metric('abstention'),fully_correct_among_graded:rows.length?rows.filter(r=>r.pass).length/rows.length:null};
  };
  return {attempts:answers.length,successful,pending,failures:answers.length-successful,
    overall_pass_rate:pending===0&&answers.length?scored.filter(r=>r.pass).length/answers.length:null,
    ...aggregate(scored),by_category:Object.fromEntries([...new Set(scored.map(r=>r.category))].map(c=>[c,aggregate(scored.filter(r=>r.category===c))])),cases:scored,
    note:'Human ratings are judgments. Pending reviews suppress the overall pass rate. Generation errors and blocked conversation turns count as failed attempts. Report denominators and reviewer identities.'};
}
if(process.argv[1]===fileURLToPath(import.meta.url)) {
  const [directory,reviewPath]=process.argv.slice(2);
  if(!directory||!reviewPath)throw new Error('Usage: node grade.mjs RUN_DIRECTORY REVIEW_JSON');
  const readLines=async p=>(await fs.readFile(p,'utf8')).trim().split('\n').map(JSON.parse);
  const run=JSON.parse(await fs.readFile(path.join(directory,'run.json')));
  if(run.status!=='complete')throw new Error('Quality aggregation requires a complete run');
  const report=grade(await readLines(path.join(directory,'answers.jsonl')),await readLines(path.join(directory,'cases.jsonl')),JSON.parse(await fs.readFile(reviewPath)));
  const destination=path.join(directory,`quality-${new Date().toISOString().replaceAll(':','-')}.json`);
  await fs.writeFile(destination,JSON.stringify(report,null,2)+'\n');console.log(destination);
}
