# KnowledgeBase v1 Evaluation Plan

## Purpose

Status: development comparisons and default functional acceptance are recorded
in the [release summary](release-summary.md); the implementation is merged at
`483a156`. This document retains the evaluation protocol, including independent
held-out and human-review requirements that remain open. Its purpose is to establish
which changes improve evidence retrieval, context coverage and supported answers,
and measure their latency and cost. Retain the [MVP release report](../../evals/analyses/2026-09-21-mvp-release.md)
as historical evidence rather than assigning its scores to v1.

## Data and Comparison Rules

Use the frozen NYU TXT corpus and existing questions as a development baseline.
Add Markdown fixtures with headings, lists, code, and tables, plus questions about
exact identifiers, paraphrases, adjacent qualifications, follow-ups, and missing
information. Store gold evidence as source spans rather than configuration-specific
chunk IDs so chunking strategies remain comparable.

Separate development questions used to tune settings from a new held-out set.
Freeze the latter's questions, references, and review rubric before final selection;
do not tune against its failures and continue calling it held-out. Follow-up cases
must retain their full conversation sequence. Gold answers and evidence annotations
must never enter the generation prompt.

For each comparison, hold corpus, question set, generation model/prompt, embedding
model, and all settings outside the stated intervention fixed. Record code,
configuration, corpus, and dataset hashes. Index each run in a separate data
directory. Compare saved outputs rather than rerunning an old configuration under
the same label. Existing MVP results are not directly comparable if these inputs differ.

## Baselines and Experiments

Run the following development comparisons. Every label identifies a complete
configuration; staged improvements alone do not isolate interactions.

| Label | Configuration | Question answered |
| --- | --- | --- |
| A: MVP | Existing fixed-character chunks and vector retrieval | What does the current application retrieve and answer on this frozen set? |
| B: Structural flat | Structure/sentence chunks, vector retrieval, child text as evidence | Does boundary-aware chunking help relative to A? This compares the complete chunking configurations, including their sizes. |
| C: Parent expansion | The same children and candidate ranking as B, with parent expansion | Does surrounding context improve support or add distracting content? |
| D: Hybrid | C plus BM25 and RRF | Does lexical retrieval plus fusion recover missed evidence compared with C? |
| E: Reranked | D plus reranking | Does reranking improve final evidence selection compared with D? |
| F: Semantic | E with semantic child boundaries inside the same parent regions | Does embedding-based splitting justify its ingestion cost compared with E? |

Match B's children to C's children exactly; B simply does not expand them during
answer assembly. Hold the final evidence token budget fixed across comparisons
and report actual usage, since parent expansion changes context size and count.
For D versus E, retain the same fused candidate pool and child selection count.

On E's fixed child index, also compare BM25-only, vector-only, and RRF candidate
lists at the same candidate limit to isolate route contributions before reranking.
Record both child-level recall and evidence retained after parent expansion.
Do not attribute an answer-quality change to BM25 alone when the experiment also
changes fusion or candidate coverage.

## Metrics and Artifacts

| Area | Record and interpret |
| --- | --- |
| Candidate retrieval | Annotated source-span coverage at each route, fusion, and rerank selection stage; specify candidate limits |
| Final context | Gold-span coverage after parent expansion and packing, unique parent count, actual evidence tokens, budget exclusions |
| Answer quality | Required points addressed, supported claims, quotation fidelity, missing-information handling, year and conflict preservation |
| Citations | Valid ID membership separately from whether the cited excerpt supports each claim |
| Runtime | Ingestion time; query resolution, embedding, retrieval, fusion, rerank, time to first answer token, and completion latency |
| Cost | Provider-reported token usage and charges when available; otherwise explicitly labeled estimates or unavailable values |
| Reliability | Request completion, index lifecycle, restoration, cancellation, and deletion results |

Union overlapping source spans before counting covered characters so duplicate
children or parents cannot inflate recall. Keep the existing annotated-character
and fully-covered-span measures distinct. More context can raise coverage without
improving answer quality; report both along with the context size.

Save the original question, resolved query, route candidates, scores/ranks, fused
pool, rerank results, selected children, included/excluded parents, exact model
evidence, answer, model settings, and scoring decisions. Do not overwrite failed
attempts. Distinguish missing telemetry from zero usage.

Repeat timing measurements under comparable conditions, record sample counts and
concurrency, and avoid treating a single run's latency difference as a reliable gain.
Report per-case changes and regressions in addition to aggregate values.

## Review and Release Gates

1. Pass relevant backend, frontend, build, and browser checks for implemented changes.
   Include source offsets, parent-child containment, RRF ties/missing routes,
   reranker identity mapping, budget exclusion, Ready-only search in both indexes,
   upload/restart/deletion lifecycle, and historical evidence rendering.
2. Verify the real-provider TXT and Markdown workflow, including source inspection,
   follow-up, refresh, cancellation, and deletion. UI assertions alone do not grade answers.
3. Complete the controlled development comparisons and publish the selected
   configuration with tradeoffs. Semantic chunking becomes the default only if its
   quality benefit justifies the measured extra cost; otherwise retain it as experimental.
4. Before opening held-out results, record acceptance criteria for evidence coverage,
   supported-answer regressions, latency, and cost based on development observations.
   Do not invent numerical targets now or choose them after seeing held-out scores.
5. Obtain independent human review of the held-out answer set against the frozen
   rubric, including known failure categories. Codex review remains labeled as such
   and does not substitute for independent human review. If review is unavailable,
   report semantic validation as pending.
6. Publish remaining misses, unsupported claims, configuration limits, and reviewer
   identity. Describe a functional release separately from any demonstrated quality gain.

An LLM judge may assist review only after calibration against human decisions.
The MVP's judge failures are a reason to retain auditable evidence and disagreements,
not to relabel automated scores as human approval.


### Delegated functional acceptance

When the user asks Codex to perform acceptance, Codex can execute the checks,
inspect every actual answer/source pair, record its reviewer identity and give a
functional merge recommendation. Do not require the user to do that work before
Codex can deliver a verdict. This remains model-assisted review; it does not
satisfy or impersonate independent human validation of broader semantic quality.
The [2026-09-25 delegated audit](../../evals/library-runs/20260925-v1-codex-acceptance/README.md)
uses criteria frozen before results and preserves its failed scope qualification.
Actual merge authority remains with the user.
