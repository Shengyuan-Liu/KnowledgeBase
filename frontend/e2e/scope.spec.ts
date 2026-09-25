import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  for (const file of await (await request.get("/api/files")).json()) {
    await request.delete(`/api/files/${file.file_id}`);
  }
  for (const name of ["general-faq.txt", "admissions-faq.txt"]) {
    await request.post("/api/files", { multipart: { file: {
      name, mimeType: "text/plain", buffer: Buffer.from("The library closes at 5 PM."),
    } } });
  }
});

test("scoped evidence and recorded document selection survive refresh and deletion", async ({ page, request }, testInfo) => {
  await page.goto("/");
  const composer = page.getByRole("textbox", { name: "Ask about your documents" });
  await composer.fill("According to general FAQ, when does the library close?");
  await composer.press("Enter");
  await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  await page.getByText("Debug details", { exact: true }).click();
  await expect(page.getByLabel("Document scope")).toContainText("Searched documents: general-faq.txt");
  await expect(page.getByRole("button", { name: "View source 1: general-faq.txt", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /View source.*admissions-faq/ })).toHaveCount(0);
  await page.screenshot({ path: testInfo.outputPath("document-scope.png"), fullPage: true });
  const files = await (await request.get("/api/files")).json();
  await request.delete(`/api/files/${files.find((file: { file_name: string }) => file.file_name === "general-faq.txt").file_id}`);
  await page.reload();
  await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  await page.getByText("Debug details", { exact: true }).click();
  await expect(page.getByLabel("Document scope")).toContainText("general-faq.txt");
  await page.getByRole("button", { name: "View source 1: general-faq.txt", exact: true }).click();
  await expect(page.getByText("Source deleted · Historical excerpt")).toBeVisible();
});

test("ambiguous name asks for clarification and accepts an exact filename next", async ({ page }) => {
  await page.goto("/");
  const composer = page.getByRole("textbox", { name: "Ask about your documents" });
  await composer.fill("According to the FAQ, when does the library close?");
  await composer.press("Enter");
  await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  await expect(page.locator("article > div").filter({ hasText: /The document reference "FAQ" matches more than one file:/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /View source/ })).toHaveCount(0);
  await composer.fill("According to general-faq.txt, when does the library close?");
  await composer.press("Enter");
  await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
  await expect(page.getByRole("button", { name: "View source 1: general-faq.txt", exact: true })).toBeVisible();
});
