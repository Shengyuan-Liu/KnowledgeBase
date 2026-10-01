# PDF v2 Development Corpus

Original public files are frozen before parser comparison; byte hashes, source
URLs, page counts and rights notes are in [manifest.json](manifest.json). Original
copyright notices remain in each PDF. These are development fixtures, not project
authored documents or held-out release material.

| File | Population | Compared physical pages |
| --- | --- | --- |
| `doclaynet.pdf` | Research paper; two columns, caption and list continuation | 1-2 |
| `ml-lecture.pdf` | CMU slides; native text and embedded screenshot | 2-3 |
| `background-checks.pdf` | Government report; dense grouped table and notes | 1 |
| `docling-report.pdf` | Technical report; cross-page paragraph and merged table | 4-5 |
| `apple-fy24.pdf` | Company report; quarterly/annual financial table and units | 1 |

[Annotations](annotations.json) and [Apple annotations](apple-annotations.json)
record selected expectations from rendered original pages, reviewed by Codex
(a model, not a human). They are incomplete checkpoints, not exhaustive text/cell
labels. The [annotation correction](annotation-corrections.json) corrects a
cross-page transcription without rewriting its original record.

Apple was added after the four-document comparison to include an actual company
report. It has a separate supplemental run; all candidate configurations were not
compared on it. The Stanford lecture download returned HTTP 403; an accessible
CMU lecture was selected instead, before comparison.

The original Apple PDF has four physical pages, including a landscape page; visual
review covers page 1. Full-file adapter checks cover all four Apple pages and nine
technical-report pages without claiming full visual review. Frozen parser outputs
and known failures are in the [comparison record](../../check-runs/20260926-pdf-parser-selection/README.md).
