import { execFileSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, posix, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const directory = dirname(fileURLToPath(import.meta.url));
const root = resolve(directory, '../../..');
const require = createRequire(join(root, 'frontend/package.json'));
const ts = require('typescript');
const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
const revision = 'c87bf76';
const paths = git('ls-tree', '-r', '--name-only', revision, '--', 'frontend/src').trim().split('\n')
  .filter(p => /\.tsx?$/.test(p) && !/\.test\.|\/test\//.test(p));
const modules = new Set(paths), edges = [], unresolved = [];
for (const path of paths) {
  const file = ts.createSourceFile(path, git('show', `${revision}:${path}`), ts.ScriptTarget.Latest, true);
  const add = (specifier, node, typeOnly, dynamic) => {
    if (!specifier.startsWith('.')) return;
    const base = posix.normalize(posix.join(posix.dirname(path), specifier));
    const target = [base, `${base}.ts`, `${base}.tsx`, `${base}/index.ts`, `${base}/index.tsx`].find(p => modules.has(p));
    const line = file.getLineAndCharacterOfPosition(node.getStart(file)).line + 1;
    if (target) edges.push({ source: path, target, line, type_only: typeOnly, dynamic });
    else if (!/\.css(?:\?.*)?$/.test(specifier)) unresolved.push({ source: path, specifier, line });
  };
  const visit = node => {
    if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier && ts.isStringLiteral(node.moduleSpecifier)) {
      const clause = node.importClause;
      const allType = clause?.isTypeOnly || (!clause?.name && clause?.namedBindings && ts.isNamedImports(clause.namedBindings) && clause.namedBindings.elements.every(e => e.isTypeOnly));
      add(node.moduleSpecifier.text, node, !!(node.isTypeOnly || allType), false);
    }
    if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
      if (node.arguments.length && ts.isStringLiteral(node.arguments[0])) add(node.arguments[0].text, node, false, true);
      else unresolved.push({ source: path, reason: 'nonliteral dynamic import' });
    }
    ts.forEachChild(node, visit);
  };
  visit(file);
}
function components(selected) {
  const graph = new Map(paths.map(p => [p, []]));
  selected.forEach(e => graph.get(e.source).push(e.target));
  const seen = new Set(), order = [], reverse = new Map(paths.map(p => [p, []]));
  selected.forEach(e => reverse.get(e.target).push(e.source));
  const visit = node => { if (seen.has(node)) return; seen.add(node); graph.get(node).forEach(visit); order.push(node); };
  paths.forEach(visit); seen.clear();
  const cycles = [];
  for (const node of order.reverse()) {
    if (seen.has(node)) continue;
    const group = [], collect = item => { if (seen.has(item)) return; seen.add(item); group.push(item); reverse.get(item).forEach(collect); };
    collect(node);
    if (group.length > 1 || graph.get(node).includes(node)) cycles.push(group.sort());
  }
  return cycles;
}
const layer = path => path.endsWith('/types.ts') ? 'types' : path.split('/').length > 3 ? path.split('/')[2] : 'entry';
const forbidden = { types:['api','hooks','components','entry'], api:['hooks','components','entry'], hooks:['components','entry'], components:['entry'] };
const violations = edges.filter(e => forbidden[layer(e.source)]?.includes(layer(e.target)));
const full = components(edges), runtime = components(edges.filter(e=>!e.type_only));
writeFileSync(join(directory, 'frontend-dependencies.json'), JSON.stringify({ revision:git('rev-parse',revision).trim(),module_count:paths.length,modules:paths,edges,unresolved,full_cycles:full,runtime_cycles:runtime,forbidden_layer_edges:violations,rules:forbidden,limits:'First-party production TS/TSX imports, re-exports and literal dynamic imports, including type-only edges. Test files, CSS/assets and external dependencies are excluded.' },null,2)+'\n',{flag:'wx'});
console.log(paths.length, 'frontend modules; full cycles:', full, '; runtime cycles:', runtime, '; layer violations:', violations.length, '; unresolved imports:', unresolved.length);
if (full.length || violations.length || unresolved.length) { console.log('1 failed: frontend dependency audit.'); process.exitCode=1; }
else console.log('1 passed: frontend dependency audit.');
