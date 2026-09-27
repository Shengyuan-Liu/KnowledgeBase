# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: pdf.spec.ts >> PDF upload, page links, reload and historical evidence after deletion (planned=true)
- Location: e2e/pdf.spec.ts:5:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: 'View source 1: apple-fy24.pdf', exact: true }).first()

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
        - heading "Library 1" [level=2] [ref=e17]:
          - text: Library
          - generic [ref=e18]: "1"
        - paragraph [ref=e19]: Your documents, in one place
      - generic [ref=e20]:
        - textbox "Search files" [ref=e24]:
          - /placeholder: Search files…
        - list "Files" [ref=e25]:
          - listitem [ref=e26]:
            - button "apple-fy24.pdf Ready" [ref=e27] [cursor=pointer]:
              - generic [ref=e28]: PDF
              - generic [ref=e29]:
                - strong [ref=e30]: apple-fy24.pdf
                - generic [ref=e31]: Ready · 4 pages · Review extraction
      - generic [ref=e33]:
        - status [ref=e34]: apple-fy24.pdf is ready.
        - button "Upload file" [ref=e35] [cursor=pointer]
        - paragraph [ref=e38]: TXT / Markdown (UTF-8) · PDF (digital text)
    - main [ref=e39]:
      - generic [ref=e40]:
        - generic [ref=e41]:
          - heading "Chat" [level=1] [ref=e42]
          - paragraph [ref=e43]: Grounded in your library
        - button "New chat" [ref=e44] [cursor=pointer]
      - generic [ref=e45]:
        - generic [ref=e46]: What were total net sales?
        - article "Assistant answer" [ref=e47]:
          - generic [ref=e48]:
            - generic [ref=e49]: Knowledge Base
            - status [ref=e52]: Completed
          - generic [ref=e53]: There is not enough information in the provided sources to answer this question.
          - group [ref=e54]:
            - generic "Sources (4 retrieved passages)" [ref=e55] [cursor=pointer]
          - button "View evidence" [ref=e56] [cursor=pointer]
          - group [ref=e57]:
            - generic "Debug details" [ref=e58] [cursor=pointer]
      - generic [ref=e59]:
        - generic [ref=e60]:
          - checkbox "Plan complex questions May run several searches" [checked] [ref=e61]
          - text: Plan complex questions
          - generic [ref=e62]: May run several searches
        - generic [ref=e63]:
          - textbox "Ask about your documents" [ref=e64]:
            - /placeholder: Ask about your documents…
          - button "Send question" [disabled] [ref=e65]
        - paragraph [ref=e68]: Enter to send · Shift+Enter for a new line · Check the sources.
    - complementary [ref=e69]:
      - generic [ref=e71]:
        - heading "Evidence" [level=2] [ref=e72]
        - paragraph [ref=e73]: Sources for the selected answer
      - generic [ref=e74]:
        - group [ref=e75]:
          - generic "Search plan" [ref=e76] [cursor=pointer]
        - paragraph [ref=e77]: Original excerpts supplied to this answer. A citation does not guarantee support.
        - generic [ref=e78]:
          - generic [ref=e79]:
            - generic [ref=e80]: "1"
            - strong [ref=e81]: apple-fy24.pdf
          - paragraph [ref=e82]: Chunk d7a78ce13a6f467bb4d46cd4dd3f1ce4:child:52
          - paragraph [ref=e83]: CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)
          - paragraph [ref=e84]: PDF original pages · Additional supplied evidence
          - generic "Original PDF pages" [ref=e85]:
            - link "Open page 1" [ref=e86] [cursor=pointer]:
              - /url: /api/files/d7a78ce13a6f467bb4d46cd4dd3f1ce4/original?revision=de76f69979fcece2f1d55a531cbd865aaa5df1fb5a0ccafc9b3ad54453f9756f#page=1
          - blockquote [ref=e87]: 96,169 85,200 Total net sales $
          - generic [ref=e88]:
            - paragraph [ref=e89]: Separately located table column header
            - blockquote [ref=e90]: Three Months Ended
          - generic [ref=e91]:
            - paragraph [ref=e92]: Separately located table column header
            - blockquote [ref=e93]: Twelve Months Ended
          - generic [ref=e94]:
            - paragraph [ref=e95]: Separately located table column header
            - blockquote [ref=e96]: September 28, 2024
          - generic [ref=e97]:
            - paragraph [ref=e98]: Separately located table column header
            - blockquote [ref=e99]: September 30, 2023
          - generic [ref=e100]:
            - paragraph [ref=e101]: Separately located table column header
            - blockquote [ref=e102]: September 28, 2024
          - generic [ref=e103]:
            - paragraph [ref=e104]: Separately located table column header
            - blockquote [ref=e105]: September 30, 2023
          - generic [ref=e106]:
            - paragraph [ref=e107]: Separately located table row header
            - blockquote [ref=e108]: Services
          - group [ref=e109]:
            - generic "Extraction limitations" [ref=e110] [cursor=pointer]
        - generic [ref=e111]:
          - generic [ref=e112]:
            - generic [ref=e113]: "2"
            - strong [ref=e114]: apple-fy24.pdf
          - paragraph [ref=e115]: Chunk d7a78ce13a6f467bb4d46cd4dd3f1ce4:child:45
          - paragraph [ref=e116]: CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)
          - paragraph [ref=e117]: PDF original pages · Additional supplied evidence
          - generic "Original PDF pages" [ref=e118]:
            - link "Open page 1" [ref=e119] [cursor=pointer]:
              - /url: /api/files/d7a78ce13a6f467bb4d46cd4dd3f1ce4/original?revision=de76f69979fcece2f1d55a531cbd865aaa5df1fb5a0ccafc9b3ad54453f9756f#page=1
          - blockquote [ref=e120]: "(1) Net sales by category: iPhone $ 46,222"
          - generic [ref=e121]:
            - paragraph [ref=e122]: Separately located table column header
            - blockquote [ref=e123]: Three Months Ended
          - generic [ref=e124]:
            - paragraph [ref=e125]: Separately located table column header
            - blockquote [ref=e126]: Twelve Months Ended
          - generic [ref=e127]:
            - paragraph [ref=e128]: Separately located table column header
            - blockquote [ref=e129]: September 28, 2024
          - generic [ref=e130]:
            - paragraph [ref=e131]: Separately located table column header
            - blockquote [ref=e132]: September 30, 2023
          - generic [ref=e133]:
            - paragraph [ref=e134]: Separately located table column header
            - blockquote [ref=e135]: September 28, 2024
          - generic [ref=e136]:
            - paragraph [ref=e137]: Separately located table column header
            - blockquote [ref=e138]: September 30, 2023
          - group [ref=e139]:
            - generic "Extraction limitations" [ref=e140] [cursor=pointer]
        - generic [ref=e141]:
          - generic [ref=e142]:
            - generic [ref=e143]: "3"
            - strong [ref=e144]: apple-fy24.pdf
          - paragraph [ref=e145]: Parent passage d7a78ce13a6f467bb4d46cd4dd3f1ce4:parent:3
          - paragraph [ref=e146]: CONDENSED CONSOLIDATED BALANCE SHEETS (Unaudited)
          - paragraph [ref=e147]: PDF original pages · Additional supplied evidence
          - generic "Original PDF pages" [ref=e148]:
            - link "Open page 2" [ref=e149] [cursor=pointer]:
              - /url: /api/files/d7a78ce13a6f467bb4d46cd4dd3f1ce4/original?revision=de76f69979fcece2f1d55a531cbd865aaa5df1fb5a0ccafc9b3ad54453f9756f#page=2
          - blockquote [ref=e150]: "CONDENSED CONSOLIDATED BALANCE SHEETS (Unaudited) (In millions, except number of shares, which are reflected in thousands, and par value) September 28, 2024 September 30, 2023 ASSETS: Current assets: Cash and cash equivalents $ 29,943 $ 29,965 Marketable securities 35,228 31,590 Accounts receivable, net 33,410 29,508 Vendor non-trade receivables 32,833 31,477 Inventories 7,286 6,331 Other current assets 14,287 14,695 Total current assets 152,987 143,566 Non-current assets: Marketable securities 91,479 100,544 Property, plant and equipment, net 45,680 43,715 Other non-current assets 74,834 64,758 Total non-current assets 211,993 209,017 Total assets $ 364,980 $ 352,583 LIABILITIES AND SHAREHOLDERS' EQUITY: Current liabilities: Accounts payable $ 68,960 $ 62,611 Other current liabilities 78,304 58,829 Deferred revenue 8,249 8,061 Commercial paper 9,967 5,985 Term debt 10,912 9,822 Total current liabilities 176,392 145,308 Non-current liabilities: Term debt 85,750 95,281 Other non-current liabilities 45,888 49,848 Total non-current liabilities 131,638 145,129 Total liabilities 308,030 290,437 Commitments and contingencies Shareholders' equity: Common stock and additional paid-in capital, $0.00001 par value: 50,400,000 shares authorized; 15,116,786 and 15,550,061 shares issued and outstanding, respectively 83,276 73,812 Accumulated deficit (19,154) (214) Accumulated other comprehensive loss (7,172) (11,452) Total shareholders' equity 56,950 62,146 Total liabilities and shareholders' equity $ 364,980 $ 352,583"
          - group [ref=e151]:
            - generic "Extraction limitations" [ref=e152] [cursor=pointer]
        - generic [ref=e153]:
          - generic [ref=e154]:
            - generic [ref=e155]: "4"
            - strong [ref=e156]: apple-fy24.pdf
          - paragraph [ref=e157]: Parent passage d7a78ce13a6f467bb4d46cd4dd3f1ce4:parent:0
          - paragraph [ref=e158]: Apple Inc.
          - paragraph [ref=e159]: PDF original pages · Additional supplied evidence
          - generic "Original PDF pages" [ref=e160]:
            - link "Open page 1" [ref=e161] [cursor=pointer]:
              - /url: /api/files/d7a78ce13a6f467bb4d46cd4dd3f1ce4/original?revision=de76f69979fcece2f1d55a531cbd865aaa5df1fb5a0ccafc9b3ad54453f9756f#page=1
          - blockquote [ref=e162]: Apple Inc.
          - group [ref=e163]:
            - generic "Extraction limitations" [ref=e164] [cursor=pointer]
  - contentinfo [ref=e165]:
    - generic [ref=e166]: Keep your sources close.
    - generic [ref=e167]: TXT, Markdown and PDF knowledge base
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | import path from "node:path";
  3  | 
  4  | for (const planned of [false, true]) {
  5  | test(`PDF upload, page links, reload and historical evidence after deletion (planned=${planned})`, async ({ page, request }, testInfo) => {
  6  |   for (const file of await (await request.get("/api/files")).json()) await request.delete(`/api/files/${file.file_id}`);
  7  |   await page.setViewportSize({ width: 1440, height: 1000 });
  8  |   await page.goto("/");
  9  |   await page.getByLabel("Choose TXT, Markdown or PDF file").setInputFiles(path.resolve("../evals/materials/pdf-v2/apple-fy24.pdf"));
  10 |   await expect(page.getByText("apple-fy24.pdf is ready.")).toBeVisible();
  11 |   await expect(page.getByText("Ready · 4 pages · Review extraction")).toBeVisible();
  12 |   const composer = page.getByRole("textbox", { name: "Ask about your documents" });
  13 |   if (planned) await page.getByRole("checkbox", { name: "Plan complex questions" }).check();
  14 |   await composer.fill("What were total net sales?");
  15 |   await composer.press("Enter");
  16 |   await expect(page.getByText("Completed", { exact: true })).toBeVisible();
> 17 |   await page.getByRole("button", { name: "View source 1: apple-fy24.pdf", exact: true }).first().click();
     |                                                                                                  ^ Error: locator.click: Test timeout of 30000ms exceeded.
  18 |   const evidence = page.getByRole("complementary", { name: "Evidence" });
  19 |   const link = evidence.getByRole("link", { name: /Open page/ }).first();
  20 |   await expect(link).toBeVisible();
  21 |   const href = (await link.getAttribute("href"))!;
  22 |   expect(href).toMatch(/original\?revision=.*#page=\d+/);
  23 |   const original = await request.get(href.split("#")[0]);
  24 |   expect(original.status()).toBe(200);
  25 |   expect(original.headers()["content-type"]).toBe("application/pdf");
  26 |   await link.click();
  27 |   const viewer = page.getByRole("dialog", { name: "apple-fy24.pdf" });
  28 |   const pageNumber = Number(href.split("#page=")[1]);
  29 |   await expect(viewer.getByText(`Page ${pageNumber} of 4`, { exact: true })).toBeVisible();
  30 |   await expect(viewer.locator("canvas[data-rendered=true]")).toBeVisible();
  31 |   await page.screenshot({ path: testInfo.outputPath("pdf-viewer.png"), fullPage: true });
  32 |   await viewer.getByRole("button", { name: pageNumber < 4 ? "Next page" : "Previous page" }).click();
  33 |   await expect(viewer.getByText(`Page ${pageNumber < 4 ? pageNumber + 1 : pageNumber - 1} of 4`, { exact: true })).toBeVisible();
  34 |   await expect(viewer.locator("canvas[data-rendered=true]")).toBeVisible();
  35 |   await viewer.getByRole("button", { name: "Close PDF" }).click();
  36 |   await page.screenshot({ path: testInfo.outputPath("pdf-evidence.png"), fullPage: true });
  37 |   await page.reload();
  38 |   await page.getByRole("button", { name: "View source 1: apple-fy24.pdf", exact: true }).first().click();
  39 |   await expect(evidence.getByRole("link", { name: /Open page/ }).first()).toHaveAttribute("href", href);
  40 |   await page.getByRole("button", { name: "apple-fy24.pdf Ready", exact: true }).click();
  41 |   await page.getByRole("button", { name: "Delete", exact: true }).click();
  42 |   await page.getByRole("button", { name: "Delete file", exact: true }).click();
  43 |   await expect(page.getByText("File and indexed content deleted.")).toBeVisible();
  44 |   await expect(evidence.getByRole("link", { name: /Open page/ })).toHaveCount(0);
  45 |   await page.reload();
  46 |   await page.getByRole("button", { name: "View source 1: apple-fy24.pdf", exact: true }).first().click();
  47 |   await expect(evidence.getByText(/original unavailable/).first()).toBeVisible();
  48 |   expect((await request.get(href.split("#")[0])).status()).toBe(404);
  49 | });
  50 | }
  51 | 
```