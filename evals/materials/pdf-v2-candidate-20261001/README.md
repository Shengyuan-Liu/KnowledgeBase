# New-PDF acceptance candidate

Four original PDFs were frozen before questions on 2026-10-01. They are new to
this project's evaluations; they are public documents and may be familiar to
pretrained models. This is a candidate for a first-use functional check, not
independent human validation or proof of model-training independence.

| File | Population | Physical pages | Primary source |
| --- | --- | --- | --- |
| `rag-paper.pdf` | Research paper | 16 | [NeurIPS proceedings](https://papers.nips.cc/paper_files/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html) |
| `dpr-paper.pdf` | Two-column research paper | 13 | [ACL Anthology](https://aclanthology.org/2020.emnlp-main.550/) |
| `decision-trees.pdf` | Lecture, two slides per physical page | 51 | [CMU tutorial](https://www.cs.cmu.edu/afs/cs/Web/People/awm/tutorials/dtree.html) |
| `nvidia-fy25.pdf` | Company report with grouped tables | 10 | [NVIDIA official PDF](https://nvidianews.nvidia.com/_gallery/download_pdf/67bf85d73d633281c6875f57/) |

[Manifest](manifest.json) records original byte hashes, URLs and rights notices.
All original notices remain intact; no project ownership or relicensing is claimed.
The initially selected CFO commentary returned HTTP 403. The official press-release
PDF replaced it before question authoring; the failed acquisition remains recorded.
The first three successful responses lack retained HTTP headers because that
initial script stopped before writing its metadata list; their bytes/hashes remain.

[Questions](questions.json) contain only request text and allowed filenames.
[References](references.json) separately retain expected facts, original physical
pages, table roles and negative cases. Gold annotations must never enter model
requests. The six cases contain 12 distinct positive facts, or 13 case-fact
instances because the bridge is repeated under a restricted scope.

| Case | Purpose | Expected source behavior |
| --- | --- | --- |
| `rag-document-granularity` | Prose comparison | Distinguish sequence-wide and token-level document use |
| `retriever-training-hop` | Evidence-dependent retrieval | Discover the retriever from RAG, then find its training recipe in its own paper |
| `retriever-training-restricted` | Paired scope / partial answer | Same question, only RAG allowed; retain the bridge but withhold unavailable training details |
| `lecture-overfitting` | Lecture prose and page mapping | Definition and test-set effect; printed slide 69 is physical page 35 |
| `income-period-basis` | Period and accounting-basis distinctions | Four operating-income values plus units across quarterly/annual GAAP/Non-GAAP tables |
| `forecast-is-not-actual` | Fully unanswerable / forecast distractor | Do not report an outlook as actual results |

Original-page references were reviewed by Codex, a model. They do not come from
product answers or Docling output. Reference text offsets address page-local
Poppler text; production canonical spans and retrieval labels remain unmapped
until ingestion. Missing product evidence must remain a failure, not trigger a
reference rewrite. There is no model-quality score for this preparation.

The [acceptance protocol](acceptance-protocol.md) separates answer quality from
actual dependency execution. The [browser protocol](browser-protocol.md) covers
source selection, physical-page viewing, page navigation and persisted history
at desktop/mobile widths. Both are prepared, not yet executed. The
[preparation record](../../check-runs/20261001-new-pdf-acceptance-preparation/README.md)
retains original renders, absence searches, checks and the final freeze hashes.

Once first-use model results are opened, failures may inform development, but this
set must then be labeled development material. Further independent claims require
another frozen set. No product changes or feature merge accompany this preparation.
