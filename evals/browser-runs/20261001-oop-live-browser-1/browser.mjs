import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { appendFileSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const directory = dirname(fileURLToPath(import.meta.url));
const root = resolve(directory, '../../..');
const require = createRequire(join(root, 'frontend/package.json'));
const { chromium, expect: baseExpect } = require('@playwright/test');
const expect = baseExpect.configure({ timeout: 180000 });
const baseURL = 'http://127.0.0.1:8001';
const fixtures = [
  { name: 'cedar-hours.txt', text: 'Cedar Library visitor guide.\nCedar Library closes at 5 PM Monday through Friday.\nCedar Library closes at 7 PM on Saturday and Sunday.\nVisitors must bring their library card.\n' },
  { name: 'cedar-access.md', text: '# Cedar Library Access\n\n## Quiet room reservations\n\nReserve the quiet room at least 24 hours in advance.\nThe quiet room is on the second floor.\n' },
  ...['assignment.pdf', 'laboratory-register.pdf'].map(name => ({ name, path: join(root, 'evals/materials/pdf-v2-closeout-dependency', name) })),
];
const questions = [
  { id: 'weekday', question: 'According to cedar-hours.txt, when does Cedar Library close on weekdays? Answer briefly with a citation.', gold: [{ file: 'cedar-hours.txt', quote: 'Cedar Library closes at 5 PM Monday through Friday.', expected: '5 PM' }] },
  { id: 'followup', question: 'What about on Saturday?', gold: [{ file: 'cedar-hours.txt', quote: 'Cedar Library closes at 7 PM on Saturday and Sunday.', expected: '7 PM' }] },
  { id: 'markdown', question: 'According to cedar-access.md, how far in advance must I reserve the quiet room, and where is it?', gold: [{ file: 'cedar-access.md', quote: 'Reserve the quiet room at least 24 hours in advance.', expected: '24 hours' }, { file: 'cedar-access.md', quote: 'The quiet room is on the second floor.', expected: 'second floor' }] },
  { id: 'pdf-planned', question: 'Which laboratory was assigned to Project Juniper in "assignment.pdf", and what calibration interval does "laboratory-register.pdf" specify for that laboratory?', planned: true, gold: [{ file: 'assignment.pdf', quote: 'Project Juniper was assigned to Quenwick Laboratory.', expected: 'Quenwick Laboratory' }, { file: 'laboratory-register.pdf', quote: 'Quenwick Laboratory: calibration interval is 17 days.', expected: '17 calendar days' }] },
  { id: 'unanswerable', question: 'Using only my uploaded documents, what is the exact secret PIN of my personal Cedar Library account?', gold: [], expected_abstention: true },
];
writeFileSync(join(directory, 'protocol.json'), JSON.stringify({
  frozen_at: new Date().toISOString(), questions,
  fixtures: fixtures.map(f => ({ ...f, sha256: createHash('sha256').update(f.text ?? readFileSync(f.path)).digest('hex') })),
  reviewer: 'Codex, automated fixture checks plus answer/evidence and visual inspection; not independent human review',
  quality_protocol: 'Assess each stated expected fact against exact supplied excerpts. Record unsupported or missing claims. Unanswerable PIN must abstain. Citation membership alone is insufficient.',
  retrieval_protocol: 'Document-level relevance at K=5 for the four answerable questions; one relevant label per unique gold filename. Candidate, reranking and supplied-evidence stages are separate. Fact coverage uses the exact gold quotes, normalizing whitespace only.',
  timing_protocol: 'Browser fetch invocation to first nonempty answer delta and complete SSE event; clone-stream observer, sequential requests, no test reruns. UI readiness measured separately. Includes provider queue/network; startup/model load and ingestion are separate.',
}, null, 2) + '\n', { flag: 'wx' });

const steps = [], answers = [], errors = [], network = [], streams = [];
let browser, page, status = 'running', failure;
const started = Date.now();
const record = (name, details = {}) => {
  const step = { name, at: new Date().toISOString(), details };
  steps.push(step);
  appendFileSync(join(directory, 'steps.jsonl'), JSON.stringify(step) + '\n');
  console.log(name);
};
const save = (name, data) => writeFileSync(join(directory, name), JSON.stringify(data, null, 2) + '\n', { flag: 'wx' });

try {
  browser = await chromium.launch({ channel: 'chrome', headless: false });
  const context = await browser.newContext({ baseURL, viewport: { width: 1440, height: 1000 } });
  await context.exposeBinding('__recordStream', (_, entry) => {
    streams.push(entry);
    appendFileSync(join(directory, 'streams.jsonl'), JSON.stringify(entry) + '\n');
  });
  await context.addInitScript(() => {
    const originalFetch = window.fetch.bind(window);
    window.fetch = async (...args) => {
      const url = String(args[0]);
      if (!url.endsWith('/api/chat/stream')) return originalFetch(...args);
      const start = performance.now();
      const input = JSON.parse(args[1].body);
      const entry = { request: input, started_at: new Date().toISOString(), events: [] };
      try {
        const response = await originalFetch(...args);
        entry.status = response.status;
        const reader = response.clone().body.getReader();
        (async () => {
          const decoder = new TextDecoder();
          let buffer = '';
          try {
            while (true) {
              const part = await reader.read();
              buffer += decoder.decode(part.value, { stream: !part.done });
              let separator;
              while ((separator = /\r?\n\r?\n/.exec(buffer))) {
                const frame = buffer.slice(0, separator.index);
                buffer = buffer.slice(separator.index + separator[0].length);
                const lines = frame.split(/\r?\n/);
                const event = lines.find(line => line.startsWith('event:'))?.slice(6).trim();
                const data = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
                if (data) entry.events.push({ event, elapsed_ms: performance.now() - start, data: JSON.parse(data) });
                if (event === 'complete' || event === 'error') return;
              }
              if (part.done) break;
            }
          } catch (error) { entry.read_error = String(error); }
          finally {
            entry.finished_ms = performance.now() - start;
            await window.__recordStream(entry);
            reader.cancel().catch(() => {});
          }
        })();
        return response;
      } catch (error) {
        entry.fetch_error = String(error);
        await window.__recordStream(entry);
        throw error;
      }
    };
  });
  page = await context.newPage();
  page.on('pageerror', e => errors.push({ type: 'pageerror', message: e.message }));
  page.on('console', msg => { if (msg.type() === 'error') errors.push({ type: 'console', message: msg.text() }); });
  page.on('requestfailed', req => network.push({ url: req.url(), error: req.failure()?.errorText }));
  const initial = await context.request.get('/api/files');
  assert.equal(initial.status(), 200);
  assert.deepEqual(await initial.json(), []);
  await page.goto('/');
  record('real-chrome-opened', { version: browser.version() });
  for (const f of fixtures) {
    const begin = Date.now();
    await page.getByLabel('Choose TXT, Markdown or PDF file').setInputFiles(f.path ?? {
      name: f.name, mimeType: f.name.endsWith('.md') ? 'text/markdown' : 'text/plain', buffer: Buffer.from(f.text),
    });
    await expect(page.getByText(`${f.name} is ready.`, { exact: true })).toBeVisible();
    record('upload-ready', { file_name: f.name, ui_ready_ms: Date.now() - begin });
  }
  const files = await (await context.request.get('/api/files')).json();
  save('files-before.json', files);
  assert.equal(files.length, fixtures.length);
  for (const file of files.filter(f => f.type === 'pdf')) assert.equal(file.page_count, 1);
  await page.screenshot({ path: join(directory, 'library.png'), fullPage: true });

  const history = async () => {
    const id = await page.evaluate(() => localStorage.getItem('knowledgebase.conversationId'));
    assert.ok(id);
    const response = await context.request.get(`/api/conversations/${id}`);
    assert.equal(response.status(), 200);
    return response.json();
  };
  const composer = page.getByRole('textbox', { name: 'Ask about your documents' });
  const ask = async (q, count) => {
    await page.getByRole('checkbox', { name: 'Plan complex questions' }).setChecked(!!q.planned);
    const begin = Date.now();
    await composer.fill(q.question);
    await composer.press('Enter');
    await expect(page.getByText('Completed', { exact: true })).toHaveCount(count);
    const ui_complete_ms = Date.now() - begin;
    assert.equal(await composer.inputValue(), '');
    const saved = await history();
    const answer = saved.messages.at(-1);
    answers.push({ ...q, ui_complete_ms, answer, conversation_id: saved.conversation_id });
    save(`answer-${q.id}.json`, answers.at(-1));
    record('answer-completed', { id: q.id, ui_complete_ms });
    assert.deepEqual(answer.citation_check.invalid_source_ids, []);
    return saved;
  };
  await ask(questions[0], 1);
  await page.getByRole('button', { name: /^View source \d+: cedar-hours.txt$/ }).first().click();
  const evidence = page.getByRole('complementary', { name: 'Evidence' });
  await expect(evidence.locator('blockquote').filter({ hasText: '5 PM' }).first()).toBeVisible();
  record('text-citation-opened');
  await ask(questions[1], 2);
  await ask(questions[2], 3);
  const beforeRefresh = await history();
  await page.reload();
  await expect(page.getByText('Completed', { exact: true })).toHaveCount(3);
  assert.deepEqual(await history(), beforeRefresh);
  record('refresh-preserved-history');
  await page.screenshot({ path: join(directory, 'text-chat.png'), fullPage: true });

  await page.getByRole('button', { name: 'New chat', exact: true }).click();
  const pdfHistory = await ask(questions[3], 1);
  await page.getByRole('button', { name: 'View evidence', exact: true }).click();
  const pdfLink = evidence.getByRole('link', { name: /Open page/ }).first();
  await expect(pdfLink).toBeVisible();
  const href = await pdfLink.getAttribute('href');
  assert.match(href, /original\?revision=.*#page=1/);
  const original = await context.request.get(href.split('#')[0]);
  assert.equal(original.status(), 200);
  assert.match(original.headers()['content-type'], /application\/pdf/);
  await pdfLink.click();
  const viewer = page.getByRole('dialog').filter({ has: page.getByRole('button', { name: 'Close PDF' }) });
  await expect(viewer.getByText('Page 1 of 1', { exact: true })).toBeVisible();
  await expect(viewer.locator('canvas[data-rendered=true]')).toBeVisible();
  await page.screenshot({ path: join(directory, 'pdf-viewer.png'), fullPage: true });
  await viewer.getByRole('button', { name: 'Close PDF' }).click();
  await evidence.getByText('Search plan', { exact: true }).click();
  await expect(evidence.getByRole('region', { name: 'Evidence assessment' })).toBeVisible();
  await page.screenshot({ path: join(directory, 'planned-evidence.png'), fullPage: true });
  record('planned-pdf-citation-rendered', { href });
  await page.reload();
  await expect(page.getByText('Completed', { exact: true })).toHaveCount(1);
  assert.deepEqual(await history(), pdfHistory);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'View evidence', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Evidence', exact: true })).toBeVisible();
  await page.screenshot({ path: join(directory, 'mobile-evidence.png'), fullPage: true });
  await page.getByRole('button', { name: 'Close evidence', exact: true }).click();
  record('mobile-evidence-opened');
  await page.setViewportSize({ width: 1440, height: 1000 });

  await page.getByRole('checkbox', { name: 'Plan complex questions' }).uncheck();
  const cancelled = 'According to cedar-hours.txt, write forty numbered visitor reminders using only its hours and library-card requirement. Cite the document in each item.';
  await composer.fill(cancelled);
  await composer.press('Enter');
  await expect(page.getByText('Answering…', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Stop', exact: true }).click();
  await expect(page.getByText('Interrupted', { exact: true })).toBeVisible();
  await page.waitForTimeout(1500);
  assert.deepEqual(await history(), pdfHistory);
  await page.screenshot({ path: join(directory, 'cancelled.png'), fullPage: true });
  record('cancelled-turn-not-persisted');
  await page.reload();
  await expect(page.getByText('Completed', { exact: true })).toHaveCount(1);
  await expect(page.getByText('Interrupted', { exact: true })).toHaveCount(0);

  await page.getByRole('button', { name: 'assignment.pdf Ready', exact: true }).click();
  await page.getByRole('button', { name: 'Delete', exact: true }).click();
  await page.getByRole('button', { name: 'Delete file', exact: true }).click();
  await expect(page.getByText('File and indexed content deleted.', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText('Completed', { exact: true })).toHaveCount(1);
  await page.getByRole('button', { name: 'View evidence', exact: true }).click();
  await expect(evidence.getByText(/original unavailable/).first()).toBeVisible();
  const afterDeletion = await history();
  const removedSources = afterDeletion.messages.at(-1).sources.filter(s => s.file_name === 'assignment.pdf');
  assert.ok(removedSources.length > 0 && removedSources.every(s => s.file_deleted));
  for (const source of removedSources) assert.equal(source.text, pdfHistory.messages.at(-1).sources.find(s => s.chunk_id === source.chunk_id).text);
  const removed = files.find(f => f.file_name === 'assignment.pdf');
  assert.equal((await context.request.get(`/api/files/${removed.file_id}/original`)).status(), 404);
  save('history-after-deletion.json', afterDeletion);
  save('files-after-deletion.json', await (await context.request.get('/api/files')).json());
  await page.screenshot({ path: join(directory, 'historical-pdf.png'), fullPage: true });
  record('deleted-pdf-keeps-historical-excerpt');

  await page.getByRole('button', { name: 'New chat', exact: true }).click();
  await ask(questions[4], 1);
  await page.screenshot({ path: join(directory, 'abstention.png'), fullPage: true });
  assert.match(answers[0].answer.content, /5\s*(?:PM|p\.?m)/i);
  assert.match(answers[1].answer.content, /7\s*(?:PM|p\.?m)/i);
  assert.match(answers[2].answer.content, /24/);
  assert.match(answers[2].answer.content, /second floor/i);
  assert.match(answers[3].answer.content, /Quenwick/);
  assert.match(answers[3].answer.content, /17/);
  assert.match(answers[4].answer.content, /not|cannot|can't|no |insufficient/i);
  assert.deepEqual(errors.filter(e => e.type === 'pageerror'), []);
  record('semantic-smoke-checks-passed', { answers: answers.length });
  status = 'passed';
} catch (error) {
  status = 'failed'; failure = error.stack ?? String(error);
  record('failed', { error: failure });
  if (page) await page.screenshot({ path: join(directory, 'failure.png'), fullPage: true }).catch(() => {});
} finally {
  save('acceptance.json', { status, started_at: new Date(started).toISOString(), duration_ms: Date.now() - started, steps, answers, errors, network, stream_count: streams.length, failure });
  await browser?.close();
  console.log(status === 'passed' ? '1 passed: real Chrome workflow.' : '1 failed: real Chrome workflow.');
}
if (status !== 'passed') process.exitCode = 1;
