import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const directory = dirname(fileURLToPath(import.meta.url));
const measurement = JSON.parse(readFileSync(join(directory, 'measurement.json'), 'utf8'));
const groups = {};
const add = (group, values) => {
  groups[group] ??= {};
  for (const [stage, seconds] of Object.entries(values)) (groups[group][stage] ??= []).push(seconds);
};
for (const row of measurement.stage_timings) {
  const group = ['unanswerable', 'generic-source-answerable'].includes(row.id) ? 'scope_error_responses' : row.id === 'pdf-planned' ? 'planned_answer_top_level' : 'single_retrieval';
  add(group, row.retrieval);
  row.planned_queries.forEach(query => add('planned_subqueries', Object.fromEntries(Object.entries(query).filter(([, value]) => typeof value === 'number'))));
}
add('ingestion', { ui_upload_to_ready_seconds: measurement.metric_inventory['Ingestion and index'].value.uploads[0].ui_ready_ms / 1000 });
for (const upload of measurement.metric_inventory['Ingestion and index'].value.uploads.slice(1)) add('ingestion', {ui_upload_to_ready_seconds:upload.ui_ready_ms / 1000});
const result = Object.fromEntries(Object.entries(groups).map(([group, stages]) => [group, Object.fromEntries(Object.entries(stages).map(([stage, values]) => {
  const sorted = [...values].sort((a, b) => a - b);
  return [stage, {sample_count:values.length,mean:values.reduce((a,b)=>a+b,0)/values.length,p50:sorted[Math.ceil(.5*values.length)-1],p95:sorted[Math.ceil(.95*values.length)-1],unit:'seconds',percentile_method:'nearest rank',raw_values:values}];
}))]));
writeFileSync(join(directory, 'stage-summary.json'), JSON.stringify({status:'measured',note:'Companion to measurement.json; separate response types and pipeline stages. Planned top-level and query values overlap and must not be added together. Ingestion includes first PDF lazy model startup; query stages exclude process startup. Queue waiting is included in stage time where performed inside the recorded call.',groups:result},null,2)+'\n',{flag:'wx'});
console.log('Stage sample counts, means and percentiles retained.');
