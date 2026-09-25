# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: chat.spec.ts >> stopping keeps partial output locally and does not save an unfinished turn
- Location: e2e/chat.spec.ts:109:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Interrupted', { exact: true })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText('Interrupted', { exact: true }) with timeout 5000ms
  - waiting for getByText('Interrupted', { exact: true })

```

```yaml
- banner:
  - link "Knowledge Base":
    - /url: /
  - text: A little clarity, from your own documents. Personal workspace
- complementary "Library 1":
  - heading "Library 1" [level=2]
  - paragraph: Your documents, in one place
  - textbox "Search files":
    - /placeholder: Search files…
  - list "Files":
    - listitem:
      - button "hours.txt Ready":
        - text: TXT
        - strong: hours.txt
        - text: Ready
  - status
  - button "Upload file"
  - paragraph: TXT and Markdown · UTF-8 · Indexed for search
- main:
  - heading "Chat" [level=1]
  - paragraph: Grounded in your library
  - button "New chat"
  - text: First question
  - article "Assistant answer":
    - text: Knowledge Base
    - status: Completed
    - text: The library closes at 5 PM.
    - 'button "View source 1: hours.txt"': "[1]"
    - group: Sources (1 retrieved passages)
    - button "View evidence"
    - group: Debug details
  - text: Stop this question
  - article "Assistant answer":
    - text: Knowledge Base
    - status: Completed
    - text: The library closes at 5 PM.
    - 'button "View source 1: hours.txt"': "[1]"
    - group: Sources (1 retrieved passages)
    - button "View evidence"
    - group: Debug details
  - button "Jump to latest"
  - textbox "Ask about your documents":
    - /placeholder: Ask about your documents…
  - button "Send question" [disabled]
  - paragraph: Enter to send · Shift+Enter for a new line · Check the sources.
- complementary "Evidence":
  - heading "Evidence" [level=2]
  - paragraph: Sources for the selected answer
  - paragraph: Original excerpts supplied to this answer. A citation does not guarantee support.
  - text: "1"
  - strong: hours.txt
  - paragraph: Parent passage 72966c27acbc455fb9914feb7034d9d1:parent:0
  - paragraph: Lines 1–1 · Cited in this answer
  - blockquote: The library closes at 5 PM.
- contentinfo: Keep your sources close. TXT and Markdown knowledge base
```

# Test source

```ts
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
  75  |     }
  76  |     if (width < 768) await page.getByRole("button", { name: /Library/ }).click();
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
> 127 |   await expect(page.getByText("Interrupted", { exact: true })).toBeVisible();
      |                                                                ^ Error: expect(locator).toBeVisible() failed
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