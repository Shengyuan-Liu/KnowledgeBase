"""Measure a matched component run, retaining errors and semantic review limits."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import statistics

import tiktoken
from record_check import METRICS

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "20260928-planner-fact-scope-acceptance"
CORPUS = ROOT.parent / "20260927-blank-plan-acceptance"


def read(path):
    return json.loads(path.read_text())


def distribution(values):
    values = sorted(values)
    if not values:
        return dict(status="unavailable", n=0, reason="No completed observations.")
    def percentile(p):
        rank = (len(values)-1)*p
        low = int(rank)
        return values[low] + (values[min(low+1, len(values)-1)]-values[low])*(rank-low)
    return dict(n=len(values), mean=statistics.mean(values), p50=percentile(.5), p95=percentile(.95),
                percentile_method="linear interpolation", values=values)


if __name__ == "__main__":
    assert not (ROOT / "measurement.json").exists()
    assert (ROOT/"cases.json").read_bytes() == (BASE/"cases.json").read_bytes()
    assert (ROOT/"run.py").read_bytes() == (BASE/"run.py").read_bytes()
    assert (ROOT/"frozen-evidence.json").read_bytes() == (BASE/"frozen-evidence.json").read_bytes()
    cases = read(ROOT / "cases.json")
    rows = [read(ROOT / (c["id"]+".json")) for c in cases]
    review = read(ROOT / "review.json")["cases"]
    previous = {c["case_id"]:c for c in read(BASE/"review.json")["cases"]}
    events = [json.loads(line) for line in (ROOT / "provider-events.jsonl").read_text().splitlines()]
    complete = [e for e in events if e["kind"] == "complete"]
    errors = [e for e in events if e["kind"] == "error"]
    old = read(CORPUS / "grouped-and-blank-cells-planned.json")
    context = old["answer"]["retrieval"]["planning"]["assessment"]["context"]
    extraction = read(CORPUS / "index-snapshot.json")["files"][0]["extraction"]["text"]
    audits = []
    for row in rows:
        if "assessment" not in row:
            audits.append(dict(case_id=row["case"]["id"], status="unavailable", reason="Case failed before assessment."))
            continue
        assert row["assessment"]["context"] == context
        refs = [ref for point in row["assessment"]["requirements"] for ref in [*point["references"], *point.get("table_context", [])]]
        assert all(extraction[ref["start_offset"]:ref["end_offset"]] == ref["quote"] for ref in refs)
        generation = [e for e in events if e["case"] == row["case"]["id"] and e["kind"] == "start" and "text" not in e["input"]]
        if generation:
            assert len(generation) == 1 and context in generation[0]["input"]["input"][0]["content"]
        else:
            assert all(p["status"]=="missing" for p in row["assessment"]["requirements"])
        audits.append(dict(case_id=row["case"]["id"], identical_assessment_context=True,
            exact_reference_count=len(refs), generation_context_verified=bool(generation),
            generation_skipped=not generation, note="Exact offsets do not prove semantic support."))
    spec = importlib.util.spec_from_file_location("corpus_metrics", CORPUS / "metrics/analyze.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    labels = read(CORPUS / "frozen-fact-labels.json")["labels"]
    documents = {d["file"]["file_id"]: d for d in read(CORPUS / "index-snapshot.json")["files"]}
    coverage = [dict(case_id=r["case"]["id"], result=module.supplied_coverage(old["answer"]["sources"], r["case"]["available_fact_ids"], labels, documents))
                for r in rows if r["case"]["available_fact_ids"] and "assessment" in r]
    covered = sum(p["fully_covered"] for c in coverage for p in c["result"]["facts"])
    inventory = {m: dict(status="not_applicable",value=None,unit=None,sample_count=None,
        reason="Fixed-context component run; no new retrieval, streaming HTTP, ingestion or load test.",
        population="four component cases",method="not exercised",aggregation="none",artifact="protocol.md") for m in METRICS}
    def measured(name, value, unit, count, method, artifact="review.json"):
        inventory[name] = dict(status="measured", value=value, unit=unit, sample_count=count, reason=None,
            population="four frozen development cases", method=method, aggregation="pooled observations", artifact=artifact)
    measured("Final evidence coverage", dict(covered=covered, expected=10, fraction=covered/10, per_case=coverage),
             "available source-fact occurrences", 10, "Exact row/header/cell bindings. Three absent facts have no gold evidence; missing-year is not a zero-recall case.", "frozen-evidence.json")
    points = [p for case in review for p in case["expected_point_review"]]
    claims = [p for case in review for p in case["factual_claims"]]
    scored = [p for p in points if p["score"] is not None]
    for metric in ["Answer correctness", "Answer completeness"]:
        measured(metric, dict(score=sum(p["score"] for p in scored), denominator=len(scored),
            fraction=sum(p["score"] for p in scored)/len(scored),
            unavailable_points=len(points)-len(scored),
            all_intended_delivery=dict(score=sum(p["delivered_score"] for p in points),denominator=len(points))),
            "expected answer points", len(scored), "Frozen 0/0.5/1 rubric; completed-answer semantic scores only. Failed-case quality is unavailable, while its undelivered points remain in the all-intended denominator.")
    for metric, field in [("Faithfulness","supported"), ("Citation support","citation_supported"), ("Citation coverage","citation_supported")]:
        measured(metric, dict(supported=sum(p[field] for p in claims), denominator=len(claims),fraction=sum(p[field] for p in claims)/len(claims) if claims else None),
            "factual claim groups", len(claims), "Factual sentence/list-item support including period; absence statements separately reviewed. A claim-free refusal contributes no factual-claim denominator.")
    relevant = [c["answer_relevance"] for c in review if c["answer_relevance"] is not None]
    measured("Answer relevance", dict(score=sum(relevant),denominator=len(relevant),unavailable_cases=len(review)-len(relevant)), "completed cases",len(relevant), "Addresses requested dimensions without unrelated material; failed-case relevance is unavailable.")
    partial = next(c for c in review if c["case_id"] == "factual-condition")
    partial_available = partial["semantic_quality_status"] == "measured"
    measured("Abstention", dict(appropriate_full_abstention=dict(numerator=sum(c["full_abstention"] for c in review if c["case_id"]=="missing-year"),denominator=1),
        incorrect_full_abstention_on_fully_answerable=dict(numerator=sum(c["full_abstention"] for c in review if c["case_id"] in ["original-rule","paraphrased-rule"]),denominator=2),
        correct_partial_limitation=dict(status="measured" if partial_available else "unavailable",
            numerator=int(partial["explicit_partial_limitation"]) if partial_available else None,
            denominator=1 if partial_available else None,
            reason=None if partial_available else "Factual-condition failed before an answer."),
        intended_partial_cases=1,delivered_partial_limitations=int(partial["explicit_partial_limitation"])), "case counts",4,
        "Missing-year wholly unanswerable; original/paraphrase fully answerable; factual-condition partially answerable. Failed requests are not counted as abstentions.")
    stages = sorted({s for r in rows for s in r["stage_seconds"]})
    measured("Stage latency", dict(component_total=distribution([r["component_complete_seconds"] for r in rows]),
        stages={s:distribution([r["stage_seconds"][s] for r in rows if s in r["stage_seconds"]]) for s in stages},
        sdk_calls=distribution([e["seconds"] for e in complete])), "seconds",len(rows),
        "Sequential wall time; provider queue included, not isolated; no local model loading. Component total is not HTTP latency. Generation-or-abstention includes any local bypass.", "provider-events.jsonl")
    usage = {k:sum(e["result"]["usage"][k] for e in complete) for k in ["input_tokens","output_tokens","total_tokens"]}
    measured("Token usage and cost", dict(provider_usage=usage,evidence_tokens=len(tiktoken.get_encoding("cl100k_base").encode_ordinary(context)),
        billed_cost=dict(status="unavailable",value=None,reason="No billing statement or authoritative charge returned.")), "provider and local evidence tokens",len(complete), "Actual SDK usage; skipped generation has no provider call; local token count is not billing.","provider-events.jsonl")
    measured("Reliability", dict(cases=len(rows),completed=sum(r["status"]=="completed" for r in rows),case_errors=sum(r["status"]!="completed" for r in rows),
        provider_calls=len([e for e in events if e["kind"]=="start"]),provider_completions=len(complete),provider_errors=len(errors),
        timeouts=sum("Timeout" in e["error_type"] for e in errors),retries=0),"counts",len(rows),"All cases and provider attempts; validation errors remain request failures.","provider-events.jsonl")
    inventory["Concurrency and throughput"]["reason"] = "Concurrency one; a short sequential component sample does not establish serving throughput."
    comparisons = [dict(case_id=c["case_id"],before_gate=previous[c["case_id"]]["case_gate_pass"],after_gate=c["case_gate_pass"],
        before_points=sum(p["delivered_score"] for p in previous[c["case_id"]]["expected_point_review"]),after_points=sum(p["delivered_score"] for p in c["expected_point_review"]),
        observation=c["comparison_observation"]) for c in review]
    result = dict(code_commit=read(ROOT/"preparation.json")["code_commit"],protocol="protocol.md",
        classification_pass_count=sum(c["classification_pass"] for c in review),case_gate_pass_count=sum(c["case_gate_pass"] for c in review),case_count=len(rows),
        acceptance="passed scoped gates" if all(c["case_gate_pass"] for c in review) else "failed",models=sorted({e["result"]["model"] for e in complete}),
        context_sha256=sha256(context.encode()).hexdigest(),evidence_audits=audits,metric_inventory=inventory,comparisons=comparisons,
        limits="One attempt per question; single Codex review; frozen evidence and final-round boundary, no full API/multi-round acceptance.")
    (ROOT/"measurement.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ["acceptance","classification_pass_count","case_gate_pass_count","models","comparisons"]},indent=2))
    print(json.dumps(dict(usage=usage,timings=inventory["Stage latency"]["value"]["component_total"],points=inventory["Answer correctness"]["value"],faithfulness=inventory["Faithfulness"]["value"]),indent=2))
