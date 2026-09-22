# Interrupted Markdown Acceptance Attempt

Four files were successfully uploaded using real embeddings. The harness then
failed before any answer-generation case: Playwright re-evaluated its configuration
in the worker and generated a different run ID from the server's run ID.

The recorded `settings.data_dir` is the incorrectly inferred directory. The actual
isolated server directory was `data/live-browser/20260922T222036728Z-63c76038`.
No user library was accessed. This is a harness failure, not a RAG quality result.
The original [acceptance record](acceptance.json) is retained unchanged.

The live configuration now carries its generated ID through `LIVE_RUN_ID` so the
server and worker refer to the same directory. The next attempt uses a fresh index.
