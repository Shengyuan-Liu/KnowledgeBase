import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  for (const file of await (await request.get("/api/files")).json())
    await request.delete(`/api/files/${file.file_id}`);
  for (const [name, text] of [
    ["award.txt", "The Aster Prize winner is Mira Cole."],
    ["staff.txt", "Mira Cole works at Birch Institute."],
  ]) await request.post("/api/files", { multipart: { file: {
    name, mimeType: "text/plain", buffer: Buffer.from(text),
  } } });
});

for (const width of [1440, 390]) {
  test(`dependent searches show target evidence and survive reload at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/");
    await page.getByRole("checkbox", { name: "Plan complex questions" }).check();
    const composer = page.getByRole("textbox", { name: "Ask about your documents" });
    await composer.fill("Where does the Aster Prize winner work?");
    await composer.press("Enter");
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    const evidence = width < 1200 ? page.getByRole("dialog", { name: "Evidence" }) : page.getByRole("complementary", { name: "Evidence" });
    for (const reload of [false, true]) {
      if (reload) await page.reload();
      await page.getByRole("button", { name: "View source 2: staff.txt", exact: true }).first().click();
      await evidence.getByText("Search plan", { exact: true }).click();
      await expect(evidence.getByText(/Used 2 retrieval rounds/)).toBeVisible();
      await expect(evidence.getByText("Search target: Mira Cole. Found in:")).toBeVisible();
      await expect(evidence.getByText("Search stopped: requirements supported.")).toBeVisible();
      await expect(evidence.locator("blockquote").filter({ hasText: "The Aster Prize winner is Mira Cole." }).first()).toBeVisible();
    }
    await page.screenshot({ path: testInfo.outputPath(`hops-${width}.png`), fullPage: true });
  });
}

test("stop during target binding does not save an unfinished answer", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("checkbox", { name: "Plan complex questions" }).check();
  const composer = page.getByRole("textbox", { name: "Ask about your documents" });
  await composer.fill("Stop binding: where does the Aster Prize winner work?");
  await composer.press("Enter");
  await expect(page.getByText("Searching round 2…", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Stop", exact: true }).click();
  await expect(page.getByText("Interrupted", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem("knowledgebase.conversationId"))).toBeNull();
  await page.reload();
  await expect(page.getByText("Completed", { exact: true })).toHaveCount(0);
});
