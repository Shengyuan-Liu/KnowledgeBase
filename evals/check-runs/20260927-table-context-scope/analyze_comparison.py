"""Measure source-preserving context serialization on one frozen offline replay."""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import statistics
import sys


ROOT = Path(__file__).parent
FROZEN = Path("evals/library-runs/20260927-dense-table-acceptance")
METRICS = ["Recall@K", "Precision@K", "Hit Rate@K", "MRR", "NDCG@K", "Final evidence coverage",
           "Answer correctness", "Faithfulness", "Answer completeness", "Answer relevance",
           "Citation support", "Citation coverage", "Abstention", "First-answer-delta latency",
           "Complete-response latency", "Stage latency", "Token usage and cost", "Reliability",
           "Concurrency and throughput", "Ingestion and index"]


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    with path.open("x") as output:
        output.write(value if isinstance(value, str) else json.dumps(value, indent=2) + "\n")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def distribution(values):
    values = sorted(values)
    def percentile(fraction):
        position = (len(values) - 1) * fraction
        low = int(position)
        return values[low] + (values[min(low + 1, len(values) - 1)] - values[low]) * (position - low)
    return dict(n=len(values), mean=statistics.mean(values), p50=percentile(.5), p95=percentile(.95),
                unit="seconds", percentile_method="linear interpolation")


def audit_serialized_context(evidence, context):
    blocks = re.split(r"\n\n(?=\[\d+\]\nSource metadata:)", context) if context else []
    assert len(blocks) == len(evidence["chunks"])
    rows = []
    for number, (row, block) in enumerate(zip(evidence["chunks"], blocks, strict=True), 1):
        chunk, pdf = row["chunk"], row["pdf"]
        assert block.startswith(f"[{number}]\nSource metadata: ")
        body = block.split("\nExcerpt:\n", 1)[1].split("\nPDF physical pages:", 1)[0]
        assert body == chunk["text"]
        assert f"\nExcerpt canonical offsets: {chunk['start_offset']}:{chunk['end_offset']}" in block
        expected_pages = ", ".join(str(page + 1) for page in sorted({region["page_index"] for region in pdf["regions"]}))
        assert f"\nPDF physical pages: {expected_pages}\n" in block
        tables = [{key: value for key, value in table.items() if key != "column_header_spans"}
                  for table in pdf["tables"]]
        if tables:
            line = next(line for line in block.splitlines() if line.startswith("Table cells ["))
            encoded = line.split("partial cells may intersect excerpt edges: ", 1)[1]
            assert json.loads(encoded) == tables
        else:
            assert "\nTable cells [" not in block
        for extra in pdf["supplements"]:
            pages = sorted({region["page_index"] + 1 for region in extra["regions"]})
            serialized = (f"\nSeparately located {extra['role']} for {extra['table_id']} "
                          f"(pages {pages}, offsets {extra['start_offset']}:{extra['end_offset']}):\n{extra['text']}")
            assert serialized in block
        rows.append(dict(source_id=number, chunk_id=chunk["chunk_id"], body_exact=True,
                         physical_pages_exact=True, canonical_offsets_exact=True,
                         table_metadata_json_round_trip=True, all_supplement_text_and_offsets_exact=True,
                         cell_tuple_count=sum(len(table["cells"]) for table in tables),
                         blank_cell_tuple_count=sum(cell[-1] == cell[-2] for table in tables for cell in table["cells"]),
                         supplement_count=len(pdf["supplements"])))
    return rows


def measured(value, unit, count, population, method, aggregation="none"):
    return dict(status="measured", value=value, unit=unit, sample_count=count, population=population,
                method=method, aggregation=aggregation, artifact="comparison.json")


def omitted(reason):
    return dict(status="not_applicable", value=None, unit=None, sample_count=None,
                population="offline context/scope replay", method="not exercised", aggregation="none",
                reason=reason, artifact="comparison.json")


def main():
    baseline_name, after_name, analysis_name = sys.argv[1:]
    output = ROOT / analysis_name
    assert not output.exists(), "Use a new output directory for every analysis attempt."
    output.mkdir()
    baseline = read(ROOT / baseline_name / "manifest.json")
    after = read(ROOT / after_name / "manifest.json")
    inputs = read(ROOT / "frozen-inputs.json")
    assert baseline["frozen_artifact_hashes"] == after["frozen_artifact_hashes"]
    metrics = load_module(FROZEN / "metrics/analyze.py", "frozen_metrics_analysis")
    labels = read(FROZEN / "metrics/fact-labels.json")["labels"]
    frozen = read(FROZEN / "frozen-cases.json")
    index = read(FROZEN / "index-snapshot.json")
    children = {chunk["chunk_id"]: chunk for document in index["files"] for chunk in document["chunks"]}
    comparison = []
    baseline_by_id = {row["identity"]: row for row in baseline["results"]}
    after_by_id = {row["identity"]: row for row in after["results"]}
    candidate_cases = []
    for item in inputs["cases"]:
        identity = item["identity"]
        before, later = baseline_by_id[identity], after_by_id[identity]
        assert before["selected_rank_order"] == later["selected_rank_order"]
        assert before["expanded_order"] == later["expanded_order"]
        audits = {}
        for name, phase in [("baseline", baseline_name), ("after", after_name)]:
            audits[name] = audit_serialized_context(read(ROOT / phase / f"{identity}-evidence.json"),
                (ROOT / phase / f"{identity}-context.txt").read_text())
        facts = item["case"]["expected_fact_ids"]
        row = dict(identity=identity, expected_fact_ids=facts,
                   selected_rank_order=before["selected_rank_order"],
                   original_recorded_candidates_exist=bool(item["selected"]),
                   before=dict(tokens=before["evidence_tokens"], packed_ids=before["packed_order"],
                               facts=before["final_structural_coverage"]["facts"],
                               scope=before["scope"]["result"]),
                   after=dict(tokens=later["evidence_tokens"], packed_ids=later["packed_order"],
                              facts=later["final_structural_coverage"]["facts"],
                              scope=later["scope"]["result"]),
                   actual_serialized_context_audit=audits,
                   answer_generated=False,
                   limitation=("No original retrieval candidates exist because the live request stopped at scope resolution. Scope is retested; retrieval and answer behavior remain untested."
                               if not item["selected"] else "The original selected ranks and planned queries are fixed; no new retrieval, sufficiency decision or answer generation is exercised."))
        if item["selected"]:
            row["frozen_candidate_metrics"] = metrics.retrieval_scores(before["selected_rank_order"], facts, children, labels)
            candidate_cases.append(row)
        comparison.append(row)
    coverage_counts = {}
    for phase in ["before", "after"]:
        coverage_counts[phase] = dict(covered=sum(fact["fully_covered"] for row in candidate_cases for fact in row[phase]["facts"]),
                                      total=sum(len(row[phase]["facts"]) for row in candidate_cases))
        coverage_counts[phase]["ratio"] = coverage_counts[phase]["covered"] / coverage_counts[phase]["total"]
    inventory = {metric: omitted("No model answer or provider call is made; offline serialization cannot establish live quality, latency, billing, or release acceptance.") for metric in METRICS}
    for metric in METRICS[:5]:
        value = statistics.mean(row["frozen_candidate_metrics"][metric] for row in candidate_cases)
        inventory[metric] = measured(dict(before=value, after=value), "ratio", len(candidate_cases),
            "Four original question/mode selections with recorded retrieval candidates; two original scope failures excluded and separately disclosed",
            "Re-score unchanged K=5 selections against frozen source-bound facts (Recall) and exhaustive binary child labels within the one-file 10-child corpus (Precision, Hit, MRR, NDCG). Precision divides by five. MRR cutoff five; misses zero. Binary gain and log2 rank discount. These are frozen-rank diagnostics, not new retrieval performance.", "macro mean")
    inventory["Final evidence coverage"] = measured(coverage_counts, "ratio with point numerator/denominator", len(candidate_cases),
        "Sixteen requested fact instances across four original requests with recorded candidates",
        "Exact source-bound target cells, row labels, complete parent/leaf header paths and period cells must occur in packed evidence with matching tuples and source text; prose requires all original phrases. Audit the actual serialized body/pages/offsets/table JSON/supplements for lossless correspondence. Count all required points without partial credit.", "micro across requested fact instances")
    inventory["Stage latency"] = measured({phase: {"packing": distribution([row["local_pack_seconds"] for row in manifest["results"] if not row["scope_only_without_candidates"]]),
        "scope": distribution([row["local_scope_seconds"] for row in manifest["results"]])} for phase, manifest in [("before", baseline), ("after", after)]},
        "seconds", dict(packing_per_phase=4, scope_per_phase=6), "One sequential local call per frozen input per phase",
        "perf_counter around pack_evidence and separately document_references plus resolve_document_scope. Tokenizer preloaded; includes actual context formatting/token counting; excludes model loading, queueing, retrieval, network and answer generation. Tiny single-pass diagnostics do not establish production latency or speedup.", "arithmetic mean and linearly interpolated p50/p95")
    inventory["Token usage and cost"] = measured(dict(evidence_tokens={row["identity"]: dict(before=row["before"]["tokens"], after=row["after"]["tokens"]) for row in comparison},
        provider_usage=dict(status="not_applicable", value=None, reason="No provider invoked"),
        provider_cost=dict(status="not_applicable", value=None, reason="No provider invoked")),
        "local cl100k_base tokens; no provider billing", 12, "Six serialized local evidence contexts per phase",
        "Actual numbered build_context output encoded with cl100k_base at unchanged max_tokens=4096. No API input/output tokens or model billing inferred.")
    inventory["Reliability"] = measured(dict(baseline_cases=6, after_cases=6, local_case_errors=0,
        baseline_preparation_attempts=2, baseline_preparation_failed_attempts=1,
        failure="baseline-1 asserted equality of the planned caller's human-readable not-found message with direct scope resolution. All substantive scope fields matched; baseline-2 compares those separately and preserves the message difference.",
        provider_attempts=0), "counts", 12, "Completed local replay case executions in successful baseline-2 and after phases",
        "Successful case executions are not live HTTP reliability. Retain baseline-1 failure and partial outputs; no provider retry occurred.")
    inventory["Concurrency and throughput"] = omitted("Local replay is sequential (concurrency one); no HTTP workload, load capacity or production throughput is exercised.")
    inventory["Ingestion and index"] = omitted("Use the exact frozen one-file extraction and 10-child/5-parent index snapshot read-only; no parser, upload, reindex, update or deletion is performed.")
    manifest = dict(scope="Offline replay of unchanged candidate selections and local scope parsing; no paid calls or live answer rerun",
        frozen_artifact_hashes=baseline["frozen_artifact_hashes"], baseline_source_hashes=baseline["source_hashes"],
        after_source_hashes=after["source_hashes"], baseline_product_commit="b792448", after_code_commit=after["commit"],
        reviewer="Codex agent /root/context_replay; programmatic source-bound checks, not a human reviewer or paid LLM judge",
        phases=dict(before=baseline_name, after=after_name), cases=comparison, final_coverage=coverage_counts,
        scope_resolved=dict(before=sum(row["before"]["scope"]["status"] == "resolved" for row in comparison),
                            after=sum(row["after"]["scope"]["status"] == "resolved" for row in comparison), total=6),
        metric_inventory=inventory,
        unchanged=dict(corpus=True, questions=True, fact_annotations=True, selected_ranks=True, evidence_budget=4096,
                       parser=True, index=True, retrieval_results=True),
        limits=["New answers, faithfulness, supported citations and abstention behavior remain unmeasured after the fix.",
                "The grouped/blank-cell question has no recorded candidates, so new local scope success cannot establish retrieval or blank-cell answer correctness.",
                "The four candidate-bearing comparisons freeze prior planner queries and selections. New context can change sufficiency decisions and future planned queries in a live run.",
                "Original failed acceptance answers remain immutable; no old quality score is replaced by offline evidence coverage.",
                "The baseline-1 harness assertion failure and partial outputs remain available; baseline-2 completed."])
    write(output / "comparison.json", manifest)
    write(output / "measurement.json", dict(scope=manifest["scope"], metric_inventory=inventory))
    print(json.dumps(dict(coverage=coverage_counts, scope_resolved=manifest["scope_resolved"],
                         cases=[dict(identity=row["identity"], before_tokens=row["before"]["tokens"], after_tokens=row["after"]["tokens"]) for row in comparison]), indent=2))


if __name__ == "__main__":
    main()
