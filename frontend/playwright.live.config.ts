import { randomUUID } from "node:crypto";
import { resolve } from "node:path";
import { defineConfig } from "@playwright/test";

const runId = process.env.LIVE_RUN_ID ?? `${new Date().toISOString().replace(/[-:.]/g, "")}-${randomUUID().slice(0, 8)}`;
process.env.LIVE_RUN_ID = runId;
const evidenceDir = resolve("../evals/browser-runs", runId);
process.env.LIVE_EVIDENCE_DIR = evidenceDir;

export default defineConfig({
  testDir: "./live",
  testMatch: "chat.spec.ts",
  workers: 1,
  retries: 0,
  timeout: 180_000,
  expect: { timeout: 60_000 },
  outputDir: resolve("test-results/live", runId),
  use: {
    baseURL: "http://127.0.0.1:8001",
    headless: true,
    viewport: { width: 1440, height: 900 },
  },
  webServer: [
    {
      command:
        ".venv/bin/python -m uvicorn knowledgebase.api.app:create_app --factory --host 127.0.0.1 --port 8001",
      cwd: "..",
      env: { DATA_DIR: resolve("../data/live-browser", runId) },
      url: "http://127.0.0.1:8001/api/files",
      reuseExistingServer: false,
    },
  ],
});
