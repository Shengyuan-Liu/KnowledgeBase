"""Audit frozen evidence, aggregate observed calls and retain all metric statuses."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import statistics

import tiktoken
from record_check import METRICS

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "20260927-blank-plan-acceptance"


def read(path):
    return json.loads(path.read_text())


def distribution(values):
    values = sorted(values)
    def percentile(p):
        rank = (len(values)-1)*p
        low = int(rank)
        return values[low] + (values[min(low+1, len(values)-1)]-values[low])*(rank-low)
    return dict(n=len(values), mean=statistics.mean(values), p50=percentile(.5), p95=percentile(.95),
                percentile_method="linear interpolation", values=values)


if __name__ == "__main__":
    assert not (ROOT / "measurement.json").exists()
    cases = read(ROOT / "cases.json")
    rows = [read(ROOT / (c["id"]+".json")) for c in cases]
    review = read(ROOT / "review.json")["cases"]
    events = [json.loads(line) for line in (ROOT / "provider-events.jsonl").read_text().splitlines()]
    complete = [e for e in events if e["kind"] == "complete"]
    errors = [e for e in events if e["kind"] == "error"]
    old = read(BASE / "grouped-and-blank-cells-planned.json")
    context = old["answer"]["retrieval"]["planning"]["assessment"]["context"]
    extraction = read(BASE / "index-snapshot.json")["files"][0]["extraction"]["text"]
    audits = []
    for row in rows:
        assert row["assessment"]["context"] == context
        refs = [ref for point in row["assessment"]["requirements"] for ref in [*point["references"], *point.get("table_context", [])]]
        assert all(extraction[ref["start_offset"]:ref["end_offset"]] == ref["quote"] for ref in refs)
        generation = [e for e in events if e["case"] == row["case"]["id"] and e["kind"] == "start" and "text" not in e["input"]]
        assert len(generation) == 1 and context in generation[0]["input"]["input"][0]["content"]
        audits.append(dict(case_id=row["case"]["id"], identical_context=True,
            exact_reference_count=len(refs), generation_context_verified=True,
            note="Exact offsets and valid citations do not establish correct year or semantic support."))
    spec = importlib.util.spec_from_file_location("baseline_metrics", BASE / "metrics/analyze.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    labels = read(BASE / "frozen-fact-labels.json")["labels"]
    documents = {d["file"]["file_id"]: d for d in read(BASE / "index-snapshot.json")["files"]}
    coverage = [dict(case_id=c["id"], result=module.supplied_coverage(old["answer"]["sources"], c["available_fact_ids"], labels, documents))
                for c in cases if c["available_fact_ids"]]
    assert all(c["result"]["value"] == 1 for c in coverage)
    inventory = {m: dict(status="not_applicable",value=None,unit=None,sample_count=None,
        reason="Fixed-context component replay; no new retrieval, streaming HTTP, ingestion or load test.",
        population="four component cases",method="not exercised",aggregation="none",artifact="protocol.md") for m in METRICS}
    def measured(name, value, unit, count, method, artifact="review.json"):
        inventory[name] = dict(status="measured", value=value, unit=unit, sample_count=count, reason=None,
            population="four frozen development cases", method=method, aggregation="pooled observations", artifact=artifact)
    measured("Final evidence coverage", dict(covered=10, expected=10, fraction=1, per_case=coverage),
             "available source-fact occurrences", 10, "Exact source-bound row/header/cell spans; three absent facts have no gold evidence and are not zero-recall cases.", "frozen-evidence.json")
    points = [p for case in review for p in case["expected_point_review"]]
    claims = [p for case in review for p in case["factual_claims"]]
    for metric in ["Answer correctness", "Answer completeness"]:
        measured(metric, dict(score=sum(p["score"] for p in points), denominator=len(points), fraction=sum(p["score"] for p in points)/len(points)),
                 "expected answer points", len(points), "Frozen 0/0.5/1 rubric; includes three expected explicit limitations; single Codex review.")
    for metric in ["Faithfulness", "Citation support", "Citation coverage"]:
        measured(metric, dict(supported=sum(p["supported"] for p in claims), denominator=len(claims),fraction=sum(p["supported"] for p in claims)/len(claims)),
            "factual claim groups", len(claims), "Each factual sentence/list item checked for actual source support, including period. One correct missing-explanation statement reviewed separately.")
    measured("Answer relevance", dict(score=4,denominator=4), "cases", 4, "Directly responds to requested dimensions without unrelated material; wrong facts/periods scored separately.")
    measured("Abstention", dict(appropriate_full_abstention=dict(numerator=0,denominator=1),
        incorrect_full_abstention_on_fully_answerable=dict(numerator=0,denominator=2),
        correct_partial_limitation=dict(numerator=1,denominator=1)), "case counts",4,
        "Missing-year case fully unanswerable; original/paraphrase fully answerable; factual-condition partially answerable.")
    measured("Stage latency", dict(component_total=distribution([r["component_complete_seconds"] for r in rows]),
        stages={s:distribution([r["stage_seconds"][s] for r in rows]) for s in rows[0]["stage_seconds"]},
        sdk_calls=distribution([e["seconds"] for e in complete])), "seconds",4,
        "Sequential wall time around each production component; provider queue included, not isolated; no local model loading. Component total is not API/HTTP response latency.", "provider-events.jsonl")
    usage = {k:sum(e["result"]["usage"][k] for e in complete) for k in ["input_tokens","output_tokens","total_tokens"]}
    measured("Token usage and cost", dict(provider_usage=usage, evidence_tokens=len(tiktoken.get_encoding("cl100k_base").encode_ordinary(context)),
        billed_cost=dict(status="unavailable",value=None,reason="No billing statement or authoritative charge returned.")), "provider tokens and local context tokens", len(complete), "Actual SDK usage; cl100k_base evidence count is local, not billed cost.", "provider-events.jsonl")
    measured("Reliability", dict(cases=4, completed=sum(r["status"]=="completed" for r in rows),errors=len(errors),
        provider_calls=len(complete)+len(errors),provider_completions=len(complete),timeouts=0,retries=0), "counts",4,"Count all cases and SDK attempts; no automatic retries.","provider-events.jsonl")
    inventory["Concurrency and throughput"]["reason"] = "Concurrency fixed at one; short sequential component sample does not measure serving throughput or load capacity."
    result = dict(code_commit=read(ROOT/"preparation.json")["code_commit"], protocol="protocol.md",
        classification_pass_count=sum(c["classification_pass"] for c in review),case_gate_pass_count=sum(c["case_gate_pass"] for c in review),case_count=4,
        acceptance="failed",models=sorted({e["result"]["model"] for e in complete}),
        context_sha256=sha256(context.encode()).hexdigest(), evidence_audits=audits, metric_inventory=inventory,
        limits="One attempt per question, one Codex reviewer, frozen evidence, final-round assessor boundary; no full API or multi-round acceptance.")
    (ROOT/"measurement.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(dict(acceptance=result["acceptance"], classification_pass=result["classification_pass_count"],
        case_gate_pass=result["case_gate_pass_count"], answer_points=inventory["Answer correctness"]["value"],
        faithfulness=inventory["Faithfulness"]["value"],usage=usage,models=result["models"],
        timings=inventory["Stage latency"]["value"]["component_total"]),indent=2))
