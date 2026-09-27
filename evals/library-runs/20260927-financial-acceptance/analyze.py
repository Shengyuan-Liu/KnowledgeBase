"""Compare frozen anchor diagnostics without invoking any provider."""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parent
BASE = ROOT.parent / "20260927-v2-pdf-live"
FROZEN = json.loads((ROOT / "frozen-cases.json").read_text())
spec = importlib.util.spec_from_file_location("historical_anchor_definitions", BASE / "analyze.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
distribution = prior.distribution


def write(name, value):
    path = ROOT / name
    assert not path.exists(), f"Append-only: {path}"
    path.write_text(json.dumps(value, indent=2) + "\n")


def records(folder):
    return [json.loads(line) for line in (folder / "server-observations.jsonl").read_text().splitlines()]


def final_result(observations, identity):
    stages = [r for r in observations if r["request"] == identity and r["kind"] == "stage" and "result" in r]
    return stages[-1]["result"] if stages else None


def query_runs(result):
    if result is None:
        return []
    if "trace" in result:
        return [dict(index=i, round_index=r["round_index"], query=r["text"],
                     diagnostics=r["result"]["diagnostics"])
                for i, r in enumerate(result["trace"]["runs"])]
    return [dict(index=0, round_index=1, query=None, diagnostics=result["diagnostics"])]


def evidence_diagnostics(result):
    if result is None:
        return None
    return result["evidence"]["diagnostics"] if "trace" in result else result["diagnostics"]


def selected_ids(result):
    if result is None:
        return []
    if "trace" in result:
        return result["trace"]["selected_ids"]
    return [c["chunk_id"] for c in result["diagnostics"]["candidates"]]


def supplied_anchor_coverage(sources, facts):
    spans = []
    for source in sources:
        spans.append(dict(file_id=source["file_id"], start=source["start_offset"], end=source["end_offset"]))
        for supplement in (source.get("pdf") or {}).get("supplements", []):
            spans.append(dict(file_id=source["file_id"], start=supplement["start_offset"], end=supplement["end_offset"]))
    points = []
    for fact in facts:
        anchors = [dict(anchor=a["anchor"], covered=any(
            span["file_id"] == location["file_id"] and span["start"] <= location["start"]
            and span["end"] >= location["end"] for location in a["spans"] for span in spans))
            for a in prior.LABELS[fact]["anchors"]]
        points.append(dict(fact_id=fact, fully_covered=all(a["covered"] for a in anchors), anchors=anchors))
    return dict(value=sum(p["fully_covered"] for p in points) / len(points), facts=points,
                supplied_spans=spans, source_count=len(sources))


def diagnostics():
    rows = []
    for pass_name, folder in [("baseline", BASE / "repair-1"), ("current", ROOT)]:
        observations = records(folder)
        for case in FROZEN["cases"]:
            for arm in ["single", "planned"]:
                identity = case["id"] + "-" + arm
                answer = json.loads((folder / (identity + ".json")).read_text())
                result = final_result(observations, identity)
                per_query = []
                for run in query_runs(result):
                    diag = run["diagnostics"]
                    for stage in ["vector_matches", "bm25_matches", "fused_matches", "reranked"]:
                        matches = (diag.get("rerank") or {}).get("matches") if stage == "reranked" else diag.get(stage)
                        if matches is not None:
                            ids = [match["chunk_id"] for match in matches]
                            per_query.append(dict(query_index=run["index"], round_index=run["round_index"],
                                                  query=run["query"], stage=stage, candidate_count=len(ids),
                                                  all_candidate_ids=ids,
                                                  scores=prior.retrieval_scores(ids, case["expected_fact_ids"])))
                ids = selected_ids(result)
                diag = evidence_diagnostics(result)
                rows.append(dict(pass_name=pass_name, case_id=case["id"], arm=arm, status=answer["status"],
                                 artifact=str((folder / (identity + ".json")).relative_to(ROOT.parent)),
                                 selected_ids=ids, scores=prior.retrieval_scores(ids, case["expected_fact_ids"]),
                                 per_query=per_query,
                                 final_literal_anchor_coverage=supplied_anchor_coverage(
                                     answer.get("answer", {}).get("sources", []), case["expected_fact_ids"]),
                                 evidence_tokens=diag.get("evidence_tokens") if diag else None,
                                 context_budget=diag.get("max_tokens") if diag else None,
                                 budget_exclusions=diag.get("excluded") if diag else [],
                                 unexpanded_parents=diag.get("unexpanded_parents") if diag else [],
                                 final_sources_available=answer["status"] == "completed"))
    current = {(r["case_id"], r["arm"]): r for r in rows if r["pass_name"] == "current"}
    comparison = []
    for before in [r for r in rows if r["pass_name"] == "baseline"]:
        after = current[(before["case_id"], before["arm"])]
        comparison.append(dict(case_id=before["case_id"], arm=before["arm"],
                               selected_ids_equal=before["selected_ids"] == after["selected_ids"],
                               before_selected_ids=before["selected_ids"], after_selected_ids=after["selected_ids"],
                               before_query_count=len({r["query_index"] for r in before["per_query"]}),
                               after_query_count=len({r["query_index"] for r in after["per_query"]}),
                               before_literal_coverage=before["final_literal_anchor_coverage"]["value"],
                               after_literal_coverage=after["final_literal_anchor_coverage"]["value"]))
    return dict(K=5, label_artifact="../20260927-v2-pdf-live/anchor-labels.json",
                method="Unchanged historical definitions: Recall requires every labeled original-page anchor per fact; binary child relevance requires any anchor overlap. Precision denominator is K even when fewer results. MRR cutoff K. NDCG uses binary gain, logarithmic discount, original frozen child corpus IDCG. Non-exhaustive anchor labels, not semantic truth. Final coverage uses exact source and supplement offsets; failed responses have no supplied final sources. Equivalent evidence on other pages can be semantically correct while missing these literal anchors.",
                fixture_sha256=sha256((ROOT / "frozen-cases.json").read_bytes()).hexdigest(),
                source_index_sha256=sha256((BASE / "index-snapshot.json").read_bytes()).hexdigest(),
                rows=rows, comparison=comparison)


if __name__ == "__main__":
    result = diagnostics()
    write("retrieval-diagnostics.json", result)
    print(f"Retained {len(result['rows'])} baseline/current retrieval rows and six ranking comparisons.")
