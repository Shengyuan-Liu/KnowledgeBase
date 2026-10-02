import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const directory = dirname(fileURLToPath(import.meta.url));
const root = resolve(directory, '../../..');
const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
const revision = 'c87bf76';
assert.equal(git('diff', revision, '--', 'frontend/src', 'frontend/tsconfig.json'), '');
const paths = git('ls-tree', '-r', '--name-only', revision, '--', 'frontend/src').trim().split('\n')
  .filter(p => /\.tsx?$/.test(p) && !/\.test\.|\/test\//.test(p));
const modules = new Set(paths), edges = [], trace = [];
const output = execFileSync(join(root, 'frontend/node_modules/.bin/tsc'), ['--traceResolution', '--listFilesOnly'], { cwd: join(root, 'frontend'), encoding: 'utf8', maxBuffer: 50 * 1024 * 1024 });
let current;
for (const line of output.split('\n')) {
  const start = line.match(/^======== Resolving module '(.+)' from '(.+)'. ========$/);
  if (start) current = { specifier: start[1], source: relative(root, start[2]) };
  if (current && modules.has(current.source)) {
    trace.push(line);
    const resolved = line.match(/^======== Module name '.+' was successfully resolved to '([^']+)'/);
    if (resolved) {
      const target = relative(root, resolved[1]);
      if (modules.has(target)) edges.push({ ...current, target });
    }
  }
  if (/^======== Module name /.test(line)) current = undefined;
}
const graph = new Map(paths.map(p => [p, []]));
const reverse = new Map(paths.map(p => [p, []]));
edges.forEach(e => { graph.get(e.source).push(e.target); reverse.get(e.target).push(e.source); });
const seen = new Set(), order = [];
const visit = node => { if (seen.has(node)) return; seen.add(node); graph.get(node).forEach(visit); order.push(node); };
paths.forEach(visit); seen.clear();
const cycles = [];
for (const node of order.reverse()) {
  if (seen.has(node)) continue;
  const group = [], collect = item => { if (seen.has(item)) return; seen.add(item); group.push(item); reverse.get(item).forEach(collect); };
  collect(node);
  if (group.length > 1 || graph.get(node).includes(node)) cycles.push(group.sort());
}
const layer = path => path.endsWith('/types.ts') ? 'types' : path.split('/').length > 3 ? path.split('/')[2] : 'entry';
const forbidden = { types:['api','hooks','components','entry'], api:['hooks','components','entry'], hooks:['components','entry'], components:['entry'] };
const violations = edges.filter(e => forbidden[layer(e.source)]?.includes(layer(e.target)));
assert.ok(edges.some(e=>e.source.endsWith('EvidencePanel.tsx') && e.target.endsWith('PdfViewer.tsx')), 'Dynamic PDF import must be captured');
assert.ok(edges.some(e=>e.source.endsWith('ChatPanel.tsx') && e.target.endsWith('useChat.ts')), 'Type-only hook import must be captured');
writeFileSync(join(directory, 'frontend-resolution.log'), trace.join('\n')+'\n', {flag:'wx'});
writeFileSync(join(directory, 'frontend-dependencies.json'), JSON.stringify({ revision:git('rev-parse',revision).trim(),module_count:paths.length,modules:paths,edges,full_cycles:cycles,forbidden_layer_edges:violations,rules:forbidden,method:'Installed TypeScript compiler module-resolution trace, including type-only and literal dynamic imports; SCC over first-party production modules.',limits:'Test files, CSS/assets and external dependencies excluded. Compiler trace is not split into runtime versus type-only edges; acyclicity is checked on their union.' },null,2)+'\n',{flag:'wx'});
console.log(paths.length, 'frontend modules;',edges.length,'internal import edges; cycles:',cycles,'; layer violations:', violations.length);
if (cycles.length || violations.length) { console.log('1 failed: frontend dependency audit.'); process.exitCode=1; }
else console.log('1 passed: frontend dependency audit.');
