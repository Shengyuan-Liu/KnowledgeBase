# Initial Standalone Reranker Probe

This append-only record preserves the first `child-relevance-v1` prototype probe
on four questions from the [frozen hybrid run](../../library-runs/20260923T221737Z-hybrid/README.md).
The prototype requested a structured list of `{chunk_id, score}` objects from
the configured `gpt-4.1` model, scoring 20 children per question.

Three requests succeeded. CPT failed the module's exact-ID-coverage check: the
provider returned 19 scores and omitted `e32fdf05ea4b4d0ebdf567c104e1567b:child:6`.
The incomplete score list was not used as a ranking, repaired, or replaced by RRF.

- [run.json](run.json) records the model, limits, frozen-input fingerprints, and base revision.
- [results.jsonl](results.jsonl) preserves all four attempts, durations, token usage,
  and complete scored inputs for successful attempts. The failed attempt's input
  is reproducible from its case ID and the frozen RRF top 20.
- [failed-response.json](failed-response.json) is the original parsed output read
  back by response ID after the failure; it contains the 19 returned scores.
- [run_evaluation.py](run_evaluation.py) records the experiment procedure. It imports
  the checkout's current implementation; running it now uses the corrected schema,
  not this archived prototype's response shape. Copy into a fresh directory before
  rerunning because existing output files use exclusive-create writes.

The implementation subsequently changed to a required-key response object: every
candidate ID has a required integer score field. See the
[corrected probe](../20260923T234002Z-required-scores/README.md). These initial
records are retained to show the observed failure that motivated the change.
