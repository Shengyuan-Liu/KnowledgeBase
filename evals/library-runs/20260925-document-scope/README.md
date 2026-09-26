# Document-scope initial acceptance — comparison failure retained

**10/11 cases pass; do not claim full acceptance.** The original eight questions
pass the question-aligned rubric, including the previously failing awards answer.
Both deterministic scope clarifications pass with no provider calls. The new
multi-document comparison fails: both FAQ files resolve, but global top-5 picks
only admissions chunks. Supplied gold evidence coverage is 50%, and generation
incorrectly calls an admissions-only statement a general-FAQ statement.

[PLAN.md](PLAN.md), [freeze.json](freeze.json), [answers.jsonl](answers.jsonl),
[calls.jsonl](calls.jsonl), [manual review](REVIEW.md), [metrics.json](metrics.json)
and [acceptance.json](acceptance.json) preserve all outputs and failures. Both
annotation versions remain present. Codex performed complete claim review, not
an independent human review. Do not overwrite this failed sample after correction.

Fresh isolated ingestion of 17 frozen documents took 8.765 s. Eleven service
requests completed: 17 ingestion embedding calls, 9 query embeddings, 9 answer
generations, zero paid judges, errors or retries. Default GPT-4.1, reasoning omitted.
Service mean 1.578 s/P95 2.354 s; first nonempty delta mean 0.867 s/P95 1.527 s,
N=11 including two immediate clarifications. Generation mean 1.592 s/P95 1.988 s,
first generation delta mean 0.728 s/P95 1.190 s, N=9. Median and nearest-rank
percentiles, provider waiting included; no HTTP or load-capacity claim. Actual
billed cost unavailable, not zero. Full metric inventory distinguishes skipped
provider stages from zero-duration measurements.

Answerable gold-span coverage is 92.86% (seven cases); all six original answerable
cases have full coverage, the comparison has half. Before/after scope correction
must keep these exact questions, corpus, references, prompt and model. The concrete
next correction is to retain per-document candidate representation and expose
resolved identity labels with excerpts, not change reference points or sample
another model. Existing global rank/budget limits remain relevant and must stay
visible. The original eight-case service run remains historically 7/8 under its
original references; this new result uses the previously corrected awards rubric.
