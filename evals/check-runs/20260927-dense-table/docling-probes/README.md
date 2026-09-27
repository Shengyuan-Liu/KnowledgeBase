# Dense-table Docling configuration probes

These three local probes did not recover the missing Alabama values in
`background-checks.pdf`. Every configuration received the original digital text
for Alabama, Permit `18,870`, Handgun `23,022`, Long Gun `22,650`, and Totals
`71,137`; none retained those values in its final table. No row/column association
for the requested values was recovered.

The earliest demonstrated failure is in TableFormer structure prediction, before
cell matching and the KnowledgeBase adapter. All three retained predictions have
two `ched` tokens followed by 1,021 `lcel` tokens, no row separators, and only two
predicted boxes. This degenerate sequence is retained in full. Changing cell
matching or the PDF backend did not resolve it.

## Frozen scope

The [manifest](manifest.json) records product commit `9dcb7c5`, source PDF hash,
package versions, all local model-file hashes, production-source hashes, command,
environment and device. Only physical page 1 of the same
[digital PDF](../../../materials/pdf-v2/background-checks.pdf) was parsed.

Each variant ran once in a fresh subprocess, sequentially, with CPU execution and
four threads. OCR, code/formula enrichment, picture interpretation, chart
extraction and remote services were disabled. `HF_HUB_OFFLINE=1` and
`TRANSFORMERS_OFFLINE=1` were required; all model assets came from the existing
`data/pdf-models` directory. There were no provider calls, downloads, embeddings,
index writes, or downstream answer requests.

`generate_parsed_pages=True` retains native text cells. An evaluation-only wrapper
around `TFPredictor.multi_table_predict` records the actual native tokens, table
boxes, page image and predictor output without changing their contents.

## Observations

| Variant | Final table | Predictor input tokens | Requested values in final table | Conversion seconds | Command wall seconds |
| --- | --- | ---: | ---: | ---: | ---: |
| [V1 accurate, matching enabled](accurate-matching/result-summary.json) | 1 row × 1 column; 1 cell | 1,361 | 0/4 | 12.989 | 16.157 |
| [V1 accurate, matching disabled](accurate-no-matching/result-summary.json) | 1 row × 2 columns; 2 cells | 1,361 | 0/4 | 12.808 | 15.363 |
| [PyPdfium backend, V1 accurate, matching enabled](pdfium-accurate-matching/result-summary.json) | 1 row × 1 column; 1 cell | 1,091 | 0/4 | 12.675 | 15.218 |

The standard backend is `ThreadedDoclingParseDocumentBackend`; the final variant
changes only the backend to `PyPdfiumDocumentBackend`. All three use V1 accurate
TableFormer and the same local model assets. The first two differ only in the
cell-matching option. Each option object and resolved backend name is preserved.

All native predictor inputs contain the five target strings, including Alabama.
The matching-enabled standard-backend log reports that 950 of 1,361 PDF cells
matched neither a row nor a column band of the postprocessed 2×2 grid and were
dropped. The PyPdfium variant reports 725 of 1,091 dropped cells. The exported
1×1 tables describe the surviving, compressed output; they are not the earlier
postprocessing grid mentioned by those warnings.

Conversion duration starts immediately before `converter.convert` and includes
lazy pipeline/model initialization and diagnostic writes performed inside that
call. Command wall time also includes interpreter/import overhead and final
artifact writes. There is one sample per variant; P50 and P95 in each command
record equal that sample. OS file caches may warm between variants. These values
do not establish a performance difference, throughput, or production latency.

## Retained evidence

The [comparison](comparison.json) links each variant and its summary. Each variant
has a complete 20-metric command record:

- [Standard backend, matching](accurate-matching/record.json)
- [Standard backend, no matching](accurate-no-matching/record.json)
- [PyPdfium backend, matching](pdfium-accurate-matching/record.json)

Each variant directory also contains `command.log`, `options.json`, `document.json`,
`document.md`, `native-pages.json`, `predictor-input-1.json`,
`predictor-input-1.png`, and `predictor-output-1.json`. These preserve original
native words and locations, layout/table predictions, exact model inputs, and
final table content. The [runner](run_probes.py) records each command attempt
separately. All three commands completed successfully; their table-fidelity
failure remains explicit.

The value and association fields in the summaries are mechanical diagnostics:
exact value-cell matches, shared Alabama row offsets, and same-column header
candidates. They do not constitute semantic table verification. Retrieval,
answer quality, citation quality, streaming, provider billing and index lifecycle
metrics are not applicable to this parser-only workload. Local energy/hardware
cost was not measured.

No production change is justified by these three unsuccessful configuration
variants alone. This record does not establish a repair for dense tables or
authorize a merge. No further variants or corpus-wide run were performed here.
