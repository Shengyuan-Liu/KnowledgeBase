import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  const files = await (await request.get("/api/files")).json();
  for (const file of files) await request.delete(`/api/files/${file.file_id}`);
});

for (const width of [1440, 1024, 390]) {
  test(`real file API and responsive library at ${width}px`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto("/");
    if (width < 768)
      await page.getByRole("button", { name: /Library/ }).click();
    await expect(page.getByText("A home for your notes")).toBeVisible();
    const filename = `campus-reference-notes-for-the-autumn-semester-${width}.txt`;
    await page.getByLabel("Choose TXT file").setInputFiles({
      name: filename,
      mimeType: "text/plain",
      buffer: Buffer.from(
        "The library opens at 9 AM on weekdays.\nBring your student card.",
      ),
    });
    await expect(page.getByText(`${filename} is ready.`)).toBeVisible();
    await expect(
      page.getByRole("button", { name: new RegExp(`${filename} Ready`) }),
    ).toBeVisible();
    await page.reload();
    if (width < 768)
      await page.getByRole("button", { name: /Library/ }).click();
    const row = page.getByRole("button", {
      name: new RegExp(`${filename} Ready`),
    });
    await expect(row).toBeVisible();
    await row.click();
    const deleteButton = page.getByRole("button", {
      name: "Delete",
      exact: true,
    });
    await deleteButton.click();
    await expect(
      page.getByRole("button", { name: "Cancel", exact: true }),
    ).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(deleteButton).toBeFocused();
    await expect(row).toBeVisible();
    await page.getByRole("textbox", { name: "Search files" }).fill("no-match");
    await expect(page.getByText("No matching files")).toBeVisible();
    await page.getByRole("textbox", { name: "Search files" }).fill("");
    await page.screenshot({
      path: testInfo.outputPath(`library-${width}.png`),
      fullPage: true,
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await deleteButton.click();
    await page
      .getByRole("button", { name: "Delete file", exact: true })
      .click();
    await expect(
      page.getByText("File and indexed content deleted."),
    ).toBeVisible();
    await expect(row).toHaveCount(0);
    await page.reload();
    if (width < 768) {
      const trigger = page.getByRole("button", { name: /Library/ });
      await trigger.click();
      await expect(page.getByText("A home for your notes")).toBeVisible();
      await page.keyboard.press("Escape");
      await expect(trigger).toBeFocused();
    }
    if (width < 1200) {
      await page.getByRole("button", { name: "Evidence", exact: true }).click();
      await expect(page.getByText("Sources will appear here")).toBeVisible();
      await page.keyboard.press("Escape");
    }
    await page.screenshot({
      path: testInfo.outputPath(`workspace-${width}.png`),
      fullPage: true,
    });
    expect(errors).toEqual([]);
  });
}

test("backend rejects invalid UTF-8 and empty uploads", async ({ page }) => {
  await page.goto("/");
  await page
    .getByLabel("Choose TXT file")
    .setInputFiles({
      name: "invalid.txt",
      mimeType: "text/plain",
      buffer: Buffer.from([0xff]),
    });
  await expect(page.getByRole("alert")).toHaveText(
    "The file must be UTF-8 encoded.",
  );
  await page
    .getByLabel("Choose TXT file")
    .setInputFiles({
      name: "empty.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("   "),
    });
  await expect(page.getByRole("alert")).toHaveText(
    "The file must contain nonempty text.",
  );
});
