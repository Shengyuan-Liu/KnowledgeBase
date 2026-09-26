# Question-aligned answer correction

## Annotation audit before new provider output

The awards question asks how applicants are considered, how recipients are
notified, and whether a job is guaranteed. The old reference additionally demands
limited award count, competitive jobs and semester-by-semester postings. Those
are supported optional context, not necessary answers to the actual question.
Requiring them conflicts with the product instruction to omit unrelated details.

Version 2 retains all five exact questions and all corpus/source span annotations.
Only awards points 1 and 3 change: all admission applicants considered competitively;
no individual job guarantee. Admit-letter notification remains required. Optional
facts, if supplied, must still be true, qualified and attributed to their actual
source. In particular, no separate application cannot be credited to the general
FAQ; the admissions FAQ must be explicitly identified and cited if used.
All other reference points, source-scope rules and thresholds remain unchanged.

This correction was identified after inspecting historical outputs. It is not a
blind preregistration for those outputs or an independent evaluation. Retain old
scores and report both rubric versions for the new output. Reassess the unchanged
GPT-4.1 baseline using version 2 for a like-for-like comparison. For the prior high
reasoning sample, revised factual scoring would be 5/5 instead of 4/5, but the
observed non-English status word still fails the project's language requirement.
This is a reviewer correction, not a model improvement or acceptance of that run.

## Implementation and one bounded acceptance pass

The completed prompt change requests one concise answer per question part, avoids
unrequested background and repeated summaries, checks the actual numbered excerpt,
and explicitly includes uncertainty/status labels in the English requirement.
No evidence filtering, answer repair, ASCII restriction, extra model call, setting
change or retriever change. Offline tests check shared prompt delivery and evidence
fidelity; they cannot demonstrate semantic compliance.

Compare against 20260925-grounding-order: same default GPT-4.1, reasoning omitted,
same exact user messages, source order/text, questions, context and other settings.
Only developer instructions change. Five streaming generation calls, once per
case, sequential, 60-second timeout, zero SDK retries, no warmup, no paid judge.
Freeze plan, both annotation versions, prompt, settings and baseline artifacts
before calls. Preserve all errors/outputs. No further prompt/model trials in this
session if this pass fails. No changes to local .env or checked-in model defaults.

## Review gates and measurements

Codex reviews every answer, required point and factual claim against exact source
quotes/offsets, including extra/repeated claims. This is the implementer's review,
not independent human review. All 11 question-aligned reference points must be
fully correct; all claims and associated citations must be supported; local
supporting citation coverage >=80% overall and at least one per factual answer.
Claim-free abstentions have no citation requirement. Missing information itself
is assessed under abstention, not as a positive source fact. Require appropriate
abstention on both unavailable cases and no incorrect refusal on answerable cases.
Require English explanatory text, including all labels; preserve proper names
and code identifiers. Record old-rubric factual pass separately from v2 acceptance.

Five successful calls with valid citation IDs; generation mean <=10 s, nearest-rank
P95 <=20 s, first nonempty delta P95 <=10 s, input <=12000 tokens/request. Report
N, mean, median P50 and nearest-rank P95, provider wait included, no service/HTTP
latency claim. Retain complete metric inventory, requested/resolved model, token
usage, errors/retries and concurrency/throughput. Billed cost unavailable unless
returned; inherited retrieval/coverage are not new measurements. No new indexing.

These are five known development cases with historical, noisy single samples,
not held-out accuracy, a new full-service run, or a guarantee of English/grounding
compliance. The earlier eight-case service result stays 7/8. Passing this targeted
check permits reconsidering merge readiness together with existing engineering
checks; it does not authorize a merge.
