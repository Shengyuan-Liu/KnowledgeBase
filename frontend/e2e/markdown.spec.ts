import { expect, test } from "@playwright/test";

test("uploads Markdown, inspects exact evidence, restores history, and deletes its source", async ({ page, request }, testInfo) => {
  for (const file of await (await request.get("/api/files")).json()) {
    await request.delete(`/api/files/${file.file_id}`);
  }
  const source = "# Library\n\nThe library closes at 5 PM.\n\n- Weekend visits require a reservation.\n- Bring your library card.\n";
  await page.goto("/");
  await page.getByLabel("Choose TXT or Markdown file").setInputFiles({
    name: "library.md", mimeType: "text/markdown", buffer: Buffer.from(source),
  });
  await expect(page.getByText("library.md is ready.")).toBeVisible();
  await expect(page.getByRole("button", { name: "library.md Ready" }).getByText("MD", { exact: true })).toBeVisible();
  const composer = page.getByRole("textbox", { name: "Ask about your documents" });
  await composer.fill("When does the library close?");
  await composer.press("Enter");
  await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "View source 1: library.md", exact: true }).click();
  const evidence = page.getByRole("complementary", { name: "Evidence" });
  await expect(evidence.locator("blockquote")).toHaveText(source);
  await expect(evidence.getByText(/^Parent passage /)).toBeVisible();
  await expect(evidence.getByText("Library", { exact: true })).toBeVisible();
  const conversationId = await page.evaluate(() => localStorage.getItem("knowledgebase.conversationId"));
  const detail = await (await request.get(`/api/conversations/${conversationId}`)).json();
  const answer = detail.messages.at(-1);
  expect(answer.sources).toHaveLength(1);
  expect(answer.sources[0].parent_id).toBe(answer.sources[0].chunk_id);
  expect(answer.sources[0].matched_child_ids.length).toBeGreaterThan(1);
  expect(answer.retrieval.candidates.length).toBeGreaterThan(1);
  expect(answer.retrieval.evidence_tokens).toBeLessThanOrEqual(answer.retrieval.max_tokens);
  await page.screenshot({ path: testInfo.outputPath("markdown-evidence.png"), fullPage: true });
  await page.reload();
  await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "library.md Ready" }).click();
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  await page.getByRole("button", { name: "Delete file", exact: true }).click();
  await expect(page.getByText("File and indexed content deleted.")).toBeVisible();
  await page.getByRole("button", { name: "View source 1: library.md", exact: true }).click();
  await expect(evidence.getByText("Source deleted · Historical excerpt")).toBeVisible();
  await expect(evidence.locator("blockquote")).toHaveText(source);
  await expect(evidence.getByText(/^Parent passage /)).toBeVisible();
  const restored = await (await request.get(`/api/conversations/${detail.conversation_id}`)).json();
  expect(restored.messages.at(-1).retrieval).toEqual(answer.retrieval);
  expect(await (await request.get("/api/files")).json()).toEqual([]);
});
