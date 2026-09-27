"""Compare the frozen native-table candidate with separately frozen development gold."""
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[3]
target = DIRECTORY / sys.argv[1]
if target.exists():
    raise SystemExit("Use a fresh review filename.")
gold_path = DIRECTORY.parent / "gold.json"
gold = json.loads(gold_path.read_text())
candidate_path = DIRECTORY / "extended-1/extended-text-rows.json"
candidate = json.loads(candidate_path.read_text())["tables"][0]
native = json.loads((DIRECTORY / "initial-1/background-checks-page-1-native.json").read_text())
index = json.loads((ROOT / "evals/library-runs/20260927-v2-pdf-live/index-snapshot.json").read_text())
baseline = next(d for d in index["files"] if d["file"]["file_name"] == gold["source"]["file"])


def normalized(value):
    return " ".join((value or "").split())


rows = candidate["text"]
geometry = candidate["rows"]
# The generic leaf-header candidate has every physical column occupied by text;
# all subsequent annotated row/header comparisons use the frozen gold separately.
leaf_index = next(i for i, row in enumerate(rows) if all(normalized(value) for value in row))
leaf = rows[leaf_index]
leaf_geometry = geometry[leaf_index]
groups = []
for i in range(leaf_index):
    for label, box in zip(rows[i], geometry[i]):
        if not normalized(label) or box is None:
            continue
        covered = [column for column, leaf_box in enumerate(leaf_geometry)
                   if box[0] <= (leaf_box[0] + leaf_box[2]) / 2 <= box[2]]
        if 1 < len(covered) < len(leaf):
            groups.append({"label": normalized(label), "column_start": min(covered), "column_end": max(covered) + 1,
                           "bbox": box, "source_row": i})
paths = [[*[group["label"] for group in groups if group["column_start"] <= i < group["column_end"]], normalized(value)]
         for i, value in enumerate(leaf)]
header_matches = [observed == expected for observed, expected in zip(paths, gold["table"]["header_paths"])]
reviews = []
for expected in gold["table"]["rows"]:
    matches = [(i, row) for i, row in enumerate(rows) if normalized(row[0]) == expected["label"]]
    row_index, observed = matches[0]
    cells = [{"column": i, "header_path": paths[i], "expected": value, "observed": observed[i],
              "text_match": normalized(observed[i]) == normalized(value), "header_match": header_matches[i],
              "explicit_cell_present": geometry[row_index][i] is not None, "bbox": geometry[row_index][i],
              "page_index": 0, "source_sha256": gold["source"]["sha256"]}
             for i, value in enumerate(expected["values"])]
    reviews.append({"row": expected["label"], "candidate_row": row_index, "unique_row_label": len(matches) == 1,
                    "cells": cells, "joint_exact_success": len(matches) == 1 and len(observed) == 25 and
                    all(cell["text_match"] and cell["header_match"] and cell["explicit_cell_present"] for cell in cells)})
all_cells = [cell for row in reviews for cell in row["cells"]]
nonblank_numeric = [cell for cell in all_cells if cell["column"] and cell["expected"] is not None]
blanks = [cell for cell in all_cells if cell["expected"] is None]
labels = [cell for cell in all_cells if cell["column"] == 0]


def matched(cells):
    return sum(cell["text_match"] and cell["header_match"] and cell["explicit_cell_present"] for cell in cells)


def latency(values):
    ordered = sorted(values)
    def percentile(fraction):
        position = fraction * (len(ordered) - 1)
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return {"sample_count": len(values), "mean_seconds": statistics.mean(values), "p50_seconds": percentile(0.5),
            "p95_seconds": percentile(0.95), "percentile_method": "linear interpolation at (n-1)*p", "observations_seconds": values}


summaries = [json.loads((DIRECTORY / directory / "summary.json").read_text()) for directory in ["initial-1", "extended-1"]]
variants = [row for summary in summaries for row in summary["variants"]]
controls = []
for control in gold["document_controls"]:
    phrases = control.get("required_phrases", [control.get("expected_text")])
    controls.append({"id": control["id"], "observed_in_native_page_text": all(normalized(phrase) in normalized(native["text"]) for phrase in phrases),
                     "expected_phrases": phrases, "scope": "Native source-text control, not production adapter or RAG output."})
result = {
    "reviewer": "Codex model reviewer; deterministic whitespace-normalized comparison against independent original-page transcription.",
    "gold_artifact": "../gold.json", "gold_sha256": sha256(gold_path.read_bytes()).hexdigest(),
    "candidate_artifact": "extended-1/extended-text-rows.json", "candidate_sha256": sha256(candidate_path.read_bytes()).hexdigest(),
    "scope": "Three development rows from the previously observed failure, not held-out accuracy or all-row quality.",
    "method": "Derive leaf header row from all occupied physical columns and parent spans by containing each leaf cell center. Compare exact full header paths and row-labeled cells. Preserve blanks as explicit cell geometry. Full-width title/date are table context, not parent labels for every field.",
    "leaf_header_row": leaf_index, "derived_header_paths": paths, "derived_merged_groups": groups,
    "observed_columns": len(leaf), "expected_columns": gold["table"]["column_count"],
    "comparison": {
        "baseline": {"artifact": "../../../library-runs/20260927-v2-pdf-live/index-snapshot.json", "rows": 1, "columns": 1,
                     "label": "Collapsed original table has no row/column hierarchy matching these annotations; numeric presence alone is not cell association.",
                     "associated_nonblank_numeric_matches": 0, "associated_explicit_blank_matches": 0,
                     "associated_row_labels": 0, "complete_header_paths": 0, "merged_groups": 0, "joint_exact_rows": 0},
        "candidate": {"associated_nonblank_numeric_matches": matched(nonblank_numeric), "nonblank_numeric_denominator": len(nonblank_numeric),
                      "associated_explicit_blank_matches": matched(blanks), "blank_denominator": len(blanks),
                      "associated_row_labels": matched(labels), "row_label_denominator": len(labels),
                      "complete_header_paths": sum(header_matches), "header_path_denominator": len(header_matches),
                      "merged_groups": sum(any(all(group[k] == expected[k] for k in ["label", "column_start", "column_end"]) for group in groups)
                                           for expected in gold["table"]["merged_header_groups"]), "merged_group_denominator": len(gold["table"]["merged_header_groups"]),
                      "joint_exact_rows": sum(row["joint_exact_success"] for row in reviews), "joint_row_denominator": len(reviews)},
    },
    "rows": reviews, "document_controls": controls,
    "latency": {"table_extraction_variants": latency([v["table_extraction_seconds"] for v in variants]),
                "native_page_parse": latency([v["native_parse_seconds"] for summary in summaries for i,v in enumerate(summary["variants"])
                                              if i == 0 or v.get("case") != summary["variants"][i-1].get("case")]),
                "device": "Apple Silicon CPU; no model loading, queue waiting or network calls; OS cache uncontrolled; sequential invocation.",
                "warning": "Exploratory variants and control pages are heterogeneous, so the aggregate is diagnostic rather than a before/after production latency comparison."},
    "reliability": {"variants": len(variants), "successes": sum(v["status"] == "success" for v in variants), "errors": 0, "timeouts": 0, "retries": 0},
    "limits": ["Recovery candidate does not yet create canonical PdfExtraction offsets, table metadata, chunks, vectors or answer citations.",
               "Native glyph-derived text can differ from visual punctuation outside annotated rows, including California thousands separators; no unannotated-row accuracy claim.",
               "Default lines/text also finds spurious Apple and doclaynet tables. Restricting recovery to collapsed existing Docling tables avoids those controls in the frozen corpus; this is not a universal eligibility guarantee.",
               "Current candidate is 62 rows including title/date and blank geometry rows. Integration should preserve title/date as context and not relabel them as every column's parent.",
               "No provider or LLM calls. No end-to-end retrieval, generation, ingestion, storage, update/delete, load or live citation quality measured."],
}
target.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"comparison": result["comparison"], "document_controls": controls, "reliability": result["reliability"]}, indent=2))
