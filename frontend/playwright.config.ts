import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:5174",
    headless: true,
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command:
        ".venv/bin/python -m uvicorn frontend_server:app --app-dir tests --host 127.0.0.1 --port 8001",
      cwd: "..",
      env: { PYTHONPATH: "." },
      url: "http://127.0.0.1:8001/api/files",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --port 5174",
      env: { KNOWLEDGEBASE_API_PROXY: "http://127.0.0.1:8001" },
      url: "http://127.0.0.1:5174",
      reuseExistingServer: false,
    },
  ],
});
