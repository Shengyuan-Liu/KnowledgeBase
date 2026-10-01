"""Test text-row boundaries across the native ruled-table width, without fixture values."""
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import sys
import time

import pdfplumber
from pdfplumber.table import TableSettings

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[3]
OUT = DIRECTORY / sys.argv[1]
OUT.mkdir()


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n")


started = time.perf_counter()
source = ROOT / "evals/materials/pdf-v2/background-checks.pdf"
frozen = ROOT / "evals/check-runs/20260926-pdf-parser-selection/attempt-1/background-checks-docling.json"
doc = json.loads(frozen.read_text())
records = []
with pdfplumber.open(source) as pdf:
    for item in doc["tables"]:
        if item["data"]["num_rows"] > 1 and item["data"]["num_cols"] > 1:
            continue
        provenance = item["prov"][0]
        page = pdf.pages[provenance["page_no"] - 1]
        b = provenance["bbox"]
        bbox = ((b["l"], page.height - b["t"], b["r"], page.height - b["b"])
                if b["coord_origin"] == "BOTTOMLEFT" else (b["l"], b["t"], b["r"], b["b"]))
        crop = page.crop(bbox)
        parse_start = time.perf_counter()
        native = {"bbox": bbox, "chars": crop.chars, "words": crop.extract_words(), "edges": crop.edges}
        write("cropped-native.json", native)
        parse_seconds = time.perf_counter() - parse_start
        baseline_settings = {"vertical_strategy": "lines", "horizontal_strategy": "text"}
        baseline = crop.debug_tablefinder(baseline_settings)
        y_edges = sorted({edge["top"] for edge in baseline.edges if edge["orientation"] == "h"})
        variants = [("cropped-lines-text", baseline_settings), ("extended-text-rows", {
            "vertical_strategy": "lines", "horizontal_strategy": "explicit", "explicit_horizontal_lines": y_edges})]
        for label, settings in variants:
            stage_start = time.perf_counter()
            finder = crop.debug_tablefinder(settings)
            tables = [{"bbox": t.bbox, "cells": t.cells, "rows": [r.cells for r in t.rows], "text": t.extract()}
                      for t in finder.tables]
            artifact = label + ".json"
            write(artifact, {"settings": asdict(TableSettings.resolve(settings)), "edges": finder.edges,
                             "intersections": [{"point": p, "edges": v} for p, v in finder.intersections.items()],
                             "tables": tables})
            records.append({"variant": label, "status": "success", "artifact": artifact,
                            "native_parse_seconds": parse_seconds, "table_extraction_seconds": time.perf_counter() - stage_start,
                            "table_shapes": [[len(t["text"]), max(map(len, t["text"]), default=0)] for t in tables]})

index_path = ROOT / "evals/library-runs/20260927-v2-pdf-live/index-snapshot.json"
index = json.loads(index_path.read_text())
gate = [{"file": entry["file"]["file_name"], "tables": [
    {"table_id": block["table"]["table_id"], "rows": block["table"]["rows"], "columns": block["table"]["columns"],
     "eligible_for_native_probe": block["table"]["rows"] <= 1 or block["table"]["columns"] <= 1}
    for block in entry["extraction"]["blocks"] if block.get("table")]} for entry in index["files"]]
summary = {
    "source_sha256": sha256(source.read_bytes()).hexdigest(), "frozen_docling_sha256": sha256(frozen.read_bytes()).hexdigest(),
    "frozen_index_sha256": sha256(index_path.read_bytes()).hexdigest(), "source_code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    "versions": {p: version(p) for p in ["pdfplumber", "pdfminer.six", "pypdfium2", "Pillow"]},
    "method": "Crop to the frozen collapsed Docling table. Reuse pdfplumber native vertical rules and its snapped text-row y coordinates, extending horizontal candidates across the crop width by using explicit y lines. No state names, expected values, column count, or source-specific coordinates are used by the extraction rule.",
    "duration_seconds": time.perf_counter() - started, "variants": records,
    "collapsed_table_gate": gate, "provider_calls": 0, "successes": len(records), "errors": 0, "timeouts": 0, "retries": 0,
}
write("summary.json", summary)
print(json.dumps({"variants": records, "collapsed_table_gate": gate}, indent=2))
