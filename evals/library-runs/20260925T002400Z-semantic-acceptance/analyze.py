"""Compare frozen source units and preserve per-question improvements/regressions."""
import json
import math
from pathlib import Path
from statistics import mean

from evals import metrics
from evals.evaluate import read_jsonl, retrieval_metrics, write_json

DIRECTORY = Path(__file__).parent


def overlap(a, b):
    return a["start_offset"] < b["end_offset"] and a["end_offset"] > b["start_offset"]


def fixed_block_ranking(case, hits, blocks, k=5):
    """Project ranked source intervals onto unique immutable parser-block units."""
    if not case["answerable"]:
        return None
    gold = {b["unit_id"] for b in blocks if any(b["file_name"] == e["file"] and overlap(b, e) for e in case["evidence"])}
    ordered, seen = [], set()
    for hit in hits:
        for block in blocks:
            identity = block["unit_id"]
            if identity not in seen and block["file_name"] == hit["file_name"] and overlap(block, hit):
                ordered.append(identity)
                seen.add(identity)
    relevance = [int(identity in gold) for identity in ordered[:k]]
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, len(gold))))
    return {"k": k, "gold_units": sorted(gold), "ranked_units": ordered, "relevance": relevance,
        "recall_at_k": sum(relevance) / len(gold), "precision_at_k": sum(relevance) / k,
        "hit_rate_at_k": int(any(relevance)), "mrr_at_k": next((1 / (i + 1) for i, r in enumerate(relevance) if r), 0),
        "ndcg_at_k": sum(r / math.log2(i + 2) for i, r in enumerate(relevance)) / ideal}


def ranking_trace(case, answer, chunks, blocks):
    if answer["status"] != "ok":
        return {"case_id": case["id"], "status": answer["status"]}
    trace = answer["retrieval"]
    mapping = {c["chunk_id"]: c for c in chunks}
    stages = {"vector_candidates": trace["vector_matches"], "bm25_candidates": trace["bm25_matches"],
        "fused_candidates": trace["fused_matches"],
        "reranked_top5": (trace["rerank"]["matches"][:5] if trace["rerank"] else trace["fused_matches"][:5]),
        "selected_children": trace["candidates"]}
    result = {"case_id": case["id"], "split": case["split"], "status": "ok", "stages": {}}
    for name, ranked in stages.items():
        hits = [mapping[hit["chunk_id"]] for hit in ranked]
        result["stages"][name] = {"input_child_count": len(hits), "source_span_coverage": retrieval_metrics(case, hits),
            "fixed_block_ranking": fixed_block_ranking(case, hits, blocks)}
    result["stages"]["supplied_evidence"] = {"source_span_coverage": retrieval_metrics(case, answer["sources"]),
        "fixed_block_ranking": fixed_block_ranking(case, answer["sources"], blocks)}
    return result


def main():
    if (DIRECTORY / "comparison.json").exists():
        raise SystemExit("Comparison already exists; preserve completed results.")
    cases = json.loads((DIRECTORY / "cases.json").read_text())
    blocks = json.loads((DIRECTORY / "blocks.json").read_text())
    by_case = {c["id"]: c for c in cases}
    parent_signatures = []
    aggregate = {}
    for strategy in ("parent_child", "semantic"):
        directory = DIRECTORY / strategy
        parents = json.loads((directory / "parents.json").read_text())
        parent_signatures.append(sorted((p["file_name"], p["start_offset"], p["end_offset"], p["text"], p["token_count"]) for p in parents))
        chunks = json.loads((directory / "chunks.json").read_text())
        answers = read_jsonl(directory / "answers.jsonl")
        traces = [ranking_trace(by_case[a["case_id"]], a, chunks, blocks) for a in answers]
        write_json(directory / "stage-coverage.json", traces)
        aggregate[strategy] = {}
        for split in ("all", "development-regression", "new-frozen-acceptance"):
            rows = [r for r in traces if r["status"] == "ok" and (split == "all" or r["split"] == split)]
            stages = {}
            for stage in rows[0]["stages"]:
                entries = [r["stages"][stage] for r in rows]
                rank = [e["fixed_block_ranking"] for e in entries if e["fixed_block_ranking"] is not None]
                stage_metrics = {key: metrics.measured(mean([r[key] for r in rank]), "fraction", len(rank),
                    "Macro-average answerable cases; K=5 deduplicated immutable parser blocks in induced child rank order; binary gold-overlap proxy; precision denominator 5 even when fewer hits.", "stage-coverage.json")
                    for key in ("recall_at_k", "precision_at_k", "hit_rate_at_k", "mrr_at_k", "ndcg_at_k")}
                for key in ("annotated_char_recall", "full_evidence_recall"):
                    values = [e["source_span_coverage"][key] for e in entries if e["source_span_coverage"][key] is not None]
                    stage_metrics[key] = metrics.measured(mean(values), "fraction", len(values),
                        "Fixed source-span union coverage; gold-span average per question, then macro-average. Candidate stages use the full recorded window; rerank/selected use five children.", "stage-coverage.json")
                stages[stage] = stage_metrics
            aggregate[strategy][split] = stages
        write_json(directory / "stage-summary.json", aggregate[strategy])
    assert parent_signatures[0] == parent_signatures[1], "Parent intervention changed unexpectedly"
    comparison = {"parents_identical": True, "parent_count": len(parent_signatures[0]), "splits": {}}
    for split in ("all", "development-regression", "new-frozen-acceptance"):
        summaries = [json.loads((DIRECTORY / strategy / f"summary-{split}.json").read_text()) for strategy in ("parent_child", "semantic")]
        valid = all(s["metrics"]["judge_reliability"]["value"]["pending"] == 0 for s in summaries)
        comparison["splits"][split] = metrics.compare(*summaries, quality_compatible=valid,
            timing_compatible=True, ranking_compatible=False, same_judge_protocol=True)
    comparison["limitations"] = ["Raw child-ranking deltas are withheld because child boundaries differ.",
        "Fixed-block ranking is a gold-overlap proxy with incomplete semantic labels; span coverage is primary.",
        "Single-pass sequential batches; host/provider/cache differences are uncontrolled.",
        "Six newly frozen questions on familiar documents do not establish general accuracy; Codex review is not human labeling."]
    write_json(DIRECTORY / "comparison.json", comparison)
    write_json(DIRECTORY / "fixed-block-comparison.json", aggregate)
    print(f"Matched {len(parent_signatures[0])} parents; retained all paired case scores and stage traces.")


if __name__ == "__main__":
    main()
