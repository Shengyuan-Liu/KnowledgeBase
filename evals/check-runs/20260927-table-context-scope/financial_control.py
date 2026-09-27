"""Preserve values, period associations and units on six frozen financial cases."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter

from knowledgebase.rag.context import build_context
from knowledgebase.rag.packing import pack_evidence
from knowledgebase.rag.pdf_evidence import pdf_evidence
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.schemas import ChildChunk, RetrievedChunk, RetrievalDiagnostics, StructuredChunk

from analyze_comparison import METRICS, audit_serialized_context, distribution, measured, omitted
from replay import load_module, read, tokens, write


ROOT = Path(__file__).parent
LIVE = Path("evals/library-runs/20260927-v2-pdf-live")
OLD = Path("evals/check-runs/20260927-pdf-evidence-packing")


def cell_tuple(cell):
    return [cell[key] for key in ["row_start", "row_end", "column_start", "column_end", "start_offset", "end_offset"]]


def contains(span, cell):
    return span["start_offset"] <= cell["start_offset"] and cell["end_offset"] <= span["end_offset"]


def labels_for(extraction):
    table = next(block["table"] for block in extraction["blocks"] if block.get("table"))
    definitions = dict(apple_sales_q=("Total net sales", "94,930", 1, "Three Months Ended"),
                       apple_sales_y=("Total net sales", "391,035", 3, "Twelve Months Ended"),
                       apple_income_q=("Net income", "14,736", 1, "Three Months Ended"),
                       apple_income_y=("Net income", "93,736", 3, "Twelve Months Ended"))
    labels = {}
    for identity, (row_name, value, column, period) in definitions.items():
        alternatives = []
        headers = [cell for cell in table["cells"] if cell["column_header"]
                   and cell["column_start"] <= column < cell["column_end"]]
        assert [cell["text"] for cell in headers] == [period, "September 28, 2024"]
        for target in table["cells"]:
            if target["column_start"] != column or target["text"].replace("$", "").strip() != value:
                continue
            label = next(cell for cell in table["cells"] if cell["column_start"] == 0
                         and cell["row_start"] == target["row_start"])
            if not label["text"].startswith(row_name):
                continue
            alternatives.append(dict(row_label=label, target=target, headers=headers))
        assert alternatives
        labels[identity] = dict(value=value, row_label=row_name, period=period,
                                column=column, date="September 28, 2024", alternatives=alternatives)
    unit_text = "(In millions, except number of shares, which are reflected in thousands, and per-share amounts)"
    unit_start = extraction["text"].index(unit_text)
    labels["apple_units"] = dict(text=unit_text, start_offset=unit_start, end_offset=unit_start + len(unit_text))
    return table["table_id"], labels


def coverage(result, facts, table_id, labels):
    checks = {}
    for identity in dict.fromkeys([*facts, "apple_units"]):
        choices = []
        for number, hit in enumerate(result["chunks"], 1):
            pdf = hit["pdf"]
            spans = [hit["chunk"], *pdf["supplements"]]
            if identity == "apple_units":
                matches = [span for span in spans if contains(span, labels[identity])
                           and labels[identity]["text"] in span["text"]]
                choices.append(dict(source_id=number, complete=bool(matches),
                                    unit_source_spans=[dict(start_offset=span["start_offset"], end_offset=span["end_offset"]) for span in matches]))
                continue
            table = next((table for table in pdf["tables"] if table["table_id"] == table_id), None)
            if not table:
                continue
            for alternative in labels[identity]["alternatives"]:
                cells = [alternative["row_label"], alternative["target"], *alternative["headers"]]
                cell_checks = [dict(text=cell["text"], tuple=cell_tuple(cell),
                    metadata_present=cell_tuple(cell) in table["cells"],
                    exact_text_supplied=any(contains(span, cell) and cell["text"] in span["text"] for span in spans),
                    page_indices=sorted({region["page_index"] for region in cell["regions"]})) for cell in cells]
                choices.append(dict(source_id=number, cells=cell_checks,
                    complete=all(cell["metadata_present"] and cell["exact_text_supplied"] and cell["page_indices"] == [0] for cell in cell_checks)))
        checks[identity] = dict(complete=any(choice["complete"] for choice in choices), source_checks=choices)
    return checks


def main():
    output = ROOT / sys.argv[1]
    assert not output.exists(), "Use a new output directory per attempt."
    output.mkdir()
    snapshot = read(LIVE / "index-snapshot.json")
    document = next(item for item in snapshot["files"] if item["file"]["file_name"] == "apple-fy24.pdf")
    rows = [row for row in read(OLD / "frozen-inputs.json")["rows"]
            if row["case_id"] in {"apple-sales", "apple-income", "apparent-conflict"}]
    extraction = PdfExtraction.model_validate(document["extraction"])
    children = {row["chunk_id"]: ChildChunk.model_validate(row) for row in document["chunks"]}
    parents = {row["parent_id"]: row for row in document["parents"]}
    table_id, labels = labels_for(document["extraction"])
    write(output / "source-bound-labels.json", labels)
    baseline_context = load_module(ROOT / "baseline-code/context.py", "financial_baseline_context")
    baseline_packing = load_module(ROOT / "baseline-code/packing.py", "financial_baseline_packing")
    baseline_packing.build_context = baseline_context.build_context
    baseline_packing.PDF_CONTEXT_FORMAT = baseline_context.PDF_CONTEXT_FORMAT
    assert sha256(Path("knowledgebase/rag/pdf_evidence.py").read_bytes()).hexdigest() == sha256((ROOT / "baseline-code/pdf_evidence.py").read_bytes()).hexdigest()
    all_results = []
    for row in rows:
        identity = row["case_id"] + "-" + row["arm"]
        selected = [RetrievedChunk.model_validate({**hit, "chunk": children[hit["chunk"]["chunk_id"]]}) for hit in row["selected"]]
        regions = {}
        for child in selected:
            parent_id = child.parent_id
            if parent_id is None:
                regions[child.chunk.chunk_id] = child.model_copy(deep=True)
            elif parent_id in regions:
                regions[parent_id].matched_child_ids.append(child.chunk.chunk_id)
            else:
                parent = parents[parent_id]
                regions[parent_id] = child.model_copy(update={"chunk": StructuredChunk(chunk_id=parent_id,
                    **{key: value for key, value in parent.items() if key != "parent_id"}), "matched_child_ids": [child.chunk.chunk_id]})
        for hit in [*selected, *regions.values()]:
            hit.pdf = pdf_evidence(extraction, hit.chunk.start_offset, hit.chunk.end_offset)
        write(output / f"{identity}-inputs.json", dict(selected=[hit.model_dump(mode="json") for hit in selected],
            expanded=[hit.model_dump(mode="json") for hit in regions.values()], diagnostics=row["diagnostics"]))
        result_row = dict(identity=identity, question=row["question"], requested_facts=row["facts"],
                          selected_rank_order=[hit.chunk.chunk_id for hit in selected])
        for phase, pack, render in [("before", baseline_packing.pack_evidence, baseline_context.build_context),
                                    ("after", pack_evidence, build_context)]:
            started = perf_counter()
            packed = pack(deepcopy(selected), deepcopy(list(regions.values())), RetrievalDiagnostics.model_validate(row["diagnostics"]))
            elapsed = perf_counter() - started
            context = render(packed.chunks)
            assert tokens(context) == packed.diagnostics.evidence_tokens <= 4096
            result = packed.model_dump(mode="json")
            for hit in result["chunks"]:
                for span in [hit["chunk"], *hit["pdf"]["supplements"]]:
                    assert span["text"] == extraction.text[span["start_offset"]:span["end_offset"]]
            context_audit = audit_serialized_context(result, context)
            point_checks = coverage(result, row["facts"], table_id, labels)
            assert all(check["complete"] for check in point_checks.values()), (identity, phase, point_checks)
            write(output / f"{identity}-{phase}-evidence.json", result)
            write(output / f"{identity}-{phase}-context.txt", context)
            result_row[phase] = dict(tokens=packed.diagnostics.evidence_tokens,
                packed_ids=[hit.chunk.chunk_id for hit in packed.chunks],
                coverage=point_checks, context_audit=context_audit, packing_seconds=elapsed,
                requested_points_covered=sum(point_checks[fact]["complete"] for fact in row["facts"]),
                requested_points_total=len(row["facts"]))
        all_results.append(result_row)
    aggregate = {phase: dict(covered=sum(row[phase]["requested_points_covered"] for row in all_results),
                            total=sum(row[phase]["requested_points_total"] for row in all_results)) for phase in ["before", "after"]}
    inventory = {metric: omitted("Financial control exercises only local serialization and packing of six fixed historical selections; no provider or new retrieval, model answer, ingestion or load test.") for metric in METRICS}
    inventory["Final evidence coverage"] = measured(aggregate, "covered requested fact instances / total", 6,
        "Six financial case/mode pairs; 16 requested facts, plus an explicit unit-preservation check on all six",
        "Require exact target and row-label tuples, period-parent/date-leaf headers at the matching column, unchanged canonical slices and physical page one, with full units and exceptions. Audit serialized JSON and all source bodies/supplements.", "micro fact coverage")
    inventory["Token usage and cost"] = measured(dict(context_tokens={row["identity"]: {phase: row[phase]["tokens"] for phase in ["before", "after"]} for row in all_results},
        provider_usage=dict(status="not_applicable", value=None, reason="No provider invoked"),
        provider_cost=dict(status="not_applicable", value=None, reason="No provider invoked")), "local cl100k_base tokens", 12,
        "Six source contexts per phase", "Actual numbered serialized source text; no provider billing inferred")
    inventory["Stage latency"] = measured({phase: distribution([row[phase]["packing_seconds"] for row in all_results]) for phase in ["before", "after"]},
        "seconds", 12, "Six local pack_evidence calls per phase", "perf_counter around packing only; tokenizer preloaded; no model loading, queues, retrieval, network or generation. Single-pass diagnostics do not establish production latency.", "mean and interpolated p50/p95")
    inventory["Reliability"] = measured(dict(local_case_checks_passed=12, local_case_check_failures=0, provider_attempts=0),
        "counts", 12, "Six before and six after local fixture checks", "All requested values/periods and explicit units preserved; this is not HTTP success or model-answer reliability")
    write(output / "comparison.json", dict(baseline_commit="b792448", frozen_inputs=str(OLD / "frozen-inputs.json"),
        frozen_hashes={str(path): sha256(path.read_bytes()).hexdigest() for path in
            [OLD / "frozen-inputs.json", LIVE / "index-snapshot.json", LIVE / "anchor-labels.json"]},
        source_hashes={str(path): sha256(path.read_bytes()).hexdigest() for path in
            [Path("knowledgebase/rag/context.py"), Path("knowledgebase/rag/packing.py"), Path("knowledgebase/rag/pdf_evidence.py")]},
        source_binding_note="The existing financial facts and source annotations are unchanged. This control additionally checks exact table row/column/header tuples and the full units sentence so unchanged substrings alone do not establish preserved meaning.",
        rows=all_results, aggregate=aggregate, metric_inventory=inventory,
        limitations="Known-child and larger-parent identities may differ when more context fits. Test semantic source coverage and provenance, not exact old child identity. No newly generated financial answer or citation behavior is evaluated."))
    print(json.dumps(dict(coverage=aggregate, cases=[dict(identity=row["identity"], before_tokens=row["before"]["tokens"],
        after_tokens=row["after"]["tokens"], before_ids=row["before"]["packed_ids"], after_ids=row["after"]["packed_ids"]) for row in all_results]), indent=2))


if __name__ == "__main__":
    main()
