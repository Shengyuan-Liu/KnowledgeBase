# Local Cross-Encoder Reranking

Status: integrated on `v1` for JSON chat, streamed chat, CLI, and evaluation.
Enable with `RERANK_ENABLED=true` under hybrid retrieval and restart. The shared
switch defaults to `false`; the active local `.env` enables it.

## Model and input

The default is [BAAI/bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3),
a dedicated multilingual sequence-classification cross-encoder. It jointly reads
a question and a passage, then returns a relevance logit. It does not generate
an answer or a structured list of scores. The implementation uses the model
publisher's Transformers sequence-classification interface with PyTorch.

[`RerankerClient`](../knowledgebase/providers/reranker.py) loads its tokenizer
and weights once when an enabled application starts. The first run downloads the
model to the standard Hugging Face cache (about 2.3 GB of weights); subsequent
runs reuse the cache. No reranking API key is required. Embeddings and answers
continue to use the configured OpenAI connection. Startup loading time is separate
from query time. Disabling reranking avoids loading weights or importing PyTorch.

Each input pair contains:

1. The resolved retrieval question.
2. The exact child text, preceded by `Heading: A > B` and a blank line when a
   heading path exists. The prefix is scoring context only; canonical source text
   and answer evidence remain unchanged.

Old vector/BM25/RRF scores are not model inputs. All candidates retain their IDs,
exact text, and headings in the diagnostic trace. The model scores batches of four
by default in evaluation/inference mode. `RERANK_DEVICE=auto` selects CUDA, then
Apple MPS, then CPU according to availability; an explicit device is also allowed.
Shared-model inference is serialized because concurrent MPS forwards caused a
native Metal command-buffer assertion during live verification. Scoring-stage
time includes waiting for that lock. There is no automatic fallback after an error.

## Selection and score meaning

The pipeline resolves follow-ups, retrieves BM25/vector candidates, fuses by RRF,
scores its leading bounded window (default 20), selects the top five children,
then expands/deduplicates parents and packs whole regions into the evidence budget.
Higher raw logits rank first. Equal scores keep RRF rank, then child ID. Scores can
be negative or greater than three; they are not calibrated correctness probabilities.
No sigmoid, score threshold, backfill, or automatic abstention policy is applied.
Siblings still consume child slots, and parent expansion can still exceed the
context budget. An empty Ready library makes no embedding or scoring request.

This replaces the former `gpt-4.1` ordinal-scoring implementation. The old provider
path is no longer active. Its frozen evaluation records remain unchanged.

## Budgets and configuration

```dotenv
RERANK_ENABLED=true
RERANK_MODEL=BAAI/bge-reranker-v2-m3
RERANK_DEVICE=auto
RERANK_BATCH_SIZE=4
RERANK_MAX_PAIR_TOKENS=1024
RERANK_CANDIDATE_LIMIT=20
RERANK_MAX_INPUT_TOKENS=16384
```

`RERANK_MODEL` now names a compatible Hugging Face sequence-classification model
or local model directory. Blank uses the BGE default, independently of
`ANSWER_MODEL`. The supported baseline is the single-logit BGE model above.
Changing this setting requires a restart but no document reindexing.

Two distinct input limits apply:

- `RERANK_MAX_INPUT_TOKENS`: sum of all question/passage pair text, including
  repeated questions and heading prefixes, counted by `CHUNK_TOKENIZER`. It excludes
  model special tokens and padding. This is a workload cap, not a model-context cap.
- `RERANK_MAX_PAIR_TOKENS`: per-pair limit counted by the rerank model's own tokenizer,
  including its special tokens. The complete window is checked before inference.
  Oversize pairs fail instead of silently truncating either question or passage.
  The configured limit should stay within the selected model's context capacity.

Neither limit modifies stored child or parent text. Both failures surface through
the existing JSON/SSE error contract, without generation or a saved exchange.
Disconnecting during synchronous scoring prevents subsequent generation and saving;
the abandoned worker can finish its current inference. See
[configuration](configuration.md) for precedence and entry-point flags.

## Traces and history

`retrieval.rerank` records the model, resolved model revision (when available),
actual device, batch size, pair limit, aggregate token count, exact candidate
window, and all ranked matches. Its retained `prompt_version` field identifies
the input format (`cross-encoder-pairs-v1`); there is no instruction prompt.
`rerank_seconds` measures scoring preparation plus inference for that query.

Every new match has `score_kind: "logit"`. Each selected source carries its best
selected child's original `fusion` metadata and separate `rerank` metadata.
The frontend debug view displays raw logits independently of RRF/vector scores.
Saved snapshots survive restart and source deletion. Older matches without
`score_kind` default to `ordinal_0_3` and retain their historical `/3` display;
old scores are never relabeled as BGE logits.

## Low-level usage

```python
from knowledgebase.config import Settings
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.rag.reranking import rerank

settings = Settings()
client = RerankerClient(
    settings.rerank_model, device=settings.rerank_device,
    batch_size=settings.rerank_batch_size,
    max_pair_tokens=settings.rerank_max_pair_tokens,
)
# candidates are canonical RerankCandidate objects from the fused Ready corpus.
result = rerank(question, candidates, client, top_k=settings.retrieval_top_k)
for hit in result.selected:
    print(hit.chunk_id, hit.rerank_score, hit.rerank_rank, hit.rank)
```

API, CLI, and evaluation use the same provider. CLI/evaluation `--rerank-model`
now takes a local cross-encoder identifier. `--no-rerank` retains the hybrid control;
vector-only retrieval requires reranking to be disabled. Evaluation metadata
records resolved model and local runtime settings; per-answer traces include
actual device and model revision.

## Verification

`tests/test_reranker_provider.py` saves and loads a tiny local Transformers model
for offline verification of batching, raw fractional negative logits, tokenizer
limits, unchanged input, and failure propagation. It never downloads pretrained
test weights. Integration tests cover selection before parent expansion, exact
budgets, JSON/SSE, CLI/evaluation configuration, follow-ups, restart/deletion,
old history, and cancellation. Frontend tests distinguish both score formats.

The earlier [LLM scoring comparison](../evals/library-runs/20260924T000238Z-rerank/README.md)
remains historical evidence. A dedicated model must be evaluated separately;
model specialization alone does not establish better answers or latency.

The [BGE integration comparison](../evals/library-runs/20260924T002009Z-bge-serialized/README.md)
records the same 18 questions with a hybrid control, local MPS timing, source
fidelity, a corrected concurrency crash, and a remaining CPT evidence regression.
