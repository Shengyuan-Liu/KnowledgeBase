# New-PDF acceptance preparation

Prepared the [four-file candidate](../../materials/pdf-v2-candidate-20261001/README.md)
and six questions on `v2` product `7b93c61`. The new corpus covers papers, lecture
material and a company report, totaling 90 physical pages. Original bytes were
frozen before questions. Product implementation, source libraries and previous
evaluation runs remain unchanged. No ingestion, query, provider call or browser
acceptance was executed in this preparation.

The set includes one positive evidence-dependent chain and its restricted-scope
twin. A correct final answer alone cannot satisfy the separately frozen dependency
execution gate. Other cases cover prose, physical-page versus printed-slide
mapping, period/accounting-basis table distinctions and a forecast distractor.
There are four fully answerable cases, one partial case and one fully unanswerable
case; 12 distinct positive facts form 13 case-fact instances. The request-only
question file is separate from gold references and neither should be indexed.

## Original-page review

Codex, a model, visually inspected eight original physical pages and compared
the relevant text/table associations. The render hashes are retained in
`render-manifest.json` and `header-render.json`:

| Original page | Review finding |
| --- | --- |
| RAG 3 | Prose distinguishes sequence/token document use and states the DPR initialization relationship |
| DPR 3 | Right-column prose states the best model's two negative sources; printed page is 6771 |
| Decision trees 35 | Upper slide is printed Slide 69; definition and possible test-set effect are prose, not chart interpretation |
| NVIDIA 1 | Quarterly GAAP and Non-GAAP operating-income rows and million-dollar units are distinct |
| NVIDIA 2 | Annual GAAP/Non-GAAP rows are distinct; Q1 FY26 revenue is explicitly an outlook |
| NVIDIA 4 | GAAP income statement supplies equivalent quarterly/annual values under dated grouped columns |
| NVIDIA 7 | Units and three-/twelve-month headings for the reconciliation table that continues on page 8 |
| NVIDIA 8 | Continued reconciliation rows supply equivalent GAAP/Non-GAAP operating income; headings come from page 7 |

`reference-page-text.json` retains Poppler layout text and
`reference-reading-text.json` retains reading-order text for every original page.
Neither is production extraction. Gold spans address page-local reference text,
not Docling canonical offsets. Product span mapping and retrieval labels remain
unavailable until ingestion; missing product facts must remain visible failures.

[Absence review](absence-review.json) retains every searched-term context from
all 16 RAG pages and all 10 NVIDIA pages. It supports scoped missing-training-recipe
and missing-actual-revenue labels, alongside relevant original-page review. This
is not exhaustive visual inspection of every embedded image. Formula/OCR/visual
chart understanding is not tested. Independent human review is unavailable.

## Retained attempts and checks

The first acquisition downloaded the three papers/lecture files, then the NVIDIA
CFO commentary returned HTTP 403. Its failed command/log remain. The successful
second acquisition used a different publicly linked official NVIDIA press-release
PDF before any question was authored. No credentials or access-control bypass
were used. The first script did not retain successful response headers before
stopping; the manifest explicitly records that limitation.

Recorded commands cover acquisition, independent page-text extraction, source
rendering, reference freezing, and final package verification. Each command has
all 20 policy metric statuses. These are offline preparation checks: no retrieval,
answer-quality, production performance or provider billing result is claimed.
Download/render durations are command wall times, not product ingestion latency.
The final verification checks source hashes, chronology, reference spans, file
scope, separate request/gold data, freeze integrity, English documentation and
local links. Raw failure logs remain unchanged.

The [acceptance protocol](../../materials/pdf-v2-candidate-20261001/acceptance-protocol.md)
fixes one future six-request planned pass and review populations. The
[browser protocol](../../materials/pdf-v2-candidate-20261001/browser-protocol.md)
fixes six checks at desktop/mobile widths using those saved results without
additional generation. Neither protocol has execution results yet. No feature
acceptance, broad accuracy claim or merge is implied.

The next execution starts with an isolated library, ingestion and a frozen
source-to-product-span mapping, then the six requests and browser/history checks.
The new population is not comparable as a before/after score against the prior
six development questions. Once opened for tuning, label it development material.
