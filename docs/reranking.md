# Child Reranking

Status: integrated on `v1` for JSON chat, streamed chat, CLI, and evaluation.
Enable it with `RERANK_ENABLED=true` under hybrid retrieval and restart. The
default is `false` so the original hybrid route remains an explicit control.

This first baseline uses the existing OpenAI Responses client with a configurable
model, rather than introducing a local model download or another provider key.
All entry points use `RERANK_MODEL` when set and otherwise `ANSWER_MODEL`.
This is an LLM relevance-scoring baseline, not a trained cross-encoder or a claim
that the chosen model is optimal for ranking, latency, or cost.

## Input and output

[`rerank()`](../knowledgebase/rag/reranking.py) takes:

- The retrieval question, after any follow-up resolution performed by its caller.
- `RerankCandidate` objects: a `FusedMatch` plus exact child `text` and separately
  supplied `heading_path`. Original IDs, route scores, and RRF ranks remain intact.
- A `RerankerClient`, whose SDK connection is owned by the caller.
- Child selection `top_k`, a scored-candidate limit, input-text token budget,
  and tokenizer.

It sorts the input by RRF rank and child ID and scores the leading bounded window.
Each question uses one provider request. The model receives the question, child
IDs, headings, and text. Existing numeric ranks and scores are withheld from the
model prompt but retained in the result. Question and passage content are marked
as untrusted data; a relevant heading or link alone is not the missing evidence.

Scores use an ordinal 0–3 rubric:

| Score | Meaning |
| --- | --- |
| 0 | Unrelated |
| 1 | Topic mention or link, without a requested fact |
| 2 | Partial or indirect support requiring interpretation |
| 3 | Explicitly supplies at least one requested fact |

These scores are not calibrated probabilities or judgments about a generated
answer. A passage can be highly relevant to one side of a comparison without
containing the full answer.

The result is a `RerankResult` with:

- `candidates`: the entire scored window, including original text and route metadata.
- `matches`: all scored IDs, in decreasing relevance order. Each match retains its
  original `rank`/`rrf_score` and adds independent `rerank_rank`/`rerank_score` fields.
- `selected`: a convenience property for `matches[:top_k]`. This property is not
  duplicated in JSON; serialized `matches` and `top_k` reconstruct the selection.
- The question, model, prompt version, configured limits, tokenizer, and input-text
  token count, so the scored input and selection can be inspected later.

Equal relevance scores keep RRF rank, then child ID. Sibling children remain
separate; parent expansion and deduplication belong to the subsequent pipeline.
No score threshold or automatic abstention policy is introduced in this module.

## Structured output and failure behavior

The adapter uses the SDK's Pydantic structured-output helper, following the
[official OpenAI guide](https://developers.openai.com/api/docs/guides/structured-outputs).
For each request, it creates an object schema whose required keys are exactly the
candidate IDs. Each value is an integer in [0, 3]. Local field names use safe aliases
so IDs do not become Python attribute names.

This addresses an observed prototype failure: an unconstrained list returned only
19 scores for 20 CPT candidates. The required-key response shape makes coverage
part of the output schema. The SDK validates the shape; the module also checks the
returned ID set against its actual window before applying a ranking. There is no
response repair, invented score, automatic RRF fallback, or module-level retry.
SDK transport retries remain the caller's existing configuration.

An empty window returns an empty result without a provider call. The input budget
counts both developer instructions and the exact serialized question/candidate
message text using the configured tokenizer. Provider message framing, schema,
and output tokens are excluded: this count is not a model context-window or
billing guarantee. Input exceeding the budget raises before calling the model;
source text is never silently shortened. Provider truncation is disabled.
Incomplete, refused, malformed, or failed requests surface as errors.

## Runtime integration

The service resolves follow-ups, retrieves BM25/vector candidates, applies RRF,
scores its bounded leading window, selects top-k children, then expands and
deduplicates parents before packing whole evidence regions. Reranking can change
which parents fit the budget. Siblings still consume child selection slots; no
additional children are backfilled after deduplication or budget exclusion.

Each selected child and source retains `fusion` and an optional `rerank` match.
A parent inherits the metadata of its highest rerank-ranked selected child.
`retrieval.rerank` preserves every scored input and output, and
`retrieval.rerank_seconds` measures that stage. Completed JSON/SSE answers persist
these diagnostics with evidence snapshots. History remains readable after restart
and source deletion; older snapshots have null rerank fields. The frontend debug
view shows relevance and rank separately from RRF and vector distance. Its
answer-preparation time includes retrieval, reranking, and generation.

A scoring error stops the current answer: JSON returns its existing processing
error; SSE emits `error` without `complete`. No exchange is saved. Disconnecting
while scoring is in progress prevents generation and persistence; the synchronous
provider request may still finish in its abandoned worker. There is no silent
hybrid fallback. An empty Ready library makes no embedding or scoring request.

CLI and evaluation accept `--rerank` / `--no-rerank` and `--rerank-model`; the
evaluation runner also exposes candidate and input-token limits. All resolved
options and the effective scoring model are saved in evaluation metadata.
Changing these settings does not require reindexing. Vector-only retrieval
requires reranking to be disabled.

```sh
uv run --locked python -m evals.evaluate run --label "Hybrid control" --retrieval-strategy hybrid --no-rerank
uv run --locked python -m evals.evaluate run --label "Hybrid with rerank" --retrieval-strategy hybrid --rerank
```

These commands make paid provider calls. See [configuration](configuration.md)
for `.env` defaults and precedence.

## Low-level example

```python
from openai import OpenAI

from knowledgebase.config import Settings
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.rag.reranking import rerank
from knowledgebase.schemas import RerankCandidate

settings = Settings()
# The caller loads these canonical chunks and fused matches for eligible files.
candidates = [
    RerankCandidate(
        **hit.model_dump(), text=chunks_by_id[hit.chunk_id].text,
        heading_path=chunks_by_id[hit.chunk_id].heading_path,
    )
    for hit in fused_matches
]
with OpenAI(
    api_key=settings.openai_api_key, base_url=settings.openai_base_url,
    timeout=settings.openai_timeout_seconds, max_retries=settings.openai_max_retries,
) as sdk:
    client = RerankerClient(sdk, settings.rerank_model or settings.answer_model)
    result = rerank(
        question, candidates, client, top_k=settings.retrieval_top_k,
        candidate_limit=settings.rerank_candidate_limit,
        max_input_tokens=settings.rerank_max_input_tokens,
        encoding_name=settings.chunk_tokenizer,
    )
    for hit in result.selected:
        print(hit.chunk_id, hit.rerank_score, hit.rerank_rank, hit.rank)
```

The example assumes structured children; legacy flat chunks use an empty heading
path. Loading Settings reads the existing ignored `.env`, never `.env.local`.
The settings template in [.env.example](../.env.example) leaves reranking disabled.

## Verification

Run `uv run --locked python -m pytest tests/test_reranking.py tests/test_reranker_provider.py tests/test_rerank_pipeline.py tests/test_chat_streaming.py`.
Tests cover identity-based mapping, preserved source and route metadata, full result
serialization, RRF-window selection, stable ties, empty input, exact budget
boundaries, missing/duplicate scores, and error propagation. Mock HTTP tests use
the actual installed SDK to check required-ID schemas, parsing, and refusal handling.

The [live four-case probe](../evals/rerank-runs/20260923T234002Z-required-scores/README.md)
and its [initial failed attempt](../evals/rerank-runs/20260923T233640Z-standalone/README.md)
preserve scores, exact inputs, duration, and usage. The
[18-question paired integration run](../evals/library-runs/20260924T000238Z-rerank/README.md)
checks parent packing, supplied evidence, answers, and end-to-end latency.
Offline integration tests cover API JSON/SSE, CLI and evaluation configuration,
resolved follow-ups, budgets, Ready filtering, restart/deletion history, provider
errors, and cancellation. Desktop/mobile browser tests verify visible ranks and
restored evidence. These checks do not establish general model quality.
