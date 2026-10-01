"""Local, sequential PDF parser comparison; preserve every attempt separately."""

import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "evals/materials/pdf-v2"
CASES = [
    ("doclaynet", (1, 2)),
    ("ml-lecture", (2, 3)),
    ("background-checks", (1, 1)),
    ("docling-report", (4, 5)),
]


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    target = Path(__file__).parent / sys.argv[1]
    target.mkdir(exist_ok=False)
    if "--apple" in sys.argv:
        CASES = [("apple-fy24", (1, 1))]
    started = time.perf_counter()
    state = {
        "command": sys.argv, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "device": platform.platform(), "concurrency": 1, "retries": 0,
        "versions": {p: importlib.metadata.version(p) for p in [
            "docling", "docling-core", "docling-ibm-models", "docling-parse", "pdfplumber", "torch",
        ]}, "cases": [],
    }
    save(target / "run.json", state)
    try:
        import pdfplumber
        for name, page_range in CASES:
            start = time.perf_counter()
            with pdfplumber.open(CORPUS / f"{name}.pdf") as pdf:
                pages = [{"page_no": p.page_number, "width": p.width, "height": p.height,
                          "text": p.extract_text(), "tables": p.extract_tables()}
                         for p in pdf.pages[page_range[0]-1:page_range[1]]]
            save(target / f"{name}-pdfplumber.json", pages)
            state["cases"].append({"parser": "pdfplumber", "case": name,
                                   "page_range": page_range, "seconds": time.perf_counter()-start,
                                   "status": "success"})
            save(target / "run.json", state)
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions, LayoutObjectDetectionOptions, TableStructureOptions,
            TableStructureV2Options,
        )
        from docling.datamodel.accelerator_options import AcceleratorOptions
        options = PdfPipelineOptions(
            do_ocr=False, do_table_structure=True,
            layout_options=LayoutObjectDetectionOptions.from_preset("layout_heron_default"),
            table_structure_options=(TableStructureV2Options() if "--table-v2" in sys.argv
                                     else TableStructureOptions()),
            accelerator_options=AcceleratorOptions(device="cpu", num_threads=4),
        )
        save(target / "options.json", options.model_dump(mode="json", serialize_as_any=True))
        converter = DocumentConverter(allowed_formats=[InputFormat.PDF], format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=options),
        })
        for name, page_range in CASES:
            print(f"Converting {name}", flush=True)
            start = time.perf_counter()
            result = converter.convert(CORPUS / f"{name}.pdf", page_range=page_range)
            save(target / f"{name}-docling.json", result.document.export_to_dict())
            (target / f"{name}-docling.md").write_text(result.document.export_to_markdown())
            state["cases"].append({"parser": "docling", "case": name,
                                   "page_range": page_range, "seconds": time.perf_counter()-start,
                                   "status": result.status.value,
                                   "errors": [e.model_dump(mode="json") for e in result.errors]})
            save(target / "run.json", state)
    except Exception:
        state["failure"] = traceback.format_exc()
        raise
    finally:
        state["total_seconds"] = time.perf_counter() - started
        state["process_peak_rss_bytes_macos"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(target / "run.json", state)
