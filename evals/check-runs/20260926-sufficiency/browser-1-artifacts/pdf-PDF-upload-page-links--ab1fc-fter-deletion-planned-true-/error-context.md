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
            - generic "Sources (3 retrieved passages)" [ref=e55] [cursor=pointer]
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
          - paragraph [ref=e82]: Chunk e4791e150178451085a2bb5089d6353e:child:10
          - paragraph [ref=e83]: CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)
          - paragraph [ref=e84]: PDF original pages · Additional supplied evidence
          - generic "Original PDF pages" [ref=e85]:
            - link "Open page 1" [ref=e86] [cursor=pointer]:
              - /url: /api/files/e4791e150178451085a2bb5089d6353e/original?revision=de76f69979fcece2f1d55a531cbd865aaa5df1fb5a0ccafc9b3ad54453f9756f#page=1
          - blockquote [ref=e87]: 94,930 89,498 391,035 383,285
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
            - blockquote [ref=e108]: Total net sales (1)
          - group [ref=e109]:
            - generic "Extraction limitations" [ref=e110] [cursor=pointer]
        - generic [ref=e111]:
          - generic [ref=e112]:
            - generic [ref=e113]: "2"
            - strong [ref=e114]: apple-fy24.pdf
          - paragraph [ref=e115]: Parent passage e4791e150178451085a2bb5089d6353e:parent:5
          - paragraph [ref=e116]: CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Unaudited)
          - paragraph [ref=e117]: PDF original pages · Additional supplied evidence
          - generic "Original PDF pages" [ref=e118]:
            - link "Open page 3" [ref=e119] [cursor=pointer]:
              - /url: /api/files/e4791e150178451085a2bb5089d6353e/original?revision=de76f69979fcece2f1d55a531cbd865aaa5df1fb5a0ccafc9b3ad54453f9756f#page=3
          - blockquote [ref=e120]: "CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Unaudited) (In millions) Twelve Months Ended Cash, cash equivalents, and restricted cash and cash equivalents, beginning balances September 28, 2024 $ 30,737 September 30, 2023 $ 24,977 Operating activities: Net income 93,736 96,995 Adjustments to reconcile net income to cash generated by operating activities: Depreciation and amortization 11,445 11,519 Share-based compensation expense 11,688 10,833 Other (2,266) (2,227) Changes in operating assets and liabilities: Accounts receivable, net (3,788) (1,688) Vendor non-trade receivables (1,356) 1,271 Inventories (1,046) (1,618) Other current and non-current assets (11,731) (5,684) Accounts payable 6,020 (1,889) Other current and non-current liabilities 15,552 3,031 Cash generated by operating activities 118,254 110,543 Investing activities: Purchases of marketable securities (48,656) (29,513) Proceeds from maturities of marketable securities 51,211 39,686 Proceeds from sales of marketable securities 11,135 5,828 Payments for acquisition of property, plant and equipment (9,447) (10,959) Other (1,308) (1,337) Cash generated by investing activities 2,935 3,705 Financing activities: Payments for taxes related to net share settlement of equity awards (5,441) (5,431) Payments for dividends and dividend equivalents (15,234) (15,025) Repurchases of common stock (94,949) (77,550) Proceeds from issuance of term debt, net - 5,228 Repayments of term debt (9,958) (11,151) Proceeds from/(Repayments of) commercial paper, net 3,960 (3,978) Other (361) (581) Cash used in financing activities (121,983) (108,488) Increase/(Decrease) in cash, cash equivalents, and restricted cash and cash equivalents (794) 5,760 Cash, cash equivalents, and restricted cash and cash equivalents, ending balances $ 29,943 $ 30,737 Supplemental cash flow disclosure: Cash paid for income taxes, net $ 26,102 $ 18,679"
          - group [ref=e121]:
            - generic "Extraction limitations" [ref=e122] [cursor=pointer]
        - generic [ref=e123]:
          - generic [ref=e124]:
            - generic [ref=e125]: "3"
            - strong [ref=e126]: apple-fy24.pdf
          - paragraph [ref=e127]: Chunk e4791e150178451085a2bb5089d6353e:child:11
          - paragraph [ref=e128]: CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)
          - paragraph [ref=e129]: PDF original pages · Additional supplied evidence
          - generic "Original PDF pages" [ref=e130]:
            - link "Open page 1" [ref=e131] [cursor=pointer]:
              - /url: /api/files/e4791e150178451085a2bb5089d6353e/original?revision=de76f69979fcece2f1d55a531cbd865aaa5df1fb5a0ccafc9b3ad54453f9756f#page=1
          - blockquote [ref=e132]: "Cost of sales: Products 44,566 42,586"
          - generic [ref=e133]:
            - paragraph [ref=e134]: Separately located table column header
            - blockquote [ref=e135]: Three Months Ended
          - generic [ref=e136]:
            - paragraph [ref=e137]: Separately located table column header
            - blockquote [ref=e138]: Twelve Months Ended
          - generic [ref=e139]:
            - paragraph [ref=e140]: Separately located table column header
            - blockquote [ref=e141]: September 28, 2024
          - generic [ref=e142]:
            - paragraph [ref=e143]: Separately located table column header
            - blockquote [ref=e144]: September 30, 2023
          - generic [ref=e145]:
            - paragraph [ref=e146]: Separately located table column header
            - blockquote [ref=e147]: September 28, 2024
          - generic [ref=e148]:
            - paragraph [ref=e149]: Separately located table column header
            - blockquote [ref=e150]: September 30, 2023
          - group [ref=e151]:
            - generic "Extraction limitations" [ref=e152] [cursor=pointer]
  - contentinfo [ref=e153]:
    - generic [ref=e154]: Keep your sources close.
    - generic [ref=e155]: TXT, Markdown and PDF knowledge base
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