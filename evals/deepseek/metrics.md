# Metric definitions and experiment protocol

Keep three questions separate: did retrieval find sufficient evidence, did the
answer correctly use that evidence, and how long did the system take? A nearest
neighbor distance, matching filename, passing unit test or valid JSON response
does not by itself answer any of the other questions.

## Quality and retrieval

| Metric | Definition and denominator | Available here |
| --- | --- | --- |
| Answer-point accuracy | Mean of point scores / 2 within each graded answerable question, then mean across those questions | Offline human grade |
| Strict pass rate | Answers with all point scores and all applicable grounding/citation/abstention scores equal to 2, divided by all attempted cases | Human grade; withheld until every successful attempt is graded; request errors fail |
| Groundedness | Mean human grounding score / 2 over graded answers | Human grade; judge against retrieved evidence, not merely the gold answer |
| Citation support | Mean human citation score / 2 over applicable graded answers | Human grade; null entries excluded with denominator shown |
| Abstention quality | Mean abstention score / 2 over graded unanswerable cases | Human grade |
| Hallucination rate | Fraction of reviewed answers with at least one unsupported factual claim | Optional claim audit; do not infer directly from lexical matches |
| False-refusal rate | Answerable cases explicitly refused despite sufficient retrieved evidence / reviewed answerable cases | Optional human error label; requires inspection of retrieved evidence |
| Document MRR | Reciprocal rank of first retrieved document with an annotated gold passage, averaged over successful answerable questions | Automatic, named `document_mrr`; coarse document diagnostic only |
| Annotated character recall | For each gold span, union of covered character intervals / span length; average spans within each question, then questions | Automatic; overlaps count once |
| Full evidence recall | Fraction of annotated spans completely covered by the union of retrieved chunks; macro-average across questions | Automatic |
| All-evidence retrieval rate | Fraction of successful answerable questions for which every annotated span is fully covered | Automatic; useful for multi-document completeness |
| Exact-token coverage | Fraction of listed exact answer strings found in answer text | Automatic for annotated cases only; diagnostic, never a correctness score |
| Recall@k / MRR@k at chunk relevance level | Annotate relevant/supporting chunks for a fixed chunking configuration, then score retrieval rankings | Requires additional qrels or a retrieval-only adapter; not claimed by this client |
| nDCG@k | Discounted cumulative graded relevance divided by ideal DCG | Requires manually graded ranked candidates; not calculated from filename matches |
| Context precision | Relevant retrieved context divided by all retrieved context, with explicit chunk- or character-level relevance rules | Optional manual relevance audit |
| Paraphrase consistency | Same-family semantic and keyword variants agree in correctness and factual answer | Group by `family_id`; inspect factual agreement, not verbatim matching |
| Temporal/source attribution | Correct historical scope, API family, and recognition of later clarifications | Dedicated historical/conflict categories plus human scoring notes |
| Multi-turn resolution accuracy | Correct standalone interpretation of follow-up, then correct grounded answer | Compare saved `retrieval_question` with `standalone_reference_question`; human review |

Gold evidence annotations are not exhaustive relevance judgments. For example,
the homepage and a dedicated Python sample repeat code, and the FAQ repeats
keep-alive behavior. A valid alternative source can yield low annotated recall
without a factual answer failure. Report both and inspect disagreements.

The current HTTP API returns chunk text but not offsets. This client maps an
excerpt back only when it appears **exactly once** in the known source file.
Absent or ambiguous text yields null span-recall metrics for that question and
an explicit uncertainty flag. It never guesses the first matching offset to
inflate recall. Known document identity can still contribute to document MRR.
Unanswerable cases have null retrieval metrics; their related background is not
a positive retrieval target.

## Latency, throughput and reliability

| Metric | Measurement boundary | Important qualification |
| --- | --- | --- |
| End-to-end latency | Client request dispatch to application `complete` event | Includes HTTP, query resolution, retrieval, generation and persistence |
| TTFT / first answer-text latency | Request dispatch to first nonempty `answer_delta` | `start`, `sources`, keep-alive and reasoning-only provider events are not answer text |
| Sources-ready latency | Dispatch to `sources` event | Includes transport, queueing and resolution; not pure vector-search latency |
| P50 / P95 / P99 | Nearest-rank quantile over successful requests with a recorded value | Always show sample count; 42 samples cannot estimate P99 reliably |
| Completion rate | Successful complete events / all attempts | HTTP failures, timeouts, incomplete streams and blocked follow-ups remain failures |
| Throughput | Successful requests / full run wall-clock seconds | Excludes ingestion and human grading; compare the same workload and concurrency |
| Ingestion time | Per-file POST dispatch to ready response; aggregate full ingestion wall time | Includes decoding, chunking, embedding, indexing, storage and HTTP |
| Repeat stability | Per-case spread of latency and quality across repetitions | Keep all repetitions; repeated questions can benefit from provider caching |
| Pure stage timings | Separate query rewriting, query embedding, vector search, prompt construction, model generation, persistence | Not exposed separately by this HTTP client; requires backend instrumentation |
| Output tokens/sec | Provider-reported output tokens divided by a precisely defined generation interval | Unavailable here; characters/sec is a different metric |
| Peak RSS and CPU | Sample the backend process and any relevant workers during each workload | External OS measurement required; record units, interval, PIDs and machine |
| Index size and chunk count | Inspect the isolated storage after ingestion | Requires a storage audit; measure before/after with same source corpus |
| Token usage and monetary cost | Actual embedding/query/resolver/answer usage × versioned provider rates, with cache hits/misses where available | Not exposed by the current app response; remain null, never inferred from latency |

Latencies from errors remain in raw attempt records but are excluded from success
quantiles. Also inspect failure duration and timeout count so a fast successful
subset does not hide slow failures. The full benchmark should include no
automatic retries; a retry study is a separate workload with attempt-level costs.

## Controlled comparisons

1. Freeze corpus, questions, model identifiers, prompts, generation settings and
   reviewer rubric. Record Git revision, configuration, machine and network.
2. Start with `quality-dev` at concurrency 1. Record a baseline before changing
   anything. Diagnose retrieval misses separately from answer-generation errors.
3. Change one factor per experiment: chunk size/overlap, top-k, model, or retrieval
   implementation. Re-ingest into a new isolated index when ingestion settings
   change. Use the same exact uploaded representation.
4. Run all compared configurations on the same questions. Report paired per-case
   changes, category-level regressions and aggregate scores. Counterbalance run
   order across repeated experiments to reduce time-of-day/provider effects.
5. Use the 42 latency cases for a first pass, then 5 repeated passes (210 requests)
   at concurrency 1. First-pass does not guarantee a cold provider cache. Provider
   cache state is unknown unless independently observed. Do not label this a true
   cold-cache benchmark just because the local process restarted.
6. Separately test concurrency 2 and 4, with fresh conversations and fixed
   per-request inputs. Measure quality as well as throughput and tail latency.
   Increased concurrency may cause provider queuing or failures.
7. Run the 12 multi-turn scenarios with sequential turns inside each conversation.
   Inspect topic changes, pronouns, mistaken prior answers, refusal of missing
   personal information and whether fresh evidence supports each answer.
8. After choosing settings on development data, use the frozen test split once
   for that iteration. Disclose fact/source overlap and public-data exposure.
   Repeated tuning against it turns it into another development set.

For uncertainty, bootstrap **fact families**, not individual paraphrase variants,
for quality comparisons. For repeated timings, preserve the question-level
grouping when resampling. Report confidence intervals only when actually
computed, with the method and number of samples; none are fabricated here.

## Candidate engineering hypotheses

These are experiments to run, not claims of improvements:

- A lexical component may improve retrieval of opaque call IDs, exact paths and
  very similar parameter names. Compare dense-only, lexical-only and hybrid at
  the same retrieval budget, once those implementations exist.
- Larger chunks may preserve API field names together with their descriptions,
  improving completeness while increasing context size and latency.
- Smaller chunks may help isolate a price row but lose the header identifying
  its model or per-million-token unit.
- Increasing top-k may recover all required pages for cross-document questions
  while introducing stale announcements and increasing unsupported synthesis.
- More selective date/API-family handling may improve historical and conflicting
  source questions, while an overly strict evidence gate may increase false refusals.

Do not assign arbitrary passing thresholds to this first benchmark and present
them as validated requirements. Establish a baseline and agree on product targets,
then apply those targets to separately recorded results.
