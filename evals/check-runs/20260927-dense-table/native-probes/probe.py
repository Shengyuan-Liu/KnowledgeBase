"""Freeze native characters, ruled boundaries, and pdfplumber extraction variants."""
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
import time
import traceback

import pdfplumber
from pdfplumber.table import TableSettings

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[3]
OUT = DIRECTORY / sys.argv[1]
OUT.mkdir()


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n")


started = time.perf_counter()
records = []
cases = [("background-checks", 1), ("apple-fy24", 1), ("docling-report", 5),
         ("doclaynet", 1), ("ml-lecture", 3)]
for name, page_no in cases:
    path = ROOT / "evals/materials/pdf-v2" / f"{name}.pdf"
    parse_started = time.perf_counter()
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[page_no - 1]
        chars = page.chars
        words = page.extract_words()
        edges = page.edges
        parse_seconds = time.perf_counter() - parse_started
        write(f"{name}-page-{page_no}-native.json", {
            "source": str(path.relative_to(ROOT)), "source_sha256": sha256(path.read_bytes()).hexdigest(),
            "page_number": page_no, "page_width": page.width, "page_height": page.height,
            "native_parse_seconds": parse_seconds, "chars": chars, "words": words, "edges": edges,
            "text": page.extract_text(),
        })
        variants = [("lines-text", {"vertical_strategy": "lines", "horizontal_strategy": "text"})]
        if name == "background-checks":
            variants.append(("lines-lines", {"vertical_strategy": "lines", "horizontal_strategy": "lines"}))
        for variant_name, settings in variants:
            variant_started = time.perf_counter()
            record = {"case": name, "page_number": page_no, "variant": variant_name,
                      "settings": asdict(TableSettings.resolve(settings)), "native_parse_seconds": parse_seconds}
            try:
                finder = page.debug_tablefinder(settings)
                tables = [{"bbox": table.bbox, "cells": table.cells,
                           "rows": [row.cells for row in table.rows], "text": table.extract()}
                          for table in finder.tables]
                artifact = f"{name}-page-{page_no}-{variant_name}.json"
                write(artifact, {"settings": record["settings"], "edges": finder.edges,
                                 "intersections": [{"point": point, "edges": value} for point, value in finder.intersections.items()],
                                 "cells": finder.cells, "tables": tables})
                record.update(status="success", table_count=len(tables),
                              table_shapes=[[len(table["text"]), max(map(len, table["text"]), default=0)] for table in tables],
                              artifact=artifact)
            except Exception as error:
                record.update(status="error", error=repr(error), traceback=traceback.format_exc())
            record["table_extraction_seconds"] = time.perf_counter() - variant_started
            records.append(record)

summary = {
    "purpose": "Native ruled-boundary probe; no production code or library mutation.",
    "versions": {package: version(package) for package in ["pdfplumber", "pdfminer.six", "pypdfium2", "Pillow"]},
    "python": sys.version, "device": platform.platform(), "concurrency": 1,
    "source_code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    "duration_seconds": time.perf_counter() - started, "variants": records,
    "provider_calls": 0, "reviewer": "Codex model reviewer; original-page visual review and frozen gold comparison recorded separately.",
    "successes": sum(row["status"] == "success" for row in records),
    "errors": sum(row["status"] == "error" for row in records), "timeouts": 0, "retries": 0,
}
write("summary.json", summary)
print(json.dumps({"versions": summary["versions"], "variants": records}, indent=2))
raise SystemExit(bool(summary["errors"]))
