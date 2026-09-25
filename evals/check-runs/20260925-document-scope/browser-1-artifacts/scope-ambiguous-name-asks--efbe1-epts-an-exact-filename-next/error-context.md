# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scope.spec.ts >> ambiguous name asks for clarification and accepts an exact filename next
- Location: e2e/scope.spec.ts:35:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText(/The document reference "FAQ" matches more than one file:/)
Expected: visible
Error: strict mode violation: getByText(/The document reference "FAQ" matches more than one file:/) resolved to 2 elements:
    1) <div class="_answerText_1lgb1_49">The document reference "FAQ" matches more than on…</div> aka getByText('The document reference "FAQ"').first()
    2) <p>The document reference "FAQ" matches more than on…</p> aka getByLabel('Document scope').getByText('The document reference "FAQ"')

Call log:
  - Expect "toBeVisible" getByText(/The document reference "FAQ" matches more than one file:/) with timeout 5000ms
  - waiting for getByText(/The document reference "FAQ" matches more than one file:/)

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - link "Knowledge Base" [ref=e5] [cursor=pointer]:
      - /url: /
    - generic [ref=e10]: A little clarity, from your own documents.
    - generic [ref=e11]: Personal workspace
  - generic [ref=e13]:
    - complementary [ref=e14]:
      - generic [ref=e16]:
        - heading "Library 2" [level=2] [ref=e17]:
          - text: Library
          - generic [ref=e18]: "2"
        - paragraph [ref=e19]: Your documents, in one place
      - generic [ref=e20]:
        - textbox "Search files" [ref=e24]:
          - /placeholder: Search files…
        - list "Files" [ref=e25]:
          - listitem [ref=e26]:
            - button "admissions-faq.txt Ready" [ref=e27] [cursor=pointer]:
              - generic [ref=e28]: TXT
              - generic [ref=e29]:
                - strong [ref=e30]: admissions-faq.txt
                - generic [ref=e31]: Ready
          - listitem [ref=e33]:
            - button "general-faq.txt Ready" [ref=e34] [cursor=pointer]:
              - generic [ref=e35]: TXT
              - generic [ref=e36]:
                - strong [ref=e37]: general-faq.txt
                - generic [ref=e38]: Ready
      - generic [ref=e40]:
        - status
        - button "Upload file" [ref=e41] [cursor=pointer]
        - paragraph [ref=e44]: TXT and Markdown · UTF-8 · Indexed for search
    - main [ref=e45]:
      - generic [ref=e46]:
        - generic [ref=e47]:
          - heading "Chat" [level=1] [ref=e48]
          - paragraph [ref=e49]: Grounded in your library
        - button "New chat" [ref=e50] [cursor=pointer]
      - generic [ref=e51]:
        - generic [ref=e52]: According to the FAQ, when does the library close?
        - article "Assistant answer" [ref=e53]:
          - generic [ref=e54]:
            - generic [ref=e55]: Knowledge Base
            - status [ref=e58]: Completed
          - generic [ref=e59]: "The document reference \"FAQ\" matches more than one file: admissions-faq.txt, general-faq.txt. Please specify the exact filename or select a file."
          - group [ref=e60]:
            - generic "Sources (0 retrieved passages)" [ref=e61] [cursor=pointer]
          - button "View evidence" [ref=e62] [cursor=pointer]
          - group [ref=e63]:
            - generic "Debug details" [ref=e64] [cursor=pointer]
      - generic [ref=e65]:
        - generic [ref=e66]:
          - textbox "Ask about your documents" [ref=e67]:
            - /placeholder: Ask about your documents…
          - button "Send question" [disabled] [ref=e68]
        - paragraph [ref=e71]: Enter to send · Shift+Enter for a new line · Check the sources.
    - complementary [ref=e72]:
      - generic [ref=e74]:
        - heading "Evidence" [level=2] [ref=e75]
        - paragraph [ref=e76]: Sources for the selected answer
      - generic [ref=e77]:
        - heading "No sources retrieved" [level=3] [ref=e81]
        - paragraph [ref=e82]: This answer has no retrieved passages to display.
  - contentinfo [ref=e83]:
    - generic [ref=e84]: Keep your sources close.
    - generic [ref=e85]: TXT and Markdown knowledge base
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | 
  3  | test.beforeEach(async ({ request }) => {
  4  |   for (const file of await (await request.get("/api/files")).json()) {
  5  |     await request.delete(`/api/files/${file.file_id}`);
  6  |   }
  7  |   for (const name of ["general-faq.txt", "admissions-faq.txt"]) {
  8  |     await request.post("/api/files", { multipart: { file: {
  9  |       name, mimeType: "text/plain", buffer: Buffer.from("The library closes at 5 PM."),
  10 |     } } });
  11 |   }
  12 | });
  13 | 
  14 | test("scoped evidence and recorded document selection survive refresh and deletion", async ({ page, request }, testInfo) => {
  15 |   await page.goto("/");
  16 |   const composer = page.getByRole("textbox", { name: "Ask about your documents" });
  17 |   await composer.fill("According to general FAQ, when does the library close?");
  18 |   await composer.press("Enter");
  19 |   await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  20 |   await page.getByText("Debug details", { exact: true }).click();
  21 |   await expect(page.getByLabel("Document scope")).toContainText("Searched documents: general-faq.txt");
  22 |   await expect(page.getByRole("button", { name: "View source 1: general-faq.txt", exact: true })).toBeVisible();
  23 |   await expect(page.getByRole("button", { name: /View source.*admissions-faq/ })).toHaveCount(0);
  24 |   await page.screenshot({ path: testInfo.outputPath("document-scope.png"), fullPage: true });
  25 |   const files = await (await request.get("/api/files")).json();
  26 |   await request.delete(`/api/files/${files.find((file: { file_name: string }) => file.file_name === "general-faq.txt").file_id}`);
  27 |   await page.reload();
  28 |   await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  29 |   await page.getByText("Debug details", { exact: true }).click();
  30 |   await expect(page.getByLabel("Document scope")).toContainText("general-faq.txt");
  31 |   await page.getByRole("button", { name: "View source 1: general-faq.txt", exact: true }).click();
  32 |   await expect(page.getByText("Source deleted · Historical excerpt")).toBeVisible();
  33 | });
  34 | 
  35 | test("ambiguous name asks for clarification and accepts an exact filename next", async ({ page }) => {
  36 |   await page.goto("/");
  37 |   const composer = page.getByRole("textbox", { name: "Ask about your documents" });
  38 |   await composer.fill("According to the FAQ, when does the library close?");
  39 |   await composer.press("Enter");
  40 |   await expect(page.getByText("Completed", { exact: true })).toBeVisible();
> 41 |   await expect(page.getByText(/The document reference "FAQ" matches more than one file:/)).toBeVisible();
     |                                                                                            ^ Error: expect(locator).toBeVisible() failed
  42 |   await expect(page.getByRole("button", { name: /View source/ })).toHaveCount(0);
  43 |   await composer.fill("According to general-faq.txt, when does the library close?");
  44 |   await composer.press("Enter");
  45 |   await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
  46 |   await expect(page.getByRole("button", { name: "View source 1: general-faq.txt", exact: true })).toBeVisible();
  47 | });
  48 | 
```