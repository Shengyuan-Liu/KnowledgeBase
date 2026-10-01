import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const directory = dirname(fileURLToPath(import.meta.url));
const read = name => JSON.parse(readFileSync(join(directory, name), 'utf8'));
const save = (name, data) => writeFileSync(join(directory, name), JSON.stringify(data, null, 2) + '\n', { flag: 'wx' });
const acceptance = read('acceptance.json');
const probe = read('scope-probe-2.json');
const initial = read('storage-initial.json'), final = read('storage-final.json');
const rows = [...acceptance.answers, ...probe.rows];
const normalize = text => text.replace(/\s+/g, ' ').trim();
const namesByFile = Object.fromEntries(read('files-before.json').map(f => [f.file_id, f.file_name]));
const filesByChunk = Object.fromEntries([...initial.tables.chunks, ...initial.tables.parent_chunks].map(c => [c.chunk_id, namesByFile[c.file_id]]));
const mean = values => values.reduce((sum, value) => sum + value, 0) / values.length;
function distribution(values) {
  const sorted = [...values].sort((a, b) => a - b);
  if (!values.length) return { status: 'unavailable', sample_count: 0 };
  return { sample_count: values.length, mean: mean(values), p50: sorted[Math.ceil(.5 * sorted.length) - 1], p95: sorted[Math.ceil(.95 * sorted.length) - 1], percentile_method: 'nearest rank', unit: 'milliseconds' };
}
const rankingRows = [], coverage = [];
function rank(stage, question, actual, relevant) {
  const documents = [...new Set(actual.filter(Boolean))].slice(0, 5);
  const gold = [...new Set(relevant)];
  const hits = documents.map(name => Number(gold.includes(name)));
  const relevantCount = hits.reduce((a, b) => a + b, 0);
  const first = hits.indexOf(1);
  const dcg = hits.reduce((sum, gain, index) => sum + gain / Math.log2(index + 2), 0);
  const idcg = gold.slice(0, 5).reduce((sum, _, index) => sum + 1 / Math.log2(index + 2), 0);
  rankingRows.push({ stage, question, documents, relevant: gold, K: 5, recall: relevantCount / gold.length, precision: relevantCount / 5, hit_rate: Number(relevantCount > 0), mrr: first < 0 ? 0 : 1 / (first + 1), ndcg: dcg / idcg });
}
for (const row of rows.filter(r => r.gold.length)) {
  const diagnostics = row.answer.retrieval;
  const gold = row.gold.map(g => g.file);
  const runs = diagnostics.planning?.trace?.runs;
  const units = runs ? runs.map(run => ({ id: `${row.id}:${run.query_ids.join(',')}`, d: run.result.diagnostics, gold: run.result.diagnostics.document_scope.matches.map(f => f.file_name) })) : [{ id: row.id, d: diagnostics, gold }];
  for (const unit of units) {
    rank('candidate_fusion_per_query', unit.id, unit.d.fused_matches.map(hit => filesByChunk[hit.chunk_id]), unit.gold);
    rank('reranking_per_query', unit.id, (unit.d.rerank?.matches ?? []).map(hit => filesByChunk[hit.chunk_id]), unit.gold);
  }
  rank('final_supplied_documents_per_answer', row.id, row.answer.sources.map(s => s.file_name), gold);
  coverage.push({ id: row.id, facts: row.gold.map(g => ({ ...g, covered: row.answer.sources.some(s => s.file_name === g.file && normalize(s.text).includes(normalize(g.quote))) })) });
}
const rankingSummary = Object.fromEntries([...new Set(rankingRows.map(r => r.stage))].map(stage => {
  const matching = rankingRows.filter(r => r.stage === stage);
  return [stage, { sample_count: matching.length, ...Object.fromEntries(['recall', 'precision', 'hit_rate', 'mrr', 'ndcg'].map(key => [key, mean(matching.map(r => r[key]))])) }];
}));
const allFacts = coverage.flatMap(row => row.facts);
const streams = readFileSync(join(directory, 'streams.jsonl'), 'utf8').trim().split('\n').map(line => JSON.parse(line));
const timings = streams.map(stream => ({
  question: stream.request.question, mode: stream.request.retrieval_mode,
  first_answer_delta_ms: stream.events.find(e => e.event === 'answer_delta' && e.data.delta)?.elapsed_ms ?? null,
  complete_response_ms: stream.events.find(e => e.event === 'complete')?.elapsed_ms ?? null,
  outcome: stream.read_error ? 'cancelled_by_test' : 'completed',
  type: stream.request.question.startsWith('Using only my uploaded') ? 'scope_error_response' : stream.request.retrieval_mode === 'planned' ? 'planned_model_answer' : 'single_model_answer',
}));
const timingSummary = Object.fromEntries([...new Set(timings.map(r => r.type))].map(type => {
  const matching = timings.filter(r => r.type === type && r.outcome === 'completed');
  return [type, { first_answer_delta: distribution(matching.map(r => r.first_answer_delta_ms)), complete_response: distribution(matching.map(r => r.complete_response_ms)) }];
}));
const stageTimings = rows.map(row => ({ id: row.id, retrieval: Object.fromEntries(Object.entries(row.answer.retrieval).filter(([key, value]) => key.endsWith('_seconds') && typeof value === 'number')), planned_queries: row.answer.retrieval.planning?.trace?.runs.map(run => ({ query_ids: run.query_ids, total_seconds: run.seconds, ...Object.fromEntries(Object.entries(run.result.diagnostics).filter(([key, value]) => key.endsWith('_seconds') && typeof value === 'number')) })) ?? [] }));
const usageByResponse = {};
function usage(value) {
  if (value && typeof value === 'object') {
    if (value.response_id && value.usage) usageByResponse[value.response_id] = { model: value.model, usage: value.usage, billed_cost: value.billed_cost ?? null, billed_cost_status: value.billed_cost_status ?? 'unavailable', seconds: value.seconds };
    Object.values(value).forEach(usage);
  }
}
rows.forEach(usage);
const reviewedClaims = [
  { id: 'weekday', claim: 'The library closes at 5 PM on weekdays.', source_id: 1, file: 'cedar-hours.txt', support: 'Cedar Library closes at 5 PM Monday through Friday.' },
  { id: 'followup', claim: 'The library closes at 7 PM on Saturday.', source_id: 1, file: 'cedar-hours.txt', support: 'Cedar Library closes at 7 PM on Saturday and Sunday.' },
  { id: 'markdown', claim: 'Reserve at least 24 hours in advance.', source_id: 1, file: 'cedar-access.md', support: 'Reserve the quiet room at least 24 hours in advance.' },
  { id: 'markdown', claim: 'The quiet room is on the second floor.', source_id: 1, file: 'cedar-access.md', support: 'The quiet room is on the second floor.' },
  { id: 'pdf-planned', claim: 'Project Juniper was assigned to Quenwick Laboratory.', source_id: 1, file: 'assignment.pdf', support: 'Project Juniper was assigned to Quenwick Laboratory.' },
  { id: 'pdf-planned', claim: 'The calibration interval is 17 days.', source_id: 2, file: 'laboratory-register.pdf', support: 'Quenwick Laboratory: calibration interval is 17 days.' },
  { id: 'explicit-source-unanswerable', claim: 'The supplied cedar-hours excerpt does not specify the PIN.', source_id: 1, file: 'cedar-hours.txt', support: 'Absence claim checked against the complete supplied excerpt and frozen source; it only covers hours and the library-card rule.' },
];
const reviews = rows.map(row => ({
  id: row.id, answerable: row.gold.length > 0,
  result: ['generic-source-answerable', 'unanswerable'].includes(row.id) ? 'failed' : 'passed',
  reason: row.id === 'generic-source-answerable' ? 'Incorrect abstention: relevant document is ready and contains the answer; a generic source phrase is treated as a filename.' : row.id === 'unanswerable' ? 'PIN was not invented, but the response gives an erroneous missing-document explanation and never tests evidence sufficiency.' : row.id === 'explicit-source-unanswerable' ? 'Appropriate abstention after retrieving the named source; no PIN is present.' : 'Expected facts are correct, relevant and supported by the cited excerpts.',
  answer: row.answer.content,
}));
save('review.json', { reviewer: 'Codex model, not human', method: 'Read every unique answer and its exact supplied excerpts; compare frozen expected points and cited source IDs, then inspect screenshots.', reviews, reviewed_claims: reviewedClaims, visual_review: ['text-chat.png', 'pdf-viewer.png', 'mobile-evidence.png', 'planned-evidence.png', 'generic-source-answerable-2.png', 'explicit-source-unanswerable-2.png'], visual_result: 'Readable desktop and mobile evidence, original PDF rendered correctly; generic-source refusal visibly reproduced.', unresolved_issues: [
  { severity: 'functional', file: 'knowledgebase/rag/scope.py', issue: 'Generic source phrase "my uploaded documents" resolves as a missing filename. Reproduced with an answerable question.', status: 'not fixed; this request is browser verification', provenance: 'scope-provenance.json' },
  { severity: 'cosmetic', issue: 'GET /favicon.ico returns 404.', status: 'not fixed; no observed workflow impact' },
], harness_failure: 'First supplemental attempt failed while reading the already-consumed SSE response via Playwright. It is retained unchanged. The second attempt records unavailable response bodies and continues; it still reports the product failure.' });

const metric = (status, value, reason, sample_count, method, aggregation = 'none') => ({ status, value, unit: status === 'measured' ? 'see value and method' : null, reason, sample_count, population: 'This synthetic acceptance workload only', method, aggregation, artifact: 'measurement.json; review.json; raw answer/stream/storage artifacts' });
const inventory = {};
for (const [name, key] of [['Recall@K','recall'],['Precision@K','precision'],['Hit Rate@K','hit_rate'],['MRR','mrr'],['NDCG@K','ndcg']]) inventory[name] = metric('measured', Object.fromEntries(Object.entries(rankingSummary).map(([stage, summary]) => [stage, {value:summary[key],sample_count:summary.sample_count}])), null, rankingRows.length, 'K=5, binary document relevance, deduplicate documents before cutoff; precision denominator stays 5 when fewer documents are returned. Candidate fusion and reranking use five executed subqueries plus one failed-scope query; final evidence uses five answerable questions. Planned subquery labels follow its explicit file scope.', 'macro mean within each stage; never across stages');
inventory['Final evidence coverage'] = metric('measured', {covered:allFacts.filter(f=>f.covered).length,total:allFacts.length,ratio:allFacts.filter(f=>f.covered).length/allFacts.length}, null, allFacts.length, 'Frozen source facts; whitespace-normalized exact quote present in actual supplied sources, including the supplemental false refusal.', 'micro facts');
inventory['Answer correctness'] = metric('measured', {passed:5,total:7,ratio:5/7}, null, 7, 'Codex review of unique cases: correct expected facts or a justified source-based abstention. Both generic-source cases fail. Not independent ground truth.', 'case pass rate');
inventory['Faithfulness'] = metric('measured', {supported:7,total:7,ratio:1}, null, 7, 'Seven substantive claims in five useful answers, including one explicitly scoped absence claim; scope-error messages are separate correctness failures.', 'claim support rate');
inventory['Answer completeness'] = metric('measured', {present:6,expected:7,ratio:6/7}, null, 7, 'Expected fact coverage across five answerable questions; the supplemental false refusal contributes one missing fact.', 'micro facts');
inventory['Answer relevance'] = metric('measured', {passed:5,total:7,ratio:5/7}, null, 7, 'Addresses the requested facts or explains absent source information; unrelated missing-filename messages fail.', 'case pass rate');
inventory['Citation support'] = metric('measured', {supported:7,total:7,ratio:1}, null, 7, 'Review each claim-to-citation pair against the actual excerpt; see reviewed_claims in review.json.', 'claim-citation pairs');
inventory['Citation coverage'] = metric('measured', {cited_supported:7,requires_citation:7,ratio:1}, null, 7, 'All seven substantive source claims require citations, including the scoped absence claim; generic-scope error messages are excluded and reported as failures.', 'claim rate');
inventory['Abstention'] = metric('measured', {unanswerable:{withheld_unknown_secret:2,total:2,appropriate_source_based_reason:1},answerable:{incorrect_abstentions:1,total:5}}, null, 7, 'Separate refusal to invent a PIN from giving an appropriate reason; retain incorrect abstention on an answerable question.');
inventory['First-answer-delta latency'] = metric('measured', timingSummary, 'Supplemental probe timings are unavailable; its UI completion duration is retained separately. Cancellation is retained separately, not counted as a completed answer.', 5, 'Fetch invocation to first nonempty answer_delta observed through cloned SSE reader; includes queue/network and local inference, excludes startup/ingestion.', 'mean/P50/P95 nearest rank, grouped by response type');
inventory['Complete-response latency'] = metric('measured', timingSummary, 'Supplemental probe has UI-ready duration only, not equivalent SSE completion measurement.', 5, 'Fetch invocation to complete SSE event, after persistence. Scope-error response stays separate from model answers.', 'mean/P50/P95 nearest rank, grouped by response type');
inventory['Stage latency'] = metric('measured', stageTimings, 'Search/fusion are not timed separately by the application; provider generation-only time and queue separation unavailable. Do not sum duplicated retained trace snapshots.', 7, 'Recorded application diagnostic stage boundaries in seconds, plus final planned-trace per-query times.', 'raw per-case values');
inventory['Token usage and cost'] = metric('measured', {recorded_structured_calls:usageByResponse,evidence_tokens:rows.map(r=>({id:r.id,tokens:r.answer.retrieval.evidence_tokens})),answer_embedding_usage:{status:'unavailable',reason:'Production answer and embedding clients do not expose usage in HTTP/history records.'},billed_cost:{status:'unavailable',reason:'No billing figures returned in saved records.'},local_reranking:'Local MPS compute, not a paid reranking API call.'}, 'Only structured planning/binding/assessment usage is available; this is not total request token usage or a cost estimate.', Object.keys(usageByResponse).length, 'Deduplicate structured-call usage by response_id; keep source records and requested/resolved model IDs.');
inventory['Reliability'] = metric('measured', {stream_attempts:9,completed_persisted_exchanges:8,intentional_cancellations:1,server_error_responses:0,browser_page_errors:0,unique_semantic_cases_passed:5,unique_semantic_cases_failed:2,test_harness_failures:1,sdk_retries:{status:'unavailable',reason:'Configured maximum is 2; individual retries are not emitted by the application.'}}, 'One failed harness attempt produced a duplicate scope-error exchange; retained in final storage and excluded from unique-question scoring.', 9, 'Server access log, persisted snapshots, browser events and all command attempts. HTTP 200/completed is distinct from answer correctness.');
inventory['Concurrency and throughput'] = metric('unavailable', null, 'Sequential browser interaction at concurrency 1; deliberate UI pauses and inspection make this unsuitable as a throughput or load-capacity benchmark.', 1, 'not measured');
inventory['Ingestion and index'] = metric('measured', {uploads:acceptance.steps.filter(s=>s.name==='upload-ready').map(s=>s.details),initial_index_and_db_bytes:initial.bytes,final_index_and_db_bytes:final.bytes,original_file_count:4,final_file_count:3,deleted_original_http_status:404,historical_sources_preserved:true,updates:{status:'not_applicable',reason:'No document update feature exercised.'}}, 'Size includes database, Chroma files and PDF originals; history grows during the run, so before/after byte difference is not a deletion-efficiency metric. First PDF ingestion includes lazy model startup.', 4, 'File chooser action to Ready UI; read-only SQLite snapshots and directory byte totals.');
save('measurement.json', { status:'completed_with_known_product_failure',code_commit:read('environment.json').code_commit,metric_inventory:inventory,ranking_rows:rankingRows,ranking_summary:rankingSummary,coverage,timings,timing_summary:timingSummary,stage_timings:stageTimings,model_resolution:{answer:'Requested gpt-4.1; exact answer response revision not retained.',embedding:'Requested text-embedding-3-small; exact response revision not retained.',structured_calls:Object.values(usageByResponse).map(v=>v.model),reranker:acceptance.answers[0].answer.retrieval.rerank},limits:['Synthetic small corpus; no general RAG quality or load-capacity claim.','No live before/after baseline on the pre-refactor commit; prior offline equality is a separate record.','Original protocol regex smoke check accepted a generic-scope refusal; semantic review overrides that as a failure without rewriting raw artifacts.','All attempts remain, including the first supplemental capture failure.'] });
console.log(JSON.stringify({rankingSummary,timingSummary,coverage:[allFacts.filter(f=>f.covered).length,allFacts.length],structured_usage_records:Object.keys(usageByResponse).length}, null, 2));
