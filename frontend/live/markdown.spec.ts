import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { appendFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { basename, join, resolve } from "node:path";
import { expect, test } from "@playwright/test";
import type { FileInfo, SavedConversation } from "../src/types";

test("live Markdown RAG acceptance with frozen documentation", async ({ page, request }) => {
  test.setTimeout(600_000);
  const directory = process.env.LIVE_EVIDENCE_DIR!;
  const dataDir = resolve("../data/live-browser", basename(directory));
  await mkdir(directory, { recursive: true });
  const python = (code: string, ...args: string[]) => execFileSync(
    "../.venv/bin/python", ["-c", code, ...args],
    { encoding: "utf8", env: { ...process.env, PYTHONPATH: ".." } },
  );
  const settings = JSON.parse(python(`
import json
from knowledgebase.config import Settings
s = Settings(_env_file='../.env')
print(json.dumps(s.model_dump(mode='json', exclude={'openai_api_key', 'data_dir'})))
`));
  const fixtures = await Promise.all([
    "guides/chat_prefix_completion.md", "guides/kv_cache.md", "quick_start/error_codes.md",
  ].map(async (path) => ({
    name: basename(path), path: `evals/materials/deepseek/md/${path}`,
    text: await readFile(resolve("../evals/materials/deepseek/md", path), "utf8"),
  })));
  fixtures.push({ name: "garden.txt", path: "synthetic fixture", text: "Garden notes.\nBasil prefers well-drained soil and a sunny window.\n" });
  const steps: { name: string; at: string; details?: unknown }[] = [];
  const checks: { id: string; passed: boolean; details?: unknown }[] = [];
  const browserErrors: string[] = [];
  page.on("pageerror", (error) => browserErrors.push(error.message));
  const report = {
    started_at: new Date().toISOString(),
    git_commit: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
    working_tree_dirty: !!execFileSync("git", ["status", "--porcelain"], { encoding: "utf8" }).trim(),
    settings: { ...settings, data_dir: dataDir },
    provider_mode: "Real configured providers; unmodified production application",
    scope: "Targeted development acceptance, not a held-out benchmark or independent human review",
    cost: "Provider token usage and monetary cost are not exposed by the application",
    fixtures: fixtures.map((f) => ({ ...f, sha256: createHash("sha256").update(f.text).digest("hex") })),
    steps, checks, browser_errors: browserErrors, status: "running",
  };
  const save = () => writeFile(join(directory, "acceptance.json"), JSON.stringify(report, null, 2) + "\n");
  const record = async (name: string, details?: unknown) => {
    steps.push({ name, at: new Date().toISOString(), details });
    await save();
    console.log(`Markdown acceptance: ${name}`);
  };
  const check = (id: string, passed: boolean, details?: unknown) => checks.push({ id, passed, details });
  const snapshot = () => JSON.parse(python(`
import json, sqlite3, sys
db = sqlite3.connect(sys.argv[1])
db.row_factory = sqlite3.Row
result = {}
for table in ['files', 'document_sources', 'chunks', 'chunk_structures']:
    result[table] = [dict(row) for row in db.execute('SELECT * FROM ' + table)]
print(json.dumps(result))
db.close()
`, join(dataDir, "knowledgebase.db")));
  type Chunk = { chunk_id: string; file_id: string; text: string; start_offset: number; end_offset: number };
  const histories: SavedConversation[] = [];
  const history = async (): Promise<SavedConversation> => {
    const id = await page.evaluate(() => localStorage.getItem("knowledgebase.conversationId"));
    expect(id).toBeTruthy();
    const response = await request.get(`/api/conversations/${id}`);
    expect(response.ok()).toBe(true);
    return response.json();
  };
  await save();
  try {
    expect(settings.chunking_strategy).toBe("structural");
    expect(await (await request.get("/api/files")).json()).toEqual([]);
    await page.goto("/");
    for (const fixture of fixtures) {
      const started = Date.now();
      await page.getByLabel("Choose TXT or Markdown file").setInputFiles({
        name: fixture.name, mimeType: fixture.name.endsWith(".md") ? "text/markdown" : "text/plain",
        buffer: Buffer.from(fixture.text),
      });
      await expect(page.getByText(`${fixture.name} is ready.`)).toBeVisible();
      await record("upload-ready", { file_name: fixture.name, elapsed_ms: Date.now() - started });
    }
    const files: FileInfo[] = await (await request.get("/api/files")).json();
    const stored = snapshot();
    await writeFile(join(directory, "storage-before-deletion.json"), JSON.stringify(stored, null, 2) + "\n");
    for (const fixture of fixtures) {
      const file = files.find((f) => f.file_name === fixture.name)!;
      const source = stored.document_sources.find((s: { file_id: string }) => s.file_id === file.file_id);
      expect(source.text).toBe(fixture.text);
      expect(source.source_hash).toBe(createHash("sha256").update(fixture.text).digest("hex"));
      const chunks: Chunk[] = stored.chunks.filter((c: Chunk) => c.file_id === file.file_id);
      expect(chunks.length).toBeGreaterThan(0);
      for (const chunk of chunks) {
        expect(chunk.text).toBe(Array.from(fixture.text).slice(chunk.start_offset, chunk.end_offset).join(""));
      }
    }
    expect(stored.chunk_structures).toHaveLength(stored.chunks.length);
    for (const chunk of stored.chunk_structures) {
      expect(chunk.token_count).toBeLessThanOrEqual(settings.chunk_max_tokens);
      expect(chunk.tokenizer).toBe(settings.chunk_tokenizer);
    }
    const kinds = new Set(stored.document_sources.flatMap((s: { blocks: string }) => JSON.parse(s.blocks).map((b: { kind: string }) => b.kind)));
    for (const kind of ["heading", "paragraph", "list", "code", "table"]) expect(kinds.has(kind)).toBe(true);
    await record("canonical-source-and-structure-verified", { files: files.length, chunks: stored.chunks.length, block_kinds: [...kinds] });

    const composer = page.getByRole("textbox", { name: "Ask about your documents" });
    async function ask(id: string, question: string, answerPattern: RegExp, snippets: string[], fresh = true) {
      if (fresh) await page.getByRole("button", { name: "New chat", exact: true }).click();
      const before = await page.getByText("Completed", { exact: true }).count();
      const started = Date.now();
      await composer.fill(question);
      await composer.press("Enter");
      await expect(page.getByText("Completed", { exact: true })).toHaveCount(before + 1);
      const conversation = await history();
      histories.push(conversation);
      const answer = conversation.messages.at(-1)!;
      const sources = answer.sources ?? [];
      const snippetCoverage = snippets.map((snippet) => ({ snippet, retrieved: sources.some((s) => s.text.includes(snippet)) }));
      await appendFile(join(directory, "answers.jsonl"), JSON.stringify({
        id, question, elapsed_ms: Date.now() - started, conversation_id: conversation.conversation_id,
        answer, expected_evidence: snippetCoverage,
      }) + "\n");
      check(`${id}:answer-content-smoke`, answerPattern.test(answer.content), { pattern: answerPattern.source });
      check(`${id}:gold-snippets-retrieved`, snippetCoverage.every((s) => s.retrieved), snippetCoverage);
      check(`${id}:citation-ids-valid`, (answer.citation_check?.invalid_source_ids.length ?? 0) === 0);
      if (snippets.length) check(`${id}:has-citation`, (answer.citation_check?.valid_source_ids.length ?? 0) > 0);
      for (const source of sources) {
        expect(source.text).toBe(stored.chunks.find((c: Chunk) => c.chunk_id === source.chunk_id)?.text);
      }
      await record("answer-recorded", { id, elapsed_ms: Date.now() - started });
      return answer;
    }
    await ask("prefix-configuration", "According to the uploaded Chat Prefix Completion guide, what role and prefix flag must the last message use, and what base URL enables the feature? Cite the guide.", /assistant/i,
      ['`assistant`', '`True`', 'https://api.deepseek.com/beta']);
    await ask("prefix-code-followup", "In that guide's Python example, what exact stop value prevents additional explanations? Cite the example.", /```/,
      ['stop=["```"]'], false);
    await page.getByRole("button", { name: /^View source \d+: chat_prefix_completion.md$/ }).last().click();
    const evidence = page.getByRole("complementary", { name: "Evidence" });
    await expect(evidence.locator("blockquote").filter({ hasText: 'stop=["```"]' }).first()).toBeVisible();
    await page.screenshot({ path: join(directory, "markdown-code-evidence.png"), fullPage: true });
    await page.reload();
    await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
    await record("two-turn-refresh-restored");

    await ask("cache-rule", "What matching condition does the uploaded Context Caching guide require for a cache hit?", /fully|complete|exact/i,
      ['**fully matches** a **cache prefix unit**']);
    await ask("cache-fields", "Which two usage fields distinguish cache hits and misses in the uploaded Context Caching guide, and what does each count?", /prompt_cache_hit_tokens/,
      ['prompt_cache_hit_tokens', 'prompt_cache_miss_tokens']);
    await ask("table-error-429", "In the uploaded Error Codes table, what causes HTTP 429 and what action does the table recommend?", /quick|fast|rate|pace/i,
      ['429', 'Please pace your requests reasonably.']);
    await page.getByRole("button", { name: /^View source \d+: error_codes.md$/ }).first().click();
    await expect(evidence.locator("blockquote").filter({ hasText: "429" }).first()).toBeVisible();
    await page.screenshot({ path: join(directory, "markdown-table-evidence.png"), fullPage: true });
    await ask("missing-personal-balance", "What is the exact remaining balance in my personal DeepSeek account? Use only my uploaded documents.", /not|cannot|can't|no |insufficient/i, []);

    const prior = await history();
    await composer.fill("Write a detailed explanation of every uploaded guide, including thirty numbered reminders with citations. Be thorough.");
    await composer.press("Enter");
    await expect(page.getByText("Answering…", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Stop", exact: true }).click();
    await expect(page.getByText("Interrupted", { exact: true })).toBeVisible();
    await page.waitForTimeout(1500);
    expect((await history()).messages).toEqual(prior.messages);
    await page.reload();
    await expect(page.getByText("Interrupted", { exact: true })).toHaveCount(0);
    await record("cancelled-answer-not-persisted");

    const prefixConversation = histories[1];
    await page.evaluate((id) => localStorage.setItem("knowledgebase.conversationId", id), prefixConversation.conversation_id);
    await page.reload();
    await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
    const removed = files.find((f) => f.file_name === "chat_prefix_completion.md")!;
    await page.getByRole("button", { name: `${removed.file_name} Ready` }).click();
    await page.getByRole("button", { name: "Delete", exact: true }).click();
    await page.getByRole("button", { name: "Delete file", exact: true }).click();
    await expect(page.getByText("File and indexed content deleted.")).toBeVisible();
    await page.getByRole("button", { name: /^View source \d+: chat_prefix_completion.md$/ }).last().click();
    await expect(evidence.getByText("Source deleted · Historical excerpt").first()).toBeVisible();
    await expect(evidence.locator("blockquote").filter({ hasText: 'stop=["```"]' }).first()).toBeVisible();
    await page.screenshot({ path: join(directory, "deleted-markdown-evidence.png"), fullPage: true });
    const after = await ask("post-deletion", "Using only documents currently in my library, what base URL enables DeepSeek chat prefix completion?", /not|cannot|can't|no |insufficient/i, [], false);
    expect(after.sources?.every((s) => s.file_id !== removed.file_id)).toBe(true);
    const remaining = snapshot();
    expect(remaining.document_sources.some((s: { file_id: string }) => s.file_id === removed.file_id)).toBe(false);
    expect(remaining.chunks.some((c: Chunk) => c.file_id === removed.file_id)).toBe(false);
    expect(remaining.chunk_structures).toHaveLength(remaining.chunks.length);
    await writeFile(join(directory, "storage-after-deletion.json"), JSON.stringify(remaining, null, 2) + "\n");
    await writeFile(join(directory, "conversation-after-deletion.json"), JSON.stringify(await history(), null, 2) + "\n");
    await record("deletion-and-historical-evidence-verified");
    expect(browserErrors).toEqual([]);
    report.status = checks.every((c) => c.passed) ? "passed" : "completed-with-check-failures";
    await record("finished");
    expect(checks.filter((c) => !c.passed)).toEqual([]);
  } catch (error) {
    report.status = "failed";
    await record("failed", { message: error instanceof Error ? error.message : String(error) });
    throw error;
  } finally {
    await save();
    console.log(`Live Markdown evidence: ${directory}`);
  }
});
