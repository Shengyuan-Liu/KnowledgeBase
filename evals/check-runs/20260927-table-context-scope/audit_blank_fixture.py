"""Audit blank positions in one known source fixture, independently of retrieval."""

from hashlib import sha256
import json
from pathlib import Path
import sys

from knowledgebase.rag.context import build_context
from knowledgebase.schemas import RetrievedChunk
from analyze_comparison import audit_serialized_context
from replay import load_module, read, source, tokens, write


ROOT = Path(__file__).parent
FROZEN = Path("evals/library-runs/20260927-dense-table-acceptance")


def main():
    directory = ROOT / sys.argv[1]
    assert not directory.exists(), "Use an append-only output name."
    directory.mkdir()
    inputs = read(ROOT / "frozen-inputs.json")
    case = next(item for item in inputs["cases"] if item["identity"] == "dense-table-single")
    child = next(row for row in case["selected"] if row["chunk"]["chunk_id"].endswith(":child:0"))
    hit = RetrievedChunk.model_validate(child)
    context = build_context([hit])
    frozen = read(FROZEN / "frozen-cases.json")
    question = next(item for item in frozen["cases"] if item["id"] == "grouped-and-blank-cells")
    labels = read(FROZEN / "metrics/fact-labels.json")["labels"]
    documents = {row["file"]["file_id"]: row for row in read(FROZEN / "index-snapshot.json")["files"]}
    metrics = load_module(FROZEN / "metrics/analyze.py", "blank_fixture_metrics")
    coverage = metrics.supplied_coverage([source(hit, 1)], question["expected_fact_ids"], labels, documents)
    audits = audit_serialized_context(dict(chunks=[hit.model_dump(mode="json")]), context)
    assert coverage["value"] == 1
    assert audits[0]["blank_cell_tuple_count"] > 0
    result = dict(scope="Explicit serialization of the already known child:0 fixture; this does not simulate retrieval for the scope-blocked question or generate an answer.",
        question=question["question"], expected_fact_ids=question["expected_fact_ids"],
        fixture_origin="frozen-inputs.json / dense-table-single / selected child:0",
        context_tokens=tokens(context), budget=4096, fits_empty_budget=tokens(context) <= 4096,
        structural_coverage=coverage, actual_serialized_context_audit=audits,
        labels={fact: dict(header_path=labels[fact]["fact"]["header_path"],
                          exact_value=labels[fact]["fact"]["exact_value"],
                          target_cell=labels[fact]["target_cell"], row_label=labels[fact]["row_label_cell"],
                          header_cells=labels[fact]["header_cells"], period_cell=labels[fact]["period_cell"])
                for fact in question["expected_fact_ids"]},
        context_sha256=sha256(context.encode()).hexdigest(),
        distinction="An explicit empty cell is encoded as an interior zero-width canonical span at the original row/column indices with both parent and leaf header paths. It is not converted to zero, omitted, or inferred from missing evidence.",
        limitations="Proves preserved source semantics in this explicit serialization fixture only. No new ranking or full Q3 request exists, and blank-cell answer correctness and citation support remain untested.")
    write(directory / "context.txt", context)
    write(directory / "evidence.json", hit.model_dump(mode="json"))
    write(directory / "audit.json", result)
    print(json.dumps(dict(context_tokens=result["context_tokens"], structural_coverage=coverage["value"],
                         point_count=len(coverage["facts"]), serialized_blank_cell_tuple_count=audits[0]["blank_cell_tuple_count"]), indent=2))


if __name__ == "__main__":
    main()
