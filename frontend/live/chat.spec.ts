import { execFileSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { expect, test } from "@playwright/test";
import type { SavedConversation } from "../src/types";

const fixtures = [
  {
    name: "cedar-library-hours.txt",
    text: "Cedar Library visitor guide.\nCedar Library closes at 5 PM Monday through Friday.\nCedar Library closes at 7 PM on Saturday and Sunday.\nVisitors must bring their library card.\nThe quiet room is on the second floor.\n",
  },
  {
    name: "cedar-garden.txt",
    text: "Cedar Garden planting guide.\nPlant basil in well-drained soil. Water the soil when the top layer is dry. Place pots near a sunny window.\nThis document does not describe any library or its opening hours.\n",
  },
];

const acceptanceFixtures = [
  { name: "learning-notes.txt", text: "Study notes: vector retrieval.\nAn embedding represents text as a numeric vector. Vector retrieval compares a question vector with document vectors to find related passages. Similarity does not prove that a passage supports an answer.\n" },
  { name: "maple-printer-2025.txt", text: "Maple printer guide, academic year 2025.\nTo print, sign in to the Maple print portal, upload a PDF, and release the job using your student card. Black-and-white printing costs 0.08 USD per page in 2025.\n" },
  { name: "maple-printer-2026-a.txt", text: "Maple printer notice A, academic year 2026.\nBlack-and-white printing costs 0.10 USD per page in 2026. This notice does not establish priority over other notices.\n" },
  { name: "maple-printer-2026-b.txt", text: "Maple printer notice B, academic year 2026.\nBlack-and-white printing costs 0.20 USD per page in 2026. This notice does not establish priority over other notices.\n" },
];

test("live provider browser acceptance in an isolated library", async ({
  page,
  request,
}) => {
  const directory = process.env.LIVE_EVIDENCE_DIR!;
  await mkdir(directory, { recursive: true });
  const browserErrors: string[] = [];
  page.on("pageerror", (error) => browserErrors.push(error.message));
  const steps: { name: string; observed_at: string; details?: unknown }[] = [];
  const record = (name: string, details?: unknown) =>
    steps.push({ name, observed_at: new Date().toISOString(), details });
  const report = {
    started_at: new Date().toISOString(),
    git_commit: execFileSync("git", ["rev-parse", "HEAD"], {
      encoding: "utf8",
    }).trim(),
    working_tree_dirty: !!execFileSync("git", ["status", "--porcelain"], {
      encoding: "utf8",
    }).trim(),
    provider_mode: "real OpenAI, unmodified production application",
    configured_answer_model: "gpt-4.1-nano",
    configured_embedding_model: "text-embedding-3-small",
    scope:
      "One synthetic browser workflow, not a quality benchmark. No automatic retries.",
    fixtures: [...fixtures, ...acceptanceFixtures],
    steps,
    browser_errors: browserErrors,
    status: "running",
  };
  const save = async () =>
    writeFile(
      join(directory, "acceptance.json"),
      JSON.stringify(report, null, 2) + "\n",
    );
  await save();
  try {
    // Never delete pre-existing data; the live configuration must supply an empty store.
    expect(await (await request.get("/api/files")).json()).toEqual([]);
    await page.goto("/");
    for (const fixture of fixtures) {
      await page
        .getByLabel("Choose TXT file")
        .setInputFiles({
          name: fixture.name,
          mimeType: "text/plain",
          buffer: Buffer.from(fixture.text),
        });
      await expect(page.getByText(`${fixture.name} is ready.`)).toBeVisible();
      record("upload-ready", { file_name: fixture.name });
    }
    const composer = page.getByRole("textbox", {
      name: "Ask about your documents",
    });
    async function ask(question: string, completedCount: number) {
      await composer.fill(question);
      await composer.press("Enter");
      await expect(page.getByText("Completed", { exact: true })).toHaveCount(
        completedCount,
      );
      expect(await composer.inputValue()).toBe("");
    }
    await ask(
      "When does Cedar Library close on weekdays? Reply briefly with a citation.",
      1,
    );
    const id = await page.evaluate(() =>
      localStorage.getItem("knowledgebase.conversationId"),
    );
    expect(id).toBeTruthy();
    const history = async (): Promise<SavedConversation> => {
      const response = await request.get(`/api/conversations/${id}`);
      expect(response.ok()).toBe(true);
      return response.json();
    };
    record("first-answer-completed", await history());
    await page
      .getByRole("button", {
        name: /^View source \d+: cedar-library-hours.txt$/,
      })
      .first()
      .click();
    const evidence = page.getByRole("complementary", { name: "Evidence" });
    await expect(
      evidence.locator("blockquote").filter({ hasText: "5 PM" }).first(),
    ).toBeVisible();
    record("citation-opens-original-excerpt");
    await ask("What about on Saturday?", 2);
    record("follow-up-completed", await history());
    await page.reload();
    await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
    await page.screenshot({
      path: join(directory, "completed-chat.png"),
      fullPage: true,
    });
    record("refresh-restored-two-turns");

    await composer.fill(
      "Explain every detail from the Cedar Library guide, then provide thirty short numbered reminders based only on those details. Cite your sources.",
    );
    await composer.press("Enter");
    await expect(page.getByText("Answering…", { exact: true })).toBeVisible();
    const partial = await page
      .getByRole("article", { name: "Assistant answer" })
      .last()
      .innerText();
    await page.getByRole("button", { name: "Stop", exact: true }).click();
    await expect(page.getByText("Interrupted", { exact: true })).toBeVisible();
    // Give the cancelled provider request time to unwind before inspecting persisted history.
    await page.waitForTimeout(1500);
    expect((await history()).messages).toHaveLength(4);
    record("cancelled-partial-not-saved", { visible_before_stop: partial });
    await page.reload();
    await expect(page.getByText("Completed", { exact: true })).toHaveCount(2);
    await expect(page.getByText("Interrupted", { exact: true })).toHaveCount(0);
    await writeFile(
      join(directory, "conversation-before-deletion.json"),
      JSON.stringify(await history(), null, 2) + "\n",
    );

    const files = await (await request.get("/api/files")).json();
    const removed = files.find(
      (file: { file_name: string }) => file.file_name === fixtures[0].name,
    );
    await page
      .getByRole("button", { name: `${fixtures[0].name} Ready` })
      .click();
    await page.getByRole("button", { name: "Delete", exact: true }).click();
    await page
      .getByRole("button", { name: "Delete file", exact: true })
      .click();
    await expect(
      page.getByText("File and indexed content deleted."),
    ).toBeVisible();
    await page
      .getByRole("button", {
        name: /^View source \d+: cedar-library-hours.txt$/,
      })
      .first()
      .click();
    await expect(
      evidence.getByText("Source deleted · Historical excerpt").first(),
    ).toBeVisible();
    await expect(
      evidence.locator("blockquote").filter({ hasText: "5 PM" }).first(),
    ).toBeVisible();
    record("delete-retained-historical-evidence");
    await ask(
      "Using only the documents currently in my library, when does Cedar Library close on Saturday?",
      3,
    );
    const after = await history();
    const latest = after.messages.at(-1)!;
    expect(
      latest.sources?.every((source) => source.file_id !== removed.file_id),
    ).toBe(true);
    record("post-deletion-answer", latest);
    await writeFile(
      join(directory, "conversation-after-deletion.json"),
      JSON.stringify(after, null, 2) + "\n",
    );
    await page.screenshot({
      path: join(directory, "after-deletion.png"),
      fullPage: true,
    });
    for (const fixture of acceptanceFixtures) {
      await page.getByLabel("Choose TXT file").setInputFiles({
        name: fixture.name, mimeType: "text/plain", buffer: Buffer.from(fixture.text),
      });
      await expect(page.getByText(`${fixture.name} is ready.`)).toBeVisible();
      record("acceptance-upload-ready", { file_name: fixture.name });
    }
    const scenarios = [
      "According to my study notes, what is an embedding, how does vector retrieval use it, and does similarity prove answer support?",
      "How do I use the Maple printer in academic year 2025?",
      "How much does it cost per black-and-white page that year?",
      "The two Maple printer notices for 2026 list different prices. What does each say, and can these sources establish which price applies?",
      "What is the exact remaining balance of my personal Maple printing account?",
    ];
    for (const [index, question] of scenarios.entries()) {
      await ask(question, index + 4);
      record("mvp-answer", (await history()).messages.at(-1));
    }
    await writeFile(join(directory, "mvp-conversation.json"), JSON.stringify(await history(), null, 2) + "\n");
    await page.screenshot({ path: join(directory, "mvp-acceptance.png"), fullPage: true });
    expect(browserErrors).toEqual([]);
    report.status = "passed";
  } catch (error) {
    report.status = "failed";
    record("failed", {
      message: error instanceof Error ? error.message : String(error),
    });
    throw error;
  } finally {
    record("finished");
    await save();
    console.log(`Live acceptance evidence: ${directory}`);
  }
});
