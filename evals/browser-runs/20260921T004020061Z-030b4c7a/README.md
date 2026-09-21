# Final local MVP browser acceptance

Real OpenAI providers, production application, built UI and API on one origin, isolated data directory. Implementation: `689d49c8b8bc6100451d85d6a55e82749b094726`. Answer/resolution model: `gpt-4.1`; embeddings: `text-embedding-3-small`. No automatic test retries.

Result: one workflow passed in 26.2 seconds overall (24.0-second test). Six TXT uploads, eight completed answers, one cancelled turn, one deletion. The completed answers cover weekday/weekend hours, refusal after deletion, an embedding concept, printer instructions in 2025, the 2025 price follow-up, conflicting 2026 notices and an unknown personal balance. Semantic fixture assertions passed, and Codex inspected all eight answers and the screenshot. Zero browser page errors were recorded.

- [Raw acceptance log](acceptance.json)
- [Complete final conversation and sources](mvp-conversation.json)
- [Final screenshot](mvp-acceptance.png)
- [History before deletion](conversation-before-deletion.json)
- [History after deletion](conversation-after-deletion.json)

This is synthetic functional acceptance, not an independent answer-quality benchmark. See the [full release evaluation](../../analyses/2026-09-21-mvp-release.md) for the separate 25-question corpus findings and known failures.
