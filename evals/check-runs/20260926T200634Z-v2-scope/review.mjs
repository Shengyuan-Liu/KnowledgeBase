import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import os from 'node:os';
import { execFileSync, spawnSync } from 'node:child_process';

const started = new Date();
const start = performance.now();
const run = 'evals/check-runs/20260926T200634Z-v2-scope';
const files = [
  'AGENTS.md',
  'docs/README.md',
  ...fs.readdirSync('docs/v2').filter(name => name.endsWith('.md'))
    .sort().map(name => `docs/v2/${name}`),
  `${run}/README.md`,
];
const findings = [];
const hashes = {};
let checks = 0;
let links = 0;
const external = new Set();
function check(ok, message) {
  checks += 1;
  if (!ok) findings.push(message);
}
function anchors(text) {
  const counts = new Map();
  return new Set([...text.matchAll(/^#{1,6}\s+(.+)$/gm)].map(match => {
    const base = match[1].toLowerCase().replace(/[^\p{L}\p{N}_\-\s]/gu, '')
      .replace(/\s/g, '-');
    const count = counts.get(base) ?? 0;
    counts.set(base, count + 1);
    return count ? `${base}-${count}` : base;
  }));
}
for (const file of files) {
  const text = fs.readFileSync(file, 'utf8');
  hashes[file] = crypto.createHash('sha256').update(text).digest('hex');
  check(!/[\u3400-\u9fff]/u.test(text), `${file}: non-English CJK text`);
  check(text.endsWith('\n'), `${file}: missing final newline`);
  let fence = null;
  let columns = null;
  const lines = text.split('\n');
  for (const [index, line] of lines.entries()) {
    const marker = line.match(/^(`{3,}|~{3,})/);
    if (marker) {
      if (fence === null) fence = marker[1];
      else if (marker[1][0] === fence[0] && marker[1].length >= fence.length) fence = null;
      columns = null;
      continue;
    }
    if (fence !== null) continue;
    if (/^#{1,6} /.test(line)) {
      check(index === 0 || lines[index - 1] === '', `${file}:${index + 1}: heading needs preceding blank line`);
      check(lines[index + 1] === '', `${file}:${index + 1}: heading needs following blank line`);
    }
    if (line.startsWith('|')) {
      const count = line.split(/(?<!\\)\|/).length;
      if (columns === null) columns = count;
      check(count === columns, `${file}:${index + 1}: inconsistent table columns`);
    } else columns = null;
    for (const match of line.matchAll(/\[[^\]]*\]\(([^)]+)\)/g)) {
      const target = match[1];
      if (/^https?:/.test(target)) { external.add(target); continue; }
      if (/^[a-z]+:/i.test(target)) continue;
      links += 1;
      const [relative, fragment] = target.split('#');
      const destination = relative ? path.resolve(path.dirname(file), decodeURIComponent(relative)) : path.resolve(file);
      const exists = fs.existsSync(destination);
      check(exists, `${file}:${index + 1}: missing link ${target}`);
      if (exists && fragment && destination.endsWith('.md')) {
        check(anchors(fs.readFileSync(destination, 'utf8')).has(decodeURIComponent(fragment)),
          `${file}:${index + 1}: missing heading ${target}`);
      }
    }
  }
  check(fence === null, `${file}: unclosed fence`);
}
const whitespace = spawnSync('git', ['diff', '--check'], { encoding: 'utf8' });
check(whitespace.status === 0, `git diff --check: ${whitespace.stdout}${whitespace.stderr}`);
// New files are not included by an unstaged Git diff; inspect them explicitly.
for (const file of [...files, `${run}/review.mjs`]) {
  const text = fs.readFileSync(file, 'utf8');
  check(!/[ \t]+$/m.test(text), `${file}: trailing whitespace`);
  check(!text.endsWith('\n\n'), `${file}: extra final blank line`);
}
const policy = fs.readFileSync('evals/measurement-policy.md', 'utf8');
const table = policy.split('## Required metric inventory')[1].split('Evaluate retrieval')[0];
const names = [...table.matchAll(/^\| ([^|]+?) \|/gm)]
  .map(match => match[1].trim()).filter(name => name !== 'Metric' && !name.startsWith('---'));
const metrics = Object.fromEntries(names.map(name => [name, {
  status: 'not_applicable', value: null, unit: null, sample_count: null,
  population: 'Documentation-only content, link, and format review',
  method: 'Applicability review against the measurement policy', aggregation: null,
  reason: 'No runtime retrieval, generation, provider, ingestion, or load behavior exercised.',
  artifact: 'README.md',
}]));
let attempt = 1;
while (fs.existsSync(`${run}/review-${attempt}.json`) || fs.existsSync(`${run}/review-${attempt}.log`)) attempt += 1;
const record = {
  purpose: 'v2 branch and scope documentation verification',
  started_at: started.toISOString(), completed_at: new Date().toISOString(),
  duration_seconds: (performance.now() - start) / 1000,
  command: `node ${run}/review.mjs`,
  base_commit: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
  branch: execFileSync('git', ['branch', '--show-current'], { encoding: 'utf8' }).trim(),
  change_identity: 'Uncommitted documentation identified by SHA-256 hashes below',
  file_sha256: hashes,
  verifier_sha256: crypto.createHash('sha256').update(fs.readFileSync(`${run}/review.mjs`)).digest('hex'),
  device: { platform: os.platform(), release: os.release(), architecture: os.arch() },
  concurrency: 1, corpus: 'not_applicable: no corpus evaluated',
  model: 'not_applicable: no provider call', settings: 'documentation checks only',
  warmup_cache: 'not_applicable', timeout_retries: 'no automatic retries',
  reviewer: 'Codex; model-assisted content review recorded in README.md',
  documentation_files: files.length, local_links: links,
  external_links: [...external].sort(),
  external_review: 'External references unchanged; not re-fetched for this scope update',
  counts: { checks, passed: checks - findings.length, failed: findings.length, skipped: 0 },
  failures: findings, git_diff_check: { exit_code: whitespace.status, stdout: whitespace.stdout, stderr: whitespace.stderr },
  metrics,
};
fs.writeFileSync(`${run}/review-${attempt}.json`, `${JSON.stringify(record, null, 2)}\n`, { flag: 'wx' });
const log = `${files.length} documents; ${links} local links; ${checks} checks; ${findings.length} failures.\n${findings.join('\n')}${findings.length ? '\n' : ''}`;
fs.writeFileSync(`${run}/review-${attempt}.log`, log, { flag: 'wx' });
process.stdout.write(log);
process.exitCode = findings.length ? 1 : 0;
