import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  for (const file of await (await request.get("/api/files")).json())
    await request.delete(`/api/files/${file.file_id}`);
  await request.post("/api/files", { multipart: { file: {
    name: "hours.txt", mimeType: "text/plain",
    buffer: Buffer.from("The library closes at 5 PM. Students can enter with a library card."),
  } } });
});

for (const width of [1440, 390]) {
  test(`planned search and saved evidence at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 950 });
    await page.goto("/");
    await page.getByRole("checkbox", { name: "Plan complex questions" }).check();
    const composer = page.getByRole("textbox", { name: "Ask about your documents" });
    await composer.fill("What are the closing hours and access rules?");
    await composer.press("Enter");
    await expect(page.getByText("Planning the search…", { exact: true })).toBeVisible();
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "View source 1: hours.txt", exact: true }).first().click();
    const evidence = width < 1200
      ? page.getByRole("dialog", { name: "Evidence" })
      : page.getByRole("complementary", { name: "Evidence" });
    await evidence.getByText("Search plan", { exact: true }).click();
    await expect(evidence.getByText("library closing hours", { exact: true })).toBeVisible();
    await expect(evidence.getByText("library access", { exact: true })).toBeVisible();
    await expect(evidence.getByText(/2 searches completed/)).toBeVisible();
    await expect(evidence.getByRole("region", { name: "Evidence assessment" })).toBeVisible();
    await expect(evidence.getByText("Closing hours · Supported", { exact: true })).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath(`planned-${width}.png`), fullPage: true });
    await page.reload();
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "View source 1: hours.txt", exact: true }).first().click();
    await evidence.getByText("Search plan", { exact: true }).click();
    await expect(evidence.getByText("library access", { exact: true })).toBeVisible();
  });
}

test("stopping during planning leaves no saved exchange", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("checkbox", { name: "Plan complex questions" }).check();
  const composer = page.getByRole("textbox", { name: "Ask about your documents" });
  await composer.fill("Stop planning this question");
  await composer.press("Enter");
  await expect(page.getByText("Planning the search…", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Stop", exact: true }).click();
  await expect(page.getByText("Interrupted", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem("knowledgebase.conversationId"))).toBeNull();
  await page.reload();
  await expect(page.getByText("Completed", { exact: true })).toHaveCount(0);
});

test("stopping during evidence assessment leaves no saved exchange", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("checkbox", { name: "Plan complex questions" }).check();
  const composer = page.getByRole("textbox", { name: "Ask about your documents" });
  await composer.fill("Stop assessment: what are the library hours?");
  await composer.press("Enter");
  await expect(page.getByText("Checking evidence…", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Stop", exact: true }).click();
  await expect(page.getByText("Interrupted", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem("knowledgebase.conversationId"))).toBeNull();
  await page.reload();
  await expect(page.getByText("Completed", { exact: true })).toHaveCount(0);
});
