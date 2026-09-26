import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { basename, join, resolve } from "node:path";
import { expect, test } from "@playwright/test";
import type { SavedConversation } from "../src/types";

const fixtures = [
  { name: "general-guide.txt", text: "Title: General Lab Guide\n\nThe lab opens at 9 AM and closes at 6 PM on weekdays.\nOn weekends, the lab opens at 10 AM and closes at 2 PM.\n" },
  { name: "access-guide.md", text: "# Lab Access Guide\n\n## Weekend reservations\n\nWeekend visits require a confirmed reservation. Submit a reservation request at least 24 hours in advance.\n" },
];
const questions = [
  "According to the general guide, when does the lab open and close on weekdays?",
  "What about on weekends?",
  "According to the general guide and access guide, which document explicitly requires a reservation for weekend visits?",
];

test("final default v1 workflow with real providers", async ({ page, request }) => {
  const directory = process.env.LIVE_EVIDENCE_DIR!;
  const dataDir = resolve("../data/live-browser", basename(directory));
  await mkdir(directory, { recursive: true });
  const answers: {question: string; ui_complete_ms: number; saved: SavedConversation}[] = [];
  const steps: {name: string; at: string; details?: unknown}[] = [];
  const browserErrors: string[] = [];
  const responses: Promise<void>[] = [];
  const transport: {question: string; body?: string; error?: string}[] = [];
  const report = {started_at: new Date().toISOString(), status: "running", fixtures: fixtures.map(f => ({...f,
    sha256: createHash("sha256").update(f.text).digest("hex")})), questions, answers, steps, browserErrors, transport};
  const save = () => writeFile(join(directory, "acceptance.json"), JSON.stringify(report, null, 2) + "\n");
  const record = async (name: string, details?: unknown) => { steps.push({name, at: new Date().toISOString(), details}); await save(); };
  page.on("pageerror", e => browserErrors.push(e.message));
  page.on("response", response => {
    if (!response.url().endsWith("/api/chat/stream")) return;
    const entry = {question: response.request().postDataJSON().question} as typeof transport[number];
    transport.push(entry);
    responses.push(response.text().then(body => {entry.body = body;}).catch(() => {entry.error = "Response body unavailable after browser cancellation.";}));
  });
  const history = async (): Promise<SavedConversation> => {
    const id = await page.evaluate(() => localStorage.getItem("knowledgebase.conversationId"));
    expect(id).toBeTruthy();
    const result = await request.get(`/api/conversations/${id}`);
    expect(result.ok()).toBe(true);
    return result.json();
  };
  const snapshot = () => JSON.parse(execFileSync("../.venv/bin/python", ["-c", `
import json, sqlite3, sys
from pathlib import Path
root = Path(sys.argv[1])
with sqlite3.connect('file:' + str(root / 'knowledgebase.db') + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    data = {table: [dict(row) for row in db.execute('SELECT * FROM ' + table)] for table in
        ['files','document_sources','document_indexes','parent_chunks','chunks','chunk_structures','child_parents']}
    print(json.dumps({'tables': data, 'index_bytes': sum(p.stat().st_size for p in root.rglob('*') if p.is_file())}))
`, dataDir], {encoding: "utf8"}));
  await save();
  try {
    expect(await (await request.get("/api/files")).json()).toEqual([]);
    await page.goto("/");
    for (const fixture of fixtures) {
      const start = Date.now();
      await page.getByLabel("Choose TXT or Markdown file").setInputFiles({name: fixture.name,
        mimeType: fixture.name.endsWith(".md") ? "text/markdown" : "text/plain", buffer: Buffer.from(fixture.text)});
      await expect(page.getByText(`${fixture.name} is ready.`)).toBeVisible();
      await record("upload-ready", {file_name: fixture.name, elapsed_ms: Date.now() - start});
    }
    const stored = snapshot();
    await writeFile(join(directory, "storage-before-deletion.json"), JSON.stringify(stored, null, 2) + "\n");
    expect(stored.tables.files).toHaveLength(2);
    for (const item of stored.tables.document_indexes) expect(JSON.parse(item.details).strategy).toBe("parent_child");
    const composer = page.getByRole("textbox", {name: "Ask about your documents"});
    for (const [i, question] of questions.entries()) {
      const start = Date.now();
      await composer.fill(question);
      await composer.press("Enter");
      await expect(page.getByText("Completed", {exact: true})).toHaveCount(i + 1);
      const ui_complete_ms = Date.now() - start;
      const saved = await history();
      answers.push({question, ui_complete_ms, saved});
      await save();
      const answer = saved.messages.at(-1)!;
      expect(answer.citation_check?.valid_source_ids.length).toBeGreaterThan(0);
      expect(answer.citation_check?.invalid_source_ids).toEqual([]);
      expect(answer.retrieval?.options?.strategy).toBe("hybrid");
      expect(answer.retrieval?.options?.rerank_enabled).toBe(false);
      expect(answer.retrieval?.document_scope?.status).toBe("resolved");
      expect(answer.retrieval!.evidence_tokens).toBeLessThanOrEqual(4096);
      for (const source of answer.sources!) {
        const text = fixtures.find(f => f.name === source.file_name)!.text;
        expect(source.text).toBe(text.slice(source.start_offset!, source.end_offset!));
        expect(source.start_line).toBe(text.slice(0, source.start_offset!).split("\n").length);
      }
      if (i < 2) expect([...new Set(answer.sources!.map(s => s.file_name))]).toEqual(["general-guide.txt"]);
      else expect(new Set(answer.sources!.map(s => s.file_name))).toEqual(new Set(fixtures.map(f => f.name)));
      await record("completed-answer-and-scope", {question});
    }
    expect(answers[0].saved.messages.at(-1)!.content).toMatch(/9\s*(?:AM|a\.m\.)/i);
    expect(answers[0].saved.messages.at(-1)!.content).toMatch(/6\s*(?:PM|p\.m\.)/i);
    expect(answers[1].saved.messages.at(-1)!.content).toMatch(/10\s*(?:AM|a\.m\.)/i);
    expect(answers[1].saved.messages.at(-1)!.content).toMatch(/2\s*(?:PM|p\.m\.)/i);
    expect(answers[2].saved.messages.at(-1)!.content).toMatch(/reserv/i);
    await page.reload();
    await expect(page.getByText("Completed", {exact: true})).toHaveCount(3);
    expect(await history()).toEqual(answers[2].saved);
    await page.getByText("Debug details", {exact: true}).last().click();
    await expect(page.getByLabel("Document scope").last()).toContainText("general-guide.txt");
    await expect(page.getByLabel("Document scope").last()).toContainText("access-guide.md");
    await expect(page.getByRole("region", {name: "Candidate ranking table"}).last()).toBeVisible();
    await page.getByRole("button", {name: /^View source \d+: access-guide.md$/}).last().click();
    const evidence = page.getByRole("complementary", {name: "Evidence"});
    await expect(evidence.getByText(/Lines \d+–\d+/).first()).toBeVisible();
    await expect(evidence.locator("blockquote").first()).toContainText("confirmed reservation");
    await page.screenshot({path: join(directory, "comparison-evidence.png"), fullPage: true});
    await record("refresh-and-citation-inspection");

    const cancellationQuestion = "According to the general guide, list forty separately numbered visitor reminders based only on its opening and closing times. Cite each item.";
    await composer.fill(cancellationQuestion);
    await composer.press("Enter");
    await expect(page.getByText("Answering…", {exact: true})).toBeVisible();
    await page.getByRole("button", {name: "Stop", exact: true}).click();
    await expect(page.getByText("Interrupted", {exact: true})).toBeVisible();
    await page.waitForTimeout(1500);
    expect(await history()).toEqual(answers[2].saved);
    await record("cancelled-turn-not-persisted", {question: cancellationQuestion});
    await page.reload();
    await expect(page.getByText("Completed", {exact: true})).toHaveCount(3);
    await expect(page.getByText("Interrupted", {exact: true})).toHaveCount(0);

    for (const fixture of fixtures) {
      await page.getByRole("button", {name: `${fixture.name} Ready`, exact: true}).click();
      await page.getByRole("button", {name: "Delete", exact: true}).click();
      await page.getByRole("button", {name: "Delete file", exact: true}).click();
      await expect(page.getByText("File and indexed content deleted.")).toBeVisible();
    }
    await page.reload();
    await expect(page.getByText("Completed", {exact: true})).toHaveCount(3);
    await page.getByRole("button", {name: /^View source \d+: access-guide.md$/}).last().click();
    await expect(evidence.getByText("Source deleted · Historical excerpt").first()).toBeVisible();
    const deleted = await history();
    for (const message of deleted.messages.filter(m => m.role === "assistant")) {
      const before = answers[2].saved.messages.find(m => m.message_id === message.message_id)!;
      expect(message.retrieval).toEqual(before.retrieval);
      expect(message.sources).toEqual(before.sources!.map(s => ({...s, file_deleted: true})));
    }
    const remaining = snapshot();
    for (const rows of Object.values(remaining.tables)) expect(rows).toEqual([]);
    expect(await (await request.get("/api/files")).json()).toEqual([]);
    await expect(composer).toBeDisabled();
    await writeFile(join(directory, "conversation-after-deletion.json"), JSON.stringify(deleted, null, 2) + "\n");
    await writeFile(join(directory, "storage-after-deletion.json"), JSON.stringify(remaining, null, 2) + "\n");
    await page.screenshot({path: join(directory, "deleted-evidence.png"), fullPage: true});
    await record("deletion-and-historical-evidence");
    expect(browserErrors).toEqual([]);
    report.status = "passed";
  } catch (error) {
    report.status = "failed";
    await page.screenshot({path: join(directory, "failure.png"), fullPage: true});
    await record("failure", {message: error instanceof Error ? error.message : String(error)});
    throw error;
  } finally {
    await Promise.all(responses);
    await record("finished");
  }
});
