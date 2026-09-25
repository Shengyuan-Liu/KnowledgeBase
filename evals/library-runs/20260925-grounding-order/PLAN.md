# Grounding instruction placement — frozen verification

The explicit attribution/status instructions still failed in the preceding
[recorded attempt](../20260925-source-attribution/README.md). Check whether placing
the SAME developer instructions after the user question/evidence improves the
observed behavior. This is a two-message order change, shared by complete and
streaming generation. Message content and roles are unchanged. Source excerpts
remain user data; they are never promoted to developer instructions. No new rule,
extra model call, source filtering, answer repair or changed model/defaults.

Use the same five cases and exact user/evidence messages, corpus, annotations,
configuration and developer prompt from the immediately preceding attempt. Freeze
hashes before calls. Generate once per case, GPT-4.1, timeout 60 seconds, no retries,
concurrency one, no warmup. No ingestion, retrieval, embedding or paid judge calls.
Record all responses, deltas, provider usage/revision, errors and timings. No
same-configuration retry to select a better response.

Apply the unchanged [functional rubric](../20260925-v1-codex-acceptance/PLAN.md)
and [five-case gates](../20260925-source-attribution/PLAN.md): every required fact
fully correct with source-supported scope; no unsupported factual claims/advice;
all associated citations support their claims; local supporting citation coverage
>=80% overall with at least one citation per factual answer; both unavailable
cases appropriately abstain, no incorrect refusal on answerable cases. Inspect
all claims including repetitions/extras; preserve exact quotes and source offsets.
Codex is the implementer/reviewer, not an independent human. Prior conservative
scope judgments are not relaxed. These are known regression questions, not new
held-out accuracy or a fresh full-service acceptance.

Operational gates: five successful calls with valid citation IDs, generation
completion mean <=10 s / nearest-rank P95 <=20 s, first nonempty generation delta
P95 <=10 s, input <=12000 tokens/request. Report median P50, nearest-rank P95,
N=5, provider waiting included, no service/HTTP/ingestion timings. Full metric
inventory includes inherited retrieval provenance, throughput and provider tokens;
billed cost unavailable if not returned. Single historical samples do not isolate
causal effects or establish universal model compliance.

If all gates pass, combine with the recorded service/backend/UI checks to recommend
the existing default functional v1 scope, with experimental options opt-in and
broader semantic reliability limitations disclosed. Otherwise preserve the failure.
No criterion changes, discarded attempts or automatic merge. Explicit user merge
approval remains required.
