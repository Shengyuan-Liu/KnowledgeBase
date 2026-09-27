"""Three recorded local parser configurations on one frozen digital PDF page."""

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter
import traceback

ROOT = Path(__file__).parent
SOURCE = Path("evals/materials/pdf-v2/background-checks.pdf")
MODELS = Path("data/pdf-models")
VARIANTS = ["accurate-matching", "accurate-no-matching", "pdfium-accurate-matching"]
METRICS = ["Recall@K", "Precision@K", "Hit Rate@K", "MRR", "NDCG@K", "Final evidence coverage", "Answer correctness", "Faithfulness", "Answer completeness", "Answer relevance", "Citation support", "Citation coverage", "Abstention", "First-answer-delta latency", "Complete-response latency", "Stage latency", "Token usage and cost", "Reliability", "Concurrency and throughput", "Ingestion and index"]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    if hasattr(value, "tolist"):
        return value.tolist()
    raise TypeError(f"Unsupported retained result: {type(value).__name__}")


def write(path, value):
    assert not path.exists(), f"Append-only: {path}"
    path.write_text(json.dumps(value, indent=2, default=encode) + "\n")


def inventory(variant, seconds, success, summary):
    values = {metric: dict(status="not_applicable", value=None, unit=None, sample_count=None,
                          population="One-page offline parser configuration probe", method="No retrieval, generated answer, streaming, provider, index lifecycle or load workload.",
                          reason="No retrieval, generated answer, streaming, provider, index lifecycle or load workload.", aggregation="none", artifact="record.json") for metric in METRICS}
    values["Stage latency"] = dict(status="measured", value=dict(n=1, mean=seconds, p50=seconds, p95=seconds), unit="seconds", sample_count=1,
                                  population="One local parser invocation", method="Child wall time including imports, converter/model initialization, parse, instrumentation and output writes; not isolated model inference. No provider/network/queue. Fresh process per variant; cached model files, OS file cache can warm between sequential variants.", aggregation="single sample; P50/P95 equal that observation", artifact="record.json; result-summary.json")
    values["Reliability"] = dict(status="measured", value=dict(attempts=1, completed=int(success), failed=int(not success)), unit="counts", sample_count=1,
                                 population="One parser command attempt", method="Child exit code; successful parse does not establish table fidelity.", aggregation="counts", artifact="record.json; command.log")
    values["Token usage and cost"] = dict(status="not_applicable", value=None, unit=None, sample_count=0, population="Local CPU-only parsing", method="No provider calls; cached local Docling models only.", reason="No provider calls or paid-model token usage; hardware/energy cost unmeasured.", aggregation="none", artifact="manifest.json; record.json")
    values["Ingestion and index"] = dict(status="not_applicable", value=None, unit=None, sample_count=None, population="Parser-only probe", method="No library upload, embedding, index write, update or deletion; raw extraction is retained separately.", reason="Parser-only probe does not exercise ingestion/index lifecycle.", aggregation="none", artifact="result-summary.json")
    return values


def parse_variant(variant):
    target = ROOT / variant
    target.mkdir(exist_ok=False)
    started = perf_counter()
    from docling.datamodel.accelerator_options import AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, LayoutObjectDetectionOptions, TableStructureOptions, TableFormerMode
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    from docling_ibm_models.tableformer.data_management.tf_predictor import TFPredictor
    matching = variant != "accurate-no-matching"
    options = PdfPipelineOptions(artifacts_path=MODELS, do_ocr=False, do_table_structure=True,
        do_formula_enrichment=False, do_code_enrichment=False, do_picture_description=False,
        do_picture_classification=False, do_chart_extraction=False, enable_remote_services=False,
        generate_parsed_pages=True,
        layout_options=LayoutObjectDetectionOptions.from_preset("layout_heron_default"),
        table_structure_options=TableStructureOptions(do_cell_matching=matching, mode=TableFormerMode.ACCURATE),
        accelerator_options=AcceleratorOptions(device="cpu", num_threads=4))
    kwargs = dict(pipeline_options=options)
    if variant == "pdfium-accurate-matching":
        kwargs["backend"] = PyPdfiumDocumentBackend
    format_option = PdfFormatOption(**kwargs)
    write(target / "options.json", dict(pipeline=options.model_dump(mode="json", serialize_as_any=True), backend=format_option.backend.__name__))
    original = TFPredictor.multi_table_predict
    sequence = 0

    def observe(self, iocr_page, table_bboxes, *args, **kwargs):
        nonlocal sequence
        sequence += 1
        from PIL import Image
        Image.fromarray(iocr_page["image"]).save(target / f"predictor-input-{sequence}.png")
        write(target / f"predictor-input-{sequence}.json", dict(
            page_input={key: deepcopy(value) for key, value in iocr_page.items() if key != "image"},
            image_shape=list(iocr_page["image"].shape), table_bboxes=deepcopy(table_bboxes),
            positional_options=args, keyword_options=kwargs))
        output = original(self, iocr_page, table_bboxes, *args, **kwargs)
        write(target / f"predictor-output-{sequence}.json", output)
        return output

    TFPredictor.multi_table_predict = observe
    converter = DocumentConverter(allowed_formats=[InputFormat.PDF], format_options={InputFormat.PDF: format_option})
    convert_started = perf_counter()
    result = converter.convert(SOURCE, page_range=(1, 1))
    conversion_seconds = perf_counter() - convert_started
    write(target / "document.json", result.document.export_to_dict())
    (target / "document.md").write_text(result.document.export_to_markdown())
    pages = []
    for page in result.pages:
        pages.append(dict(page_no=page.page_no, parsed_page=page.parsed_page.model_dump(mode="json") if page.parsed_page is not None else None,
                          predictions=page.predictions.model_dump(mode="json")))
    write(target / "native-pages.json", pages)
    tables = []
    expected = {"Permit": "18,870", "Handgun": "23,022", "Long Gun": "22,650", "Totals": "71,137"}
    for table in result.document.tables:
        cells = [cell.model_dump(mode="json") for cell in table.data.table_cells]
        alabama = [cell for cell in cells if cell["text"].strip() == "Alabama"]
        facts = []
        for header, value in expected.items():
            occurrences = [cell for cell in cells if value in cell["text"]]
            exact = [cell for cell in occurrences if cell["text"].strip() == value]
            aligned = [cell for cell in exact if any(cell["start_row_offset_idx"] == state["start_row_offset_idx"] and cell["end_row_offset_idx"] == state["end_row_offset_idx"] for state in alabama)]
            headers = [cell for cell in cells if cell["text"].strip() == header and any(cell["start_col_offset_idx"] <= value_cell["start_col_offset_idx"] < cell["end_col_offset_idx"] for value_cell in aligned)]
            facts.append(dict(header=header, value=value, substring_present=bool(occurrences), exact_value_cell_count=len(exact),
                              alabama_same_row_cell_count=len(aligned), matching_header_cells=headers,
                              exact_cells=exact, occurrence_coordinates=[{key: cell[key] for key in ["start_row_offset_idx", "end_row_offset_idx", "start_col_offset_idx", "end_col_offset_idx"]} for cell in occurrences]))
        tables.append(dict(table_id=table.self_ref, rows=table.data.num_rows, columns=table.data.num_cols, cell_count=len(cells),
                           standalone_alabama_cells=alabama, facts=facts))
    summary = dict(variant=variant, conversion_status=result.status.value, errors=[error.model_dump(mode="json") for error in result.errors],
                   conversion_seconds=conversion_seconds, child_seconds=perf_counter()-started,
                   tables=tables, parsed_page_count=sum(p["parsed_page"] is not None for p in pages),
                   association_scope="Exact value cells and shared Alabama row offsets are mechanical diagnostics. Header matches are same-column text candidates; they do not independently verify original-page structure. Inspect retained document and original PDF.")
    write(target / "result-summary.json", summary)
    print(json.dumps(dict(variant=variant, status=summary["conversion_status"], seconds=conversion_seconds,
                         tables=[dict(rows=t["rows"], columns=t["columns"], cells=t["cell_count"],
                                      standalone_alabama=len(t["standalone_alabama_cells"]), facts=[(f["value"], f["substring_present"], f["alabama_same_row_cell_count"]) for f in t["facts"]]) for t in tables])))


def orchestrate():
    assert not (ROOT / "manifest.json").exists(), "Each probe suite is append-only."
    model_hashes = {str(path): digest(path) for path in sorted(MODELS.rglob("*")) if path.is_file() and ".cache" not in path.parts}
    environment = {key: os.environ.get(key) for key in ["HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE", "PYTHONPATH"]}
    assert environment["HF_HUB_OFFLINE"] == "1" and environment["TRANSFORMERS_OFFLINE"] == "1"
    manifest = dict(started_at=datetime.now(timezone.utc).isoformat(), command=sys.argv,
                    commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                    source=str(SOURCE), source_sha256=digest(SOURCE), page_range=[1, 1], variants=VARIANTS,
                    script_sha256=digest(__file__), model_file_hashes=model_hashes,
                    production_source_hashes={str(path): digest(path) for path in Path("knowledgebase").rglob("*.py")},
                    device=platform.platform(), concurrency=1, threads=4, provider_calls=0,
                    environment=environment, versions={name: importlib.metadata.version(name) for name in ["docling", "docling-core", "docling-ibm-models", "docling-parse", "torch", "pypdfium2"]})
    write(ROOT / "manifest.json", manifest)
    records = []
    for variant in VARIANTS:
        command = [sys.executable, str(Path(__file__)), variant]
        started = perf_counter()
        result = subprocess.run(command, capture_output=True, text=True)
        seconds = perf_counter() - started
        target = ROOT / variant
        target.mkdir(exist_ok=True)
        (target / "command.log").write_text(result.stdout + result.stderr)
        summary = json.loads((target / "result-summary.json").read_text()) if (target / "result-summary.json").exists() else None
        record = dict(variant=variant, command=command, finished_at=datetime.now(timezone.utc).isoformat(),
                      duration_seconds=seconds, exit_code=result.returncode, parsed=result.returncode == 0,
                      counts=dict(attempts=1, successful=int(result.returncode == 0), failed=int(result.returncode != 0)),
                      commit=manifest["commit"], source_sha256=manifest["source_sha256"], script_sha256=manifest["script_sha256"],
                      environment=environment, failures_artifact="command.log", metric_inventory=inventory(variant, seconds, result.returncode == 0, summary))
        write(target / "record.json", record)
        records.append(dict(variant=variant, record=str(target / "record.json"), summary=summary))
        print(result.stdout, end="", flush=True)
        if result.returncode:
            print(f"{variant}: failed; preserved {target / 'command.log'}", flush=True)
    write(ROOT / "comparison.json", dict(manifest="manifest.json", variants=records,
                                          conclusion_scope="Only these three local variants on one digital PDF page; no downstream retrieval or generated answer measurement."))


if __name__ == "__main__":
    try:
        parse_variant(sys.argv[1]) if len(sys.argv) > 1 else orchestrate()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
