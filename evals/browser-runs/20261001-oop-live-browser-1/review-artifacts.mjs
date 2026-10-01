import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const directory = dirname(fileURLToPath(import.meta.url));
const root = resolve(directory, '../../..');
for (const name of ['README.md', '../../../docs/v2/oop-refactoring.md']) {
  const path = resolve(directory, name), source = readFileSync(path, 'utf8');
  assert.equal(/[\u3400-\u9fff]/.test(source), false);
  assert.equal((source.match(/^```/gm)?.length ?? 0) % 2, 0);
  for (const match of source.matchAll(/\[[^\]\n]+\]\(([^)\n]+)\)/g)) {
    if (/^[a-z]+:|^#/.test(match[1])) continue;
    assert.ok(existsSync(resolve(dirname(path), decodeURIComponent(match[1].split('#')[0]))), match[1]);
  }
}
for (const name of ['browser.mjs', 'scope-probe.mjs', 'scope-probe-2.mjs', 'finalize.mjs', 'stage-summaries.mjs']) execFileSync(process.execPath, ['--check', join(directory, name)]);
const measurements = JSON.parse(readFileSync(join(directory, 'measurement.json'), 'utf8'));
assert.equal(Object.keys(measurements.metric_inventory).length, 20);
assert.equal(measurements.status, 'completed_with_known_product_failure');
assert.equal(measurements.metric_inventory.Reliability.value.stream_attempts, 9);
assert.equal(measurements.coverage.flatMap(r => r.facts).filter(f => !f.covered).length, 1);
const review = JSON.parse(readFileSync(join(directory, 'review.json'), 'utf8'));
assert.equal(review.reviews.filter(r => r.result === 'failed').length, 2);
const log = readFileSync(join(directory, 'server.log'), 'utf8');
assert.ok(log.includes('Application shutdown complete.'));
assert.equal(/Traceback|\bERROR\b|HTTP\/1\.1" 5\d\d/.test(log), false);
execFileSync('git', ['diff', '--check'], { cwd: root });
console.log('1 passed: report links, English text, script syntax, 20-metric inventory, retained failures and clean server shutdown verified.');
