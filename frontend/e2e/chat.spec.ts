import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  const files = await (await request.get("/api/files")).json();
  for (const file of files) await request.delete(`/api/files/${file.file_id}`);
  await request.post("/api/files", {
    multipart: {
      file: {
        name: "hours.txt",
        mimeType: "text/plain",
        buffer: Buffer.from("The library closes at 5 PM."),
      },
    },
  });
});

for (const width of [1440, 390]) {
  test(`streams, restores, selects evidence, and retains deleted excerpts at ${width}px`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto("/");
    const composer = page.getByRole("textbox", {
      name: "Ask about your documents",
    });
    await composer.fill("When does the library close?");
    await composer.press("Enter");
    await expect(page.getByText("Answering…", { exact: true })).toBeVisible();
    await expect(page.getByText("The library ", { exact: true })).toBeVisible();
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    await page.getByText("Debug details", { exact: true }).click();
    await expect(page.getByText("Rerank rank 1 (logit 3.2500)")).toBeVisible();
    const firstCitation = page.getByRole("button", {
      name: "View source 1: hours.txt",
      exact: true,
    });
    await firstCitation.click();
    const evidence =
      width < 1200
        ? page.getByRole("dialog", { name: "Evidence" })
        : page.getByRole("complementary", { name: "Evidence" });
    await expect(evidence.locator("blockquote")).toHaveText(
      "The library closes at 5 PM.",
    );
    await page.screenshot({
      path: testInfo.outputPath(`chat-${width}.png`),
      fullPage: true,
    });
    if (width < 1200) await page.keyboard.press("Escape");
    await composer.fill("What about tomorrow?");
    await composer.press("Enter");
    await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
    await page.reload();
    await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
    await page.getByText("Debug details", { exact: true }).first().click();
    await expect(page.getByText("Rerank rank 1 (logit 3.2500)").first()).toBeVisible();
    await expect(
      page.getByText("When does the library close?", { exact: true }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "View source 1: hours.txt", exact: true })
      .first()
      .click();
    await expect(evidence.locator("blockquote")).toHaveText(
      "The library closes at 5 PM.",
    );
    if (width < 1200) {
      await page.keyboard.press("Escape");
      await page.getByRole("button", { name: /Library/ }).click();
    }
    await page.getByRole("button", { name: "hours.txt Ready" }).click();
    await page.getByRole("button", { name: "Delete", exact: true }).click();
    await page
      .getByRole("button", { name: "Delete file", exact: true })
      .click();
    await expect(
      page.getByText("File and indexed content deleted."),
    ).toBeVisible();
    if (width < 1200) await page.keyboard.press("Escape");
    await page
      .getByRole("button", { name: "View source 1: hours.txt", exact: true })
      .first()
      .click();
    await expect(
      evidence.getByText("Source deleted · Historical excerpt"),
    ).toBeVisible();
    await expect(evidence.locator("blockquote")).toHaveText(
      "The library closes at 5 PM.",
    );
    await page.reload();
    await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
    await page
      .getByRole("button", { name: "View source 1: hours.txt", exact: true })
      .first()
      .click();
    await expect(
      evidence.getByText("Source deleted · Historical excerpt"),
    ).toBeVisible();
    expect(errors).toEqual([]);
  });
}

test("stopping keeps partial output locally and does not save an unfinished turn", async ({
  page,
  request,
}) => {
  await page.goto("/");
  const composer = page.getByRole("textbox", {
    name: "Ask about your documents",
  });
  await composer.fill("First question");
  await composer.press("Enter");
  await expect(page.getByText("Completed", { exact: true })).toHaveCount(1);
  const id = await page.evaluate(() =>
    localStorage.getItem("knowledgebase.conversationId"),
  );
  await composer.fill("Stop this question");
  await composer.press("Enter");
  await expect(page.getByText("Answering…", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Stop", exact: true }).click();
  await expect(page.getByText("Interrupted", { exact: true })).toBeVisible();
  await expect(composer).toHaveValue("Stop this question");
  const history = await (await request.get(`/api/conversations/${id}`)).json();
  expect(history.messages).toHaveLength(2);
  await page.reload();
  await expect(page.getByText("Completed", { exact: true })).toHaveCount(1);
  await expect(
    page.getByText("Stop this question", { exact: true }),
  ).toHaveCount(0);
});

test("an unknown saved conversation offers retry or a fresh start", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("knowledgebase.conversationId", "missing"),
  );
  await page.goto("/");
  await expect(
    page.getByText("Could not restore the conversation"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Start fresh" }).click();
  await expect(
    page.getByRole("textbox", { name: "Ask about your documents" }),
  ).toBeEnabled();
  expect(
    await page.evaluate(() =>
      localStorage.getItem("knowledgebase.conversationId"),
    ),
  ).toBeNull();
});
