import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { basename, join, resolve } from "node:path";
import { expect, test } from "@playwright/test";
import type { SavedConversation } from "../src/types";

test("live semantic evidence survives refresh and document deletion", async ({ page, request }) => {
  const directory = process.env.LIVE_EVIDENCE_DIR!;
  const dataDir = resolve("../data/live-browser", basename(directory));
  await mkdir(directory, { recursive: true });
  const fixture = "# Training lab\n\n## Hours\n\nThe training lab opens at 9 AM on weekdays. It closes at 6 PM. Weekend visits require a reservation.\n\n## Contact\n\nFor reservation questions, email lab@example.test.\n";
  const questions = [
    "According to the training lab document, what time does the lab open and close on weekdays? Cite the document.",
    "What about visiting on weekends? Cite the document.",
  ];
  const answers: { question: string; ui_complete_ms: number; saved: SavedConversation }[] = [];
  const browserErrors: string[] = [];
  const steps: { name: string; at: string; details?: unknown }[] = [];
  const report = { started_at: new Date().toISOString(), status: "running", fixture, questions,
    fixture_sha256: createHash("sha256").update(fixture).digest("hex"), answers, steps, browserErrors };
  const save = () => writeFile(join(directory, "acceptance.json"), JSON.stringify(report, null, 2) + "\n");
  const record = async (name: string, details?: unknown) => {
    steps.push({ name, at: new Date().toISOString(), details });
    await save();
  };
  const history = async (): Promise<SavedConversation> => {
    const id = await page.evaluate(() => localStorage.getItem("knowledgebase.conversationId"));
    expect(id).toBeTruthy();
    const response = await request.get(`/api/conversations/${id}`);
    expect(response.ok()).toBe(true);
    return response.json();
  };
  const snapshot = () => JSON.parse(execFileSync("../.venv/bin/python", ["-c", `
import json, sqlite3, sys
with sqlite3.connect('file:' + sys.argv[1] + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    print(json.dumps({table: [dict(row) for row in db.execute('SELECT * FROM ' + table)]
        for table in ['files', 'document_sources', 'document_indexes', 'parent_chunks', 'chunks', 'chunk_structures']}))
`, join(dataDir, "knowledgebase.db")], { encoding: "utf8" }));
  page.on("pageerror", error => browserErrors.push(error.message));
  await save();
  try {
    expect(await (await request.get("/api/files")).json()).toEqual([]);
    await page.goto("/");
    const uploadStart = Date.now();
    await page.getByLabel("Choose TXT or Markdown file").setInputFiles({
      name: "training-lab.md", mimeType: "text/markdown", buffer: Buffer.from(fixture),
    });
    await expect(page.getByText("training-lab.md is ready.")).toBeVisible();
    await record("upload-ready", { elapsed_ms: Date.now() - uploadStart });
    const stored = snapshot();
    await writeFile(join(directory, "storage-before-deletion.json"), JSON.stringify(stored, null, 2) + "\n");
    expect(JSON.parse(stored.document_indexes[0].details).strategy).toBe("semantic");
    expect(stored.document_sources[0].text).toBe(fixture);
    expect(stored.parent_chunks.length).toBeGreaterThan(0);
    for (const chunk of stored.chunks) {
      expect(chunk.text).toBe(fixture.slice(chunk.start_offset, chunk.end_offset));
    }
    for (const question of questions) {
      const started = Date.now();
      const composer = page.getByRole("textbox", { name: "Ask about your documents" });
      await composer.fill(question);
      await composer.press("Enter");
      await expect(page.getByText("Completed", { exact: true })).toHaveCount(answers.length + 1);
      const uiComplete = Date.now() - started;
      const saved = await history();
      answers.push({ question, ui_complete_ms: uiComplete, saved });
      await save();
      const answer = saved.messages.at(-1)!;
      expect(answer.sources?.length).toBeGreaterThan(0);
      expect(answer.citation_check?.valid_source_ids.length).toBeGreaterThan(0);
      expect(answer.citation_check?.invalid_source_ids).toEqual([]);
      expect(answer.retrieval?.options?.strategy).toBe("hybrid");
      expect(answer.retrieval?.rerank?.matches.length).toBeGreaterThan(0);
      expect(answer.retrieval?.embedding_seconds).toBeGreaterThan(0);
      for (const source of answer.sources!) {
        expect(source.text).toBe(fixture.slice(source.start_offset!, source.end_offset!));
        expect(source.start_line).toBe(fixture.slice(0, source.start_offset!).split("\n").length);
        expect(source.end_line).toBe(fixture.slice(0, source.end_offset! - 1).split("\n").length);
      }
      await record("saved-answer-and-source-lines-verified", { question });
    }
    expect(answers[0].saved.messages.at(-1)!.content).toMatch(/9\s*(?:AM|a\.m\.)/i);
    expect(answers[0].saved.messages.at(-1)!.content).toMatch(/6\s*(?:PM|p\.m\.)/i);
    expect(answers[1].saved.messages.at(-1)!.content).toMatch(/reserv/i);
    await page.reload();
    await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
    expect(await history()).toEqual(answers[1].saved);
    await page.getByText("Debug details", { exact: true }).last().click();
    const diagnostics = page.getByRole("region", { name: "Recorded retrieval details" });
    await expect(diagnostics.getByText(/Evidence budget:/)).toBeVisible();
    await expect(page.getByRole("region", { name: "Candidate ranking table" })).toBeVisible();
    await page.getByRole("button", { name: /^View source \d+: training-lab.md$/ }).last().click();
    const evidence = page.getByRole("complementary", { name: "Evidence" });
    await expect(evidence.getByText(/Lines \d+–\d+/).first()).toBeVisible();
    await page.screenshot({ path: join(directory, "restored-evidence.png"), fullPage: true });
    await record("refresh-restored-diagnostics-and-lines");
    await page.getByRole("button", { name: "training-lab.md Ready" }).click();
    await page.getByRole("button", { name: "Delete", exact: true }).click();
    await page.getByRole("button", { name: "Delete file", exact: true }).click();
    await expect(page.getByText("File and indexed content deleted.")).toBeVisible();
    await page.reload();
    await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
    await page.getByRole("button", { name: /^View source \d+: training-lab.md$/ }).last().click();
    await expect(evidence.getByText("Source deleted · Historical excerpt").first()).toBeVisible();
    await expect(evidence.getByText(/Lines \d+–\d+/).first()).toBeVisible();
    const deleted = await history();
    for (const message of deleted.messages.filter(m => m.role === "assistant")) {
      const previous = answers[1].saved.messages.find(m => m.message_id === message.message_id)!;
      expect(message.retrieval).toEqual(previous.retrieval);
      expect(message.sources).toEqual(previous.sources!.map(source => ({ ...source, file_deleted: true })));
    }
    const remaining = snapshot();
    for (const rows of Object.values(remaining)) expect(rows).toEqual([]);
    expect(await (await request.get("/api/files")).json()).toEqual([]);
    await writeFile(join(directory, "conversation-after-deletion.json"), JSON.stringify(deleted, null, 2) + "\n");
    await writeFile(join(directory, "storage-after-deletion.json"), JSON.stringify(remaining, null, 2) + "\n");
    await page.screenshot({ path: join(directory, "deleted-evidence.png"), fullPage: true });
    await record("deletion-retains-historical-evidence");
    expect(browserErrors).toEqual([]);
    report.status = "passed";
  } catch (error) {
    report.status = "failed";
    await record("failed", { message: error instanceof Error ? error.message : String(error) });
    throw error;
  } finally {
    await record("finished");
  }
});
