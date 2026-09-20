# Real-provider browser acceptance

A single isolated browser run passed on September 20, 2026, from 22:56:45 to
22:56:56 UTC. It exercised the production React/Vite/FastAPI stack, SQLite/Chroma,
and real OpenAI clients configured for `gpt-4.1-nano` and `text-embedding-3-small`.
The service code was commit `e16b892e436f5e1d0990b07ffd0f99041c105ec4`. The working
tree was dirty because the new live-test harness was being added; production
application code was unchanged from that commit.

This is a functional acceptance run with two synthetic TXT documents, not a RAG
quality benchmark or proof about current NYU policy. The existing user library and
servers on ports 8000/5173 were untouched. Dedicated servers used 8001/5174 and an
isolated ignored `data/live-browser/` directory, then shut down after the test.

## Observations

| Step | Observed outcome |
| --- | --- |
| Upload | Both synthetic files reached Ready after real embedding calls |
| Initial question | Answer correctly gave the fixture's weekday closing time: 5 PM, with citation [1] |
| Evidence navigation | Clicking the citation displayed the original library passage |
| Follow-up | “What about on Saturday?” resolved to “What are the Saturday hours for Cedar Library?” and answered 7 PM |
| Refresh | Both completed turns and evidence restored from the server |
| Cancellation | Visible incremental text was stopped; four saved messages remained, and the partial turn was absent after refresh |
| Delete | The hours document was removed; old excerpts remained readable with a deleted-source label |
| New question after deletion | Retrieved only the remaining garden document; the model stated that the current sources cannot determine Saturday closing time |
| Browser errors | No page errors were recorded |

The workflow made two successful uploads and four chat submissions: three
completed answers and one cancelled stream. Follow-up resolution and retrieval
also make provider calls; these counts are UI operations, not provider-request or
billing counts. Token usage and cost were not measured.

The automated test verifies the workflow and source exclusion. The weekday,
Saturday, and post-deletion answer semantics were additionally inspected by Codex
against the synthetic fixture text. This is not a human rating or LLM-judge score.

## Evidence

- [Acceptance log and exact fixtures](acceptance.json)
- [Saved conversation before deletion](conversation-before-deletion.json)
- [Saved conversation after deletion](conversation-after-deletion.json)
- [Completed conversation screenshot](completed-chat.png)
- [Post-deletion screenshot](after-deletion.png)

The raw JSON preserves the observations from this run. Reproduce with
`make test-browser-live`; that explicitly invokes paid model calls and creates a
new evidence directory. There are no automatic test retries.
