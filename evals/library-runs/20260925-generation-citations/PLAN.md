# Frozen generation-citation acceptance

Replay the prior structural parent-child batch's 24 questions with byte-identical
user messages and supplied evidence. Change only the developer instructions to
the completed citation-locality and source-fidelity prompt. The production
StreamingLLMClient executes the requests. No ingestion, retrieval, reranking,
query resolution, HTTP transport, or conversation persistence runs here.

Use the same GPT-4.1 configuration, record its returned revision, and reuse all
24 prior answers and their valid v11 reviews. Judge the 24 new answers once with
the unchanged v11 source hash, GPT-5.4-mini, high reasoning, four workers and zero
retries. No calibration tuning or automated retries/regrading. Preserve errors
and invalid judgments. All 24 cases are development/regression data now, including
the six that were newly frozen in the preceding experiment.

`freeze.json` records baseline hashes, both exact prompts and the non-secret
configuration before paid generation. `test_replay.py` verifies unchanged user
messages, baseline review identities and separation of generation timings from
unexecuted service stages. Mocked generation tests verify shared prompt delivery,
not model compliance. Feature checks must pass before the paid acceptance batch.

Report claim-local citation coverage, citation support, expected-point correctness,
faithfulness, attempted points, relevance and both kinds of abstention separately.
Retain original retrieval ranking/coverage as frozen provenance, not a new
retrieval measurement. Record per-case improvements and regressions, exact answers,
evidence, prompts, provider usage and all judge stages. Billed dollars remain
unavailable unless returned; do not infer billing from token totals.

Compare generation-call-to-first-delta and generation-call-through-stream-close
timings separately from full service timings, which are not exercised. Sequential
replay concurrency is one. Report count, mean, median P50 and nearest-rank P95;
host/provider load and cache state are uncontrolled. Historical baseline versus
one fresh pass does not establish causal performance improvement.

Codex inspects all decreases in expected-point correctness or faithfulness and
representative citation failures against exact supplied evidence. Retain disputed
judge classifications. Code/source review by Codex is not independent human grading.
Keep retrieval settings and the structural default unchanged. Commit on `v1`;
feature acceptance and merging remain the user's decision.

```bash
PYTHONPATH=. uv run --locked python evals/library-runs/20260925-generation-citations/run_replay.py collect
PYTHONPATH=. uv run --locked python evals/library-runs/20260925-generation-citations/run_replay.py grade
```

Use a new directory for any later paid attempt. The existing authorized `.env`
credential is reused without modifying the file or the user's indexed library.
