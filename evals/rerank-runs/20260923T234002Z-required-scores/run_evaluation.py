"""Score frozen hybrid candidates without changing the application or its library."""

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import DefaultHttpxClient, OpenAI

from knowledgebase.config import Settings
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.rag.reranking import build_rerank_messages, rerank
from knowledgebase.schemas import RerankCandidate


def run():
    report = Path(__file__).parent
    frozen = Path("evals/library-runs/20260923T221737Z-hybrid")
    settings = Settings()
    model = settings.rerank_model or settings.answer_model
    case_ids = ["msds-admissions-prerequisites", "msds-gpa", "msds-cpt-source-context", "api-setup"]
    answers = {r["case_id"]: r for r in map(json.loads, (frozen / "answers.jsonl").read_text().splitlines())
               if r["strategy"] == "hybrid"}
    snapshot = json.loads((frozen / "chunks.json").read_text())
    chunks = {c["chunk_id"]: c for f in snapshot for c in f["chunks"]}
    usage = []

    def record_usage(response):
        response.read()
        body = response.json()
        usage.append({"response_id": body.get("id"), "usage": body.get("usage"),
                      "status": body.get("status"), "output": body.get("output")})

    metadata = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "model": model, "candidate_limit": settings.rerank_candidate_limit,
        "top_k": settings.retrieval_top_k, "max_input_tokens": settings.rerank_max_input_tokens,
        "tokenizer": settings.chunk_tokenizer, "timeout_seconds": settings.eval_timeout_seconds,
        "max_retries": settings.eval_max_retries, "frozen_run": str(frozen),
        "input_hashes": {name: hashlib.sha256((frozen / name).read_bytes()).hexdigest()
                         for name in ("answers.jsonl", "chunks.json")},
        "note": "Standalone candidate scoring only. No fresh retrieval, parent packing, or answer generation.",
    }
    with (report / "run.json").open("x") as output:
        json.dump(metadata, output, indent=2)
    with OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                timeout=settings.eval_timeout_seconds, max_retries=settings.eval_max_retries,
                http_client=DefaultHttpxClient(event_hooks={"response": [record_usage]})) as sdk:
        client = RerankerClient(sdk, model)
        with (report / "results.jsonl").open("x") as output:
            for case_id in case_ids:
                previous = answers[case_id]
                inputs = [RerankCandidate(**hit, text=chunks[hit["chunk_id"]]["text"],
                                          heading_path=chunks[hit["chunk_id"]]["heading_path"])
                          for hit in previous["answer"]["retrieval"]["fused_matches"]]
                started = time.perf_counter()
                prior_usage = len(usage)
                row = {"case_id": case_id}
                try:
                    result = rerank(previous["question"], inputs, client, top_k=settings.retrieval_top_k,
                                    candidate_limit=settings.rerank_candidate_limit,
                                    max_input_tokens=settings.rerank_max_input_tokens,
                                    encoding_name=settings.chunk_tokenizer)
                    row.update(status="ok", result=result.model_dump(),
                               messages=build_rerank_messages(result.question, result.candidates))
                except Exception as error:
                    row.update(status="error", error_type=type(error).__name__)
                row.update(seconds=time.perf_counter() - started, provider_usage=usage[prior_usage:],
                           recorded_at=datetime.now(timezone.utc).isoformat())
                output.write(json.dumps(row) + "\n")
                output.flush()
                print(case_id, row["status"], round(row["seconds"], 2), flush=True)


if __name__ == "__main__":
    run()
