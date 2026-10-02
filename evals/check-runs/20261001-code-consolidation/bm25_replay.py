"""Freeze and replay the same lexical workload without provider calls or reindexing."""

from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

from evals.evaluate import load_inputs
from evals.metrics import mean, ranking, timing
from knowledgebase.rag.bm25 import search_bm25
from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.parsing import parse_txt
from knowledgebase.schemas import ChildChunk

DIRECTORY = Path(__file__).parent
FROZEN = DIRECTORY / "bm25-workload.json"


def write_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def freeze():
    cases, manifest, documents = load_inputs(Path("evals/nyu-test-cases.jsonl"))
    chunks = [child.model_dump(mode="json") for name, text in sorted(documents.items())
              for child in split_parent_child(text, parse_txt(text), name,
                  parent_max_tokens=1536, child_max_tokens=512,
                  encoding_name="cl100k_base").children]
    write_new(FROZEN, {
        "source": "Existing frozen NYU corpus and annotated questions; no new labels",
        "cases_sha256": sha256(Path("evals/nyu-test-cases.jsonl").read_bytes()).hexdigest(),
        "manifest": manifest, "cases": cases, "chunks": chunks,
        "settings": {"k1": 1.2, "b": 0.75, "top_k": 20, "metric_k": [5, 20]},
        "protocol": "One sequential scoring pass per arm, including tokenization and temporary indexing. No model, rerank, evidence packing or answer generation. Rank relevance means overlap with annotated source spans; labels are incomplete. Precision uses denominator K even for fewer results. Unanswerable cases are excluded from ranking quality, included in timing and reliability. Scores may differ by floating-point roundoff; compare exact child order and all scores with absolute tolerance 1e-10.",
    })
    print(f"Frozen {len(cases)} questions, {len(documents)} files, {len(chunks)} children.")


def replay(name):
    workload = json.loads(FROZEN.read_text())
    chunks = [ChildChunk.model_validate(row) for row in workload["chunks"]]
    metadata = [{**row, "file_name": row["file_id"]} for row in workload["chunks"]]
    rows = []
    for case in workload["cases"]:
        started = perf_counter()
        matches = search_bm25(case["question"], chunks, top_k=20, k1=1.2, b=0.75)
        seconds = perf_counter() - started
        candidates = [match.model_dump(mode="json") for match in matches]
        rows.append({"case_id": case["id"], "question": case["question"], "seconds": seconds,
                     "candidates": candidates,
                     "ranking": {str(k): ranking(case, candidates, metadata, k) for k in [5, 20]}})
    quality = {}
    for k in [5, 20]:
        measured = [row["ranking"][str(k)] for row in rows if row["ranking"][str(k)] is not None]
        quality[str(k)] = {key: mean([row[key] for row in measured])
                          for key in ["recall_at_k", "precision_at_k", "hit_rate_at_k", "mrr_at_k", "ndcg_at_k"]}
        quality[str(k)]["n"] = len(measured)
    result = {"arm": name, "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "implementation_sha256": sha256(Path("knowledgebase/rag/bm25.py").read_bytes()).hexdigest(),
              "workload_sha256": sha256(FROZEN.read_bytes()).hexdigest(),
              "device": platform.platform(), "python": platform.python_version(),
              "numpy": version("numpy"), "bm25s": version("bm25s"),
              "quality": quality, "stage_seconds": timing([row["seconds"] for row in rows]),
              "concurrency": 1, "successes": len(rows), "errors": 0, "retries": 0,
              "cases": rows}
    result["stage_seconds"]["artifact"] = f"bm25-{name}.json#/cases"
    write_new(DIRECTORY / f"bm25-{name}.json", result)
    print(json.dumps({key: result[key] for key in ["arm", "quality", "stage_seconds", "successes"]}, indent=2))


if __name__ == "__main__":
    freeze() if sys.argv[1] == "freeze" else replay(sys.argv[1])
