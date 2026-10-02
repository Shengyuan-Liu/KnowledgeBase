import { appendFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const directory = dirname(fileURLToPath(import.meta.url));
const root = resolve(directory, '../../..');
const require = createRequire(join(root, 'frontend/package.json'));
const { chromium, expect: originalExpect } = require('@playwright/test');
const expect = originalExpect.configure({ timeout: 90000 });
const cases = [
  { id: 'generic-source-answerable', question: 'Using only my uploaded documents, when does Cedar Library close on weekdays?', expected: '5 PM with a supported citation', gold: [{ file: 'cedar-hours.txt', quote: 'Cedar Library closes at 5 PM Monday through Friday.' }] },
  { id: 'explicit-source-unanswerable', question: 'According to cedar-hours.txt, what is the exact secret PIN of my personal Cedar Library account?', expected: 'Explain that the document does not provide the PIN; do not invent one.', gold: [] },
];
writeFileSync(join(directory, 'scope-probe-2-protocol.json'), JSON.stringify({ frozen_at: new Date().toISOString(), purpose: 'Follow up observed source-scope misinterpretation; keep original workflow and scores unchanged.', cases }, null, 2) + '\n', { flag: 'wx' });
const rows = [], streams = [], pending = [];
const browser = await chromium.launch({ channel: 'chrome', headless: false });
let error;
try {
  const context = await browser.newContext({ baseURL: 'http://127.0.0.1:8001', viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  page.on('response', response => {
    if (!response.url().endsWith('/api/chat/stream')) return;
    pending.push(response.text().then(body => {
      const item = { request: response.request().postDataJSON(), body };
      streams.push(item);
      appendFileSync(join(directory, 'scope-probe-2-streams.jsonl'), JSON.stringify(item) + '\n');
    }).catch(error => {
      appendFileSync(join(directory, "scope-probe-2-stream-errors.jsonl"), JSON.stringify({question: response.request().postDataJSON().question, error: String(error)}) + "\n");
    }));
  });
  await page.goto('/');
  for (const item of cases) {
    await page.getByRole('button', { name: 'New chat', exact: true }).click();
    const composer = page.getByRole('textbox', { name: 'Ask about your documents' });
    const started = Date.now();
    await composer.fill(item.question);
    await composer.press('Enter');
    await expect(page.getByText('Completed', { exact: true })).toHaveCount(1);
    const elapsed_ms = Date.now() - started;
    const id = await page.evaluate(() => localStorage.getItem('knowledgebase.conversationId'));
    const saved = await (await context.request.get(`/api/conversations/${id}`)).json();
    const answer = saved.messages.at(-1);
    const passed = item.id === 'generic-source-answerable'
      ? /5\s*(?:PM|p\.?m)/i.test(answer.content) && answer.sources.length > 0
      : /not|cannot|can't|no |insufficient/i.test(answer.content) && answer.retrieval.document_scope?.status === 'resolved';
    rows.push({ ...item, answer, elapsed_ms, passed });
    await page.screenshot({ path: join(directory, `${item.id}-2.png`), fullPage: true });
  }
  await Promise.all(pending);
} catch (caught) { error = caught.stack ?? String(caught); }
finally {
  writeFileSync(join(directory, 'scope-probe-2.json'), JSON.stringify({ rows, error, completed_streams: streams.length, first_answer_delta_latency: { status: 'unavailable', reason: 'Supplemental probe retained the complete SSE body but did not instrument per-event arrival times.' } }, null, 2) + '\n', { flag: 'wx' });
  await browser.close();
}
const passed = rows.filter(row => row.passed).length;
const failed = rows.filter(row => !row.passed).length + Number(!!error);
console.log(`${passed} passed, ${failed} failed: supplemental source-scope checks.`);
if (error) console.log(error);
if (failed) process.exitCode = 1;
