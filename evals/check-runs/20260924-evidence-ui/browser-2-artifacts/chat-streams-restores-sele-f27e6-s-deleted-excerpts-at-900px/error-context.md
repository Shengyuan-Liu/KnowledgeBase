# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: chat.spec.ts >> streams, restores, selects evidence, and retains deleted excerpts at 900px
- Location: e2e/chat.spec.ts:18:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: /Library/ })

```

# Page snapshot

```yaml
- generic [ref=f1e3]:
  - banner [ref=f1e4]:
    - link "Knowledge Base" [ref=f1e5] [cursor=pointer]:
      - /url: /
    - generic [ref=f1e10]: Personal workspace
  - button "Evidence" [ref=f1e13] [cursor=pointer]
  - generic [ref=f1e16]:
    - complementary [ref=f1e17]:
      - generic [ref=f1e19]:
        - heading "Library 1" [level=2] [ref=f1e20]:
          - text: Library
          - generic [ref=f1e21]: "1"
        - paragraph [ref=f1e22]: Your documents, in one place
      - generic [ref=f1e23]:
        - textbox "Search files" [ref=f1e27]:
          - /placeholder: Search files…
        - list "Files" [ref=f1e28]:
          - listitem [ref=f1e29]:
            - button "hours.txt Ready" [ref=f1e30] [cursor=pointer]:
              - generic [ref=f1e31]: TXT
              - generic [ref=f1e32]:
                - strong [ref=f1e33]: hours.txt
                - generic [ref=f1e34]: Ready
      - generic [ref=f1e36]:
        - status
        - button "Upload file" [ref=f1e37] [cursor=pointer]
        - paragraph [ref=f1e40]: TXT and Markdown · UTF-8 · Indexed for search
    - main [ref=f1e41]:
      - generic [ref=f1e42]:
        - generic [ref=f1e43]:
          - heading "Chat" [level=1] [ref=f1e44]
          - paragraph [ref=f1e45]: Grounded in your library
        - button "New chat" [ref=f1e46] [cursor=pointer]
      - generic [ref=f1e47]:
        - generic [ref=f1e48]: When does the library close?
        - article "Assistant answer" [ref=f1e49]:
          - generic [ref=f1e50]:
            - generic [ref=f1e51]: Knowledge Base
            - status [ref=f1e54]: Completed
          - generic [ref=f1e55]:
            - text: The library closes at 5 PM.
            - 'button "View source 1: hours.txt" [active] [ref=f1e56] [cursor=pointer]': "[1]"
          - group [ref=f1e57]:
            - generic "Sources (1 retrieved passages)" [ref=f1e58] [cursor=pointer]
          - button "View evidence" [ref=f1e59] [cursor=pointer]
          - group [ref=f1e60]:
            - generic "Debug details" [ref=f1e61] [cursor=pointer]
            - paragraph [ref=f1e62]:
              - strong [ref=f1e63]: "Retrieval question:"
              - text: When does the library close?
            - paragraph [ref=f1e64]: "Cosine distance: smaller is nearer, not a correctness probability."
            - region "Recorded retrieval details" [ref=f1e65]:
              - paragraph [ref=f1e66]: "Strategy: hybrid · Packing: parent_then_child · Selected child limit: 5"
              - paragraph [ref=f1e67]: "Evidence budget: 31 / 4096 tokens (cl100k_base)."
              - paragraph [ref=f1e68]: "Reranker: offline-reranker · Revision: test-revision · Device: cpu"
              - paragraph [ref=f1e69]: "Retrieval and source lookup: 0.002 s · Query embedding: 0.000 s · Reranking: 0.000 s · Packing: 0.000 s. Stage timings are parts of retrieval, not additional response time."
              - region "Candidate ranking table" [ref=f1e70]:
                - table [ref=f1e71]:
                  - caption [ref=f1e72]: Candidate rankings. Scores are not correctness probabilities.
                  - rowgroup [ref=f1e73]:
                    - row [ref=f1e74]:
                      - columnheader "Child" [ref=f1e75]
                      - columnheader "BM25 rank / score" [ref=f1e76]
                      - columnheader "Vector rank / distance" [ref=f1e77]
                      - columnheader "RRF rank / score" [ref=f1e78]
                      - columnheader "Rerank rank / score" [ref=f1e79]
                      - columnheader "Selected" [ref=f1e80]
                  - rowgroup [ref=f1e81]:
                    - row [ref=f1e82]:
                      - cell "a0ee54bb6d18450aaf1a4d5f530da4b7:child:0" [ref=f1e83]
                      - cell "1 / 0.5754" [ref=f1e84]
                      - cell "1 / 0.0000" [ref=f1e85]
                      - cell "1 / 0.032787" [ref=f1e86]
                      - cell "1 / 3.2500 (logit)" [ref=f1e87]
                      - cell "Yes" [ref=f1e88]
              - paragraph [ref=f1e89]:
                - strong [ref=f1e90]: "Selected child → parent:"
              - list [ref=f1e91]:
                - listitem [ref=f1e92]: a0ee54bb6d18450aaf1a4d5f530da4b7:child:0 → a0ee54bb6d18450aaf1a4d5f530da4b7:parent:0
              - paragraph [ref=f1e93]:
                - strong [ref=f1e94]: "Excluded by evidence budget:"
              - paragraph [ref=f1e95]: No budget exclusions recorded.
            - list [ref=f1e96]:
              - listitem [ref=f1e97]:
                - text: "[1] a0ee54bb6d18450aaf1a4d5f530da4b7:parent:0: 0.0000"
                - generic [ref=f1e98]: · RRF rank 1 (score 0.032787) · BM25 rank 1 · Vector rank 1
                - generic [ref=f1e99]: · Rerank rank 1 (logit 3.2500)
            - paragraph [ref=f1e100]: "Matched citation IDs: 1."
        - generic [ref=f1e101]: What about tomorrow?
        - article "Assistant answer" [ref=f1e102]:
          - generic [ref=f1e103]:
            - generic [ref=f1e104]: Knowledge Base
            - status [ref=f1e107]: Completed
          - generic [ref=f1e108]:
            - text: The library closes at 5 PM.
            - 'button "View source 1: hours.txt" [ref=f1e109] [cursor=pointer]': "[1]"
          - group [ref=f1e110]:
            - generic "Sources (1 retrieved passages)" [ref=f1e111] [cursor=pointer]
          - button "View evidence" [ref=f1e112] [cursor=pointer]
          - group [ref=f1e113]:
            - generic "Debug details" [ref=f1e114] [cursor=pointer]
      - button "Jump to latest" [ref=f1e115] [cursor=pointer]
      - generic [ref=f1e116]:
        - generic [ref=f1e117]:
          - textbox "Ask about your documents" [ref=f1e118]:
            - /placeholder: Ask about your documents…
          - button "Send question" [disabled] [ref=f1e119]
        - paragraph [ref=f1e122]: Enter to send · Shift+Enter for a new line · Check the sources.
  - contentinfo [ref=f1e123]:
    - generic [ref=f1e124]: Keep your sources close.
    - generic [ref=f1e125]: TXT and Markdown knowledge base
```

# Test source

```ts
  1   | import { expect, test } from "@playwright/test";
  2   | 
  3   | test.beforeEach(async ({ request }) => {
  4   |   const files = await (await request.get("/api/files")).json();
  5   |   for (const file of files) await request.delete(`/api/files/${file.file_id}`);
  6   |   await request.post("/api/files", {
  7   |     multipart: {
  8   |       file: {
  9   |         name: "hours.txt",
  10  |         mimeType: "text/plain",
  11  |         buffer: Buffer.from("The library closes at 5 PM."),
  12  |       },
  13  |     },
  14  |   });
  15  | });
  16  | 
  17  | for (const width of [1440, 900, 390]) {
  18  |   test(`streams, restores, selects evidence, and retains deleted excerpts at ${width}px`, async ({
  19  |     page,
  20  |   }, testInfo) => {
  21  |     await page.setViewportSize({ width, height: 900 });
  22  |     const errors: string[] = [];
  23  |     page.on("pageerror", (error) => errors.push(error.message));
  24  |     await page.goto("/");
  25  |     const composer = page.getByRole("textbox", {
  26  |       name: "Ask about your documents",
  27  |     });
  28  |     await composer.fill("When does the library close?");
  29  |     await composer.press("Enter");
  30  |     await expect(page.getByText("Answering…", { exact: true })).toBeVisible();
  31  |     await expect(page.getByText("The library ", { exact: true })).toBeVisible();
  32  |     await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  33  |     await page.getByText("Debug details", { exact: true }).click();
  34  |     await expect(page.getByText("Rerank rank 1 (logit 3.2500)")).toBeVisible();
  35  |     await expect(page.getByRole("region", { name: "Candidate ranking table" })).toBeVisible();
  36  |     await expect(page.getByText(/Evidence budget:/)).toBeVisible();
  37  |     const firstCitation = page.getByRole("button", {
  38  |       name: "View source 1: hours.txt",
  39  |       exact: true,
  40  |     });
  41  |     await firstCitation.click();
  42  |     const evidence =
  43  |       width < 1200
  44  |         ? page.getByRole("dialog", { name: "Evidence" })
  45  |         : page.getByRole("complementary", { name: "Evidence" });
  46  |     await expect(evidence.locator("blockquote")).toHaveText(
  47  |       "The library closes at 5 PM.",
  48  |     );
  49  |     await expect(evidence.getByText("Lines 1–1 · Cited in this answer")).toBeVisible();
  50  |     await page.screenshot({
  51  |       path: testInfo.outputPath(`chat-${width}.png`),
  52  |       fullPage: true,
  53  |     });
  54  |     if (width < 1200) await page.keyboard.press("Escape");
  55  |     await composer.fill("What about tomorrow?");
  56  |     await composer.press("Enter");
  57  |     await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
  58  |     await page.reload();
  59  |     await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
  60  |     await page.getByText("Debug details", { exact: true }).first().click();
  61  |     await expect(page.getByText("Rerank rank 1 (logit 3.2500)").first()).toBeVisible();
  62  |     await expect(page.getByRole("region", { name: "Recorded retrieval details" }).first()).toBeVisible();
  63  |     await expect(
  64  |       page.getByText("When does the library close?", { exact: true }),
  65  |     ).toBeVisible();
  66  |     await page
  67  |       .getByRole("button", { name: "View source 1: hours.txt", exact: true })
  68  |       .first()
  69  |       .click();
  70  |     await expect(evidence.locator("blockquote")).toHaveText(
  71  |       "The library closes at 5 PM.",
  72  |     );
  73  |     if (width < 1200) {
  74  |       await page.keyboard.press("Escape");
> 75  |       await page.getByRole("button", { name: /Library/ }).click();
      |                                                           ^ Error: locator.click: Test timeout of 30000ms exceeded.
  76  |     }
  77  |     await page.getByRole("button", { name: "hours.txt Ready" }).click();
  78  |     await page.getByRole("button", { name: "Delete", exact: true }).click();
  79  |     await page
  80  |       .getByRole("button", { name: "Delete file", exact: true })
  81  |       .click();
  82  |     await expect(
  83  |       page.getByText("File and indexed content deleted."),
  84  |     ).toBeVisible();
  85  |     if (width < 1200) await page.keyboard.press("Escape");
  86  |     await page
  87  |       .getByRole("button", { name: "View source 1: hours.txt", exact: true })
  88  |       .first()
  89  |       .click();
  90  |     await expect(
  91  |       evidence.getByText("Source deleted · Historical excerpt"),
  92  |     ).toBeVisible();
  93  |     await expect(evidence.locator("blockquote")).toHaveText(
  94  |       "The library closes at 5 PM.",
  95  |     );
  96  |     await page.reload();
  97  |     await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
  98  |     await page
  99  |       .getByRole("button", { name: "View source 1: hours.txt", exact: true })
  100 |       .first()
  101 |       .click();
  102 |     await expect(
  103 |       evidence.getByText("Source deleted · Historical excerpt"),
  104 |     ).toBeVisible();
  105 |     expect(errors).toEqual([]);
  106 |   });
  107 | }
  108 | 
  109 | test("stopping keeps partial output locally and does not save an unfinished turn", async ({
  110 |   page,
  111 |   request,
  112 | }) => {
  113 |   await page.goto("/");
  114 |   const composer = page.getByRole("textbox", {
  115 |     name: "Ask about your documents",
  116 |   });
  117 |   await composer.fill("First question");
  118 |   await composer.press("Enter");
  119 |   await expect(page.getByText("Completed", { exact: true })).toHaveCount(1);
  120 |   const id = await page.evaluate(() =>
  121 |     localStorage.getItem("knowledgebase.conversationId"),
  122 |   );
  123 |   await composer.fill("Stop this question");
  124 |   await composer.press("Enter");
  125 |   await expect(page.getByText("Answering…", { exact: true })).toBeVisible();
  126 |   await page.getByRole("button", { name: "Stop", exact: true }).click();
  127 |   await expect(page.getByText("Interrupted", { exact: true })).toBeVisible();
  128 |   await expect(composer).toHaveValue("Stop this question");
  129 |   const history = await (await request.get(`/api/conversations/${id}`)).json();
  130 |   expect(history.messages).toHaveLength(2);
  131 |   await page.reload();
  132 |   await expect(page.getByText("Completed", { exact: true })).toHaveCount(1);
  133 |   await expect(
  134 |     page.getByText("Stop this question", { exact: true }),
  135 |   ).toHaveCount(0);
  136 | });
  137 | 
  138 | test("an unknown saved conversation offers retry or a fresh start", async ({
  139 |   page,
  140 | }) => {
  141 |   await page.addInitScript(() =>
  142 |     localStorage.setItem("knowledgebase.conversationId", "missing"),
  143 |   );
  144 |   await page.goto("/");
  145 |   await expect(
  146 |     page.getByText("Could not restore the conversation"),
  147 |   ).toBeVisible();
  148 |   await page.getByRole("button", { name: "Start fresh" }).click();
  149 |   await expect(
  150 |     page.getByRole("textbox", { name: "Ask about your documents" }),
  151 |   ).toBeEnabled();
  152 |   expect(
  153 |     await page.evaluate(() =>
  154 |       localStorage.getItem("knowledgebase.conversationId"),
  155 |     ),
  156 |   ).toBeNull();
  157 | });
  158 | 
```