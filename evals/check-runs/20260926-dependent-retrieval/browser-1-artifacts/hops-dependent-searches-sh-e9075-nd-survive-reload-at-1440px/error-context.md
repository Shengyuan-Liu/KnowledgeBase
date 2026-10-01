# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: hops.spec.ts >> dependent searches show target evidence and survive reload at 1440px
- Location: e2e/hops.spec.ts:15:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Searching round 2…', { exact: true })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText('Searching round 2…', { exact: true }) with timeout 5000ms
  - waiting for getByText('Searching round 2…', { exact: true })

```

```yaml
- banner:
  - link "Knowledge Base":
    - /url: /
  - text: A little clarity, from your own documents. Personal workspace
- complementary "Library 2":
  - heading "Library 2" [level=2]
  - paragraph: Your documents, in one place
  - textbox "Search files":
    - /placeholder: Search files…
  - list "Files":
    - listitem:
      - button "staff.txt Ready":
        - text: TXT
        - strong: staff.txt
        - text: Ready
    - listitem:
      - button "award.txt Ready":
        - text: TXT
        - strong: award.txt
        - text: Ready
  - status
  - button "Upload file"
  - paragraph: TXT / Markdown (UTF-8) · PDF (digital text)
- main:
  - heading "Chat" [level=1]
  - paragraph: Grounded in your library
  - button "New chat"
  - text: Where does the Aster Prize winner work?
  - article "Assistant answer":
    - text: Knowledge Base
    - status: Completed
    - text: Mira Cole works at Birch Institute.
    - 'button "View source 2: staff.txt"': "[2]"
    - group: Sources (2 retrieved passages)
    - button "View evidence"
    - group: Debug details
  - checkbox "Plan complex questions May run several searches" [checked]
  - text: Plan complex questions May run several searches
  - textbox "Ask about your documents":
    - /placeholder: Ask about your documents…
  - button "Send question" [disabled]
  - paragraph: Enter to send · Shift+Enter for a new line · Check the sources.
- complementary "Evidence":
  - heading "Evidence" [level=2]
  - paragraph: Sources for the selected answer
  - group: Search plan
  - paragraph: Original excerpts supplied to this answer. A citation does not guarantee support.
  - text: "1"
  - strong: award.txt
  - paragraph: Parent passage e0b7f058bd2848c39c59a21280378c78:parent:0
  - paragraph: Lines 1–1 · Additional supplied evidence
  - blockquote: The Aster Prize winner is Mira Cole.
  - text: "2"
  - strong: staff.txt
  - paragraph: Parent passage 888a042174cd44eaae8f59dc01e54473:parent:0
  - paragraph: Lines 1–1 · Cited in this answer
  - blockquote: Mira Cole works at Birch Institute.
- contentinfo: Keep your sources close. TXT, Markdown and PDF knowledge base
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | 
  3  | test.beforeEach(async ({ request }) => {
  4  |   for (const file of await (await request.get("/api/files")).json())
  5  |     await request.delete(`/api/files/${file.file_id}`);
  6  |   for (const [name, text] of [
  7  |     ["award.txt", "The Aster Prize winner is Mira Cole."],
  8  |     ["staff.txt", "Mira Cole works at Birch Institute."],
  9  |   ]) await request.post("/api/files", { multipart: { file: {
  10 |     name, mimeType: "text/plain", buffer: Buffer.from(text),
  11 |   } } });
  12 | });
  13 | 
  14 | for (const width of [1440, 390]) {
  15 |   test(`dependent searches show target evidence and survive reload at ${width}px`, async ({ page }, testInfo) => {
  16 |     await page.setViewportSize({ width, height: 1000 });
  17 |     await page.goto("/");
  18 |     await page.getByRole("checkbox", { name: "Plan complex questions" }).check();
  19 |     const composer = page.getByRole("textbox", { name: "Ask about your documents" });
  20 |     await composer.fill("Where does the Aster Prize winner work?");
  21 |     await composer.press("Enter");
> 22 |     await expect(page.getByText("Searching round 2…", { exact: true })).toBeVisible();
     |                                                                         ^ Error: expect(locator).toBeVisible() failed
  23 |     await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  24 |     const evidence = width < 1200 ? page.getByRole("dialog", { name: "Evidence" }) : page.getByRole("complementary", { name: "Evidence" });
  25 |     for (const reload of [false, true]) {
  26 |       if (reload) await page.reload();
  27 |       await page.getByRole("button", { name: "View source 2: staff.txt", exact: true }).first().click();
  28 |       await evidence.getByText("Search plan", { exact: true }).click();
  29 |       await expect(evidence.getByText(/Used 2 retrieval rounds/)).toBeVisible();
  30 |       await expect(evidence.getByText("Search target: Mira Cole. Found in:")).toBeVisible();
  31 |       await expect(evidence.getByText("Search stopped: dependencies complete.")).toBeVisible();
  32 |       await expect(evidence.locator("blockquote").filter({ hasText: "The Aster Prize winner is Mira Cole." }).first()).toBeVisible();
  33 |     }
  34 |     await page.screenshot({ path: testInfo.outputPath(`hops-${width}.png`), fullPage: true });
  35 |   });
  36 | }
  37 | 
  38 | test("stop during target binding does not save an unfinished answer", async ({ page }) => {
  39 |   await page.goto("/");
  40 |   await page.getByRole("checkbox", { name: "Plan complex questions" }).check();
  41 |   const composer = page.getByRole("textbox", { name: "Ask about your documents" });
  42 |   await composer.fill("Stop binding: where does the Aster Prize winner work?");
  43 |   await composer.press("Enter");
  44 |   await expect(page.getByText("Searching round 2…", { exact: true })).toBeVisible();
  45 |   await page.getByRole("button", { name: "Stop", exact: true }).click();
  46 |   await expect(page.getByText("Interrupted", { exact: true })).toBeVisible();
  47 |   expect(await page.evaluate(() => localStorage.getItem("knowledgebase.conversationId"))).toBeNull();
  48 |   await page.reload();
  49 |   await expect(page.getByText("Completed", { exact: true })).toHaveCount(0);
  50 | });
  51 | 
```