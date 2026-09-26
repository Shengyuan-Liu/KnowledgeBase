"""Paired live retrieval comparison; preserve every answer and actual evidence."""

import hashlib
import json
import statistics
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from evals.evaluate import retrieval_metrics
from knowledgebase.config import Settings
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.services.chat import answer_question
from knowledgebase.storage.operations import get_chunks, get_files, get_parents
from knowledgebase.storage.runtime import open_storage


def run():
    report = Path(__file__).parent
    settings = Settings()
    cases = json.loads((report / "cases.json").read_text())
    options = {
        strategy: settings.retrieval_options.model_copy(update={
            "strategy": "hybrid", "rerank_enabled": strategy == "rerank",
        })
        for strategy in ("hybrid", "rerank")
    }
    metadata = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "working_diff_sha256": hashlib.sha256(subprocess.check_output(["git", "diff"])).hexdigest(),
        "rerank_model": settings.rerank_model or settings.answer_model,
        "cases_sha256": hashlib.sha256((report / "cases.json").read_bytes()).hexdigest(),
        "answer_model": settings.answer_model, "embedding_model": settings.embedding_model,
        "top_k": settings.retrieval_top_k, "evidence_max_tokens": settings.evidence_max_tokens,
        "tokenizer": settings.chunk_tokenizer,
        "retrieval_options": {key: value.model_dump() for key, value in options.items()},
        "timeout_seconds": 90, "max_retries": 1, "concurrency": 3,
        "note": "Same stored library for both routes. No uploads or conversation writes. Automatic span coverage is not answer quality.",
    }
    with (report / "run.json").open("x") as output:
        json.dump(metadata, output, indent=2)
    rows = []
    with open_storage(settings.data_dir) as (sessions, store):
        with sessions() as session:
            snapshot = [{
                "file": file.model_dump(mode="json"),
                "chunks": [chunk.model_dump() for chunk in get_chunks(session, file.file_id)],
                "parents": [parent.model_dump() for parent in get_parents(session, file.file_id)],
            } for file in get_files(session)]
        with (report / "chunks.json").open("x") as output:
            json.dump(snapshot, output, indent=2)
        with OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                    timeout=90, max_retries=1) as sdk:
            embeddings = EmbeddingClient(sdk, model=settings.embedding_model)
            llm = LLMClient(sdk, model=settings.answer_model)
            reranker = RerankerClient(sdk, settings.rerank_model or settings.answer_model)

            def ask(case, strategy):
                started = time.perf_counter()
                row = {"case_id": case["id"], "question": case["question"], "strategy": strategy}
                try:
                    result = answer_question(
                        case["question"], sessions, embeddings, store, llm,
                        top_k=settings.retrieval_top_k,
                        evidence_max_tokens=settings.evidence_max_tokens,
                        encoding_name=settings.chunk_tokenizer, retrieval_options=options[strategy],
                        reranker_client=reranker if strategy == "rerank" else None,
                    ).model_dump(mode="json")
                    normalized = {**case, "evidence": [
                        {**span, "file": Path(span["file"]).name} for span in case["evidence"]
                    ]}
                    row.update(status="ok", answer=result, coverage=retrieval_metrics(normalized, result["sources"]))
                except Exception as error:
                    row.update(status="error", error_type=type(error).__name__)
                row["seconds"] = time.perf_counter() - started
                row["recorded_at"] = datetime.now(timezone.utc).isoformat()
                return row

            with (report / "answers.jsonl").open("x") as output, ThreadPoolExecutor(max_workers=3) as pool:
                jobs = [pool.submit(ask, case, strategy) for case in cases for strategy in options]
                for job in as_completed(jobs):
                    row = job.result()
                    rows.append(row)
                    output.write(json.dumps(row) + "\n")
                    output.flush()
                    print(row["strategy"], row["case_id"], row["status"], round(row["seconds"], 2), flush=True)
    summary = {}
    for strategy in options:
        completed = [r for r in rows if r["strategy"] == strategy and r["status"] == "ok"]
        summary[strategy] = {
            "completed": len(completed), "errors": len(cases) - len(completed),
            "coverage": {key: statistics.mean(r["coverage"][key] for r in completed if r["coverage"][key] is not None)
                         for key in ("annotated_char_recall", "full_evidence_recall")},
            "mean_evidence_tokens": statistics.mean(r["answer"]["retrieval"]["evidence_tokens"] for r in completed),
            "mean_seconds": statistics.mean(r["seconds"] for r in completed),
            "mean_rerank_seconds": statistics.mean(
                r["answer"]["retrieval"]["rerank_seconds"] or 0 for r in completed),
        }
    with (report / "summary.json").open("x") as output:
        json.dump({"finished_at": datetime.now(timezone.utc).isoformat(), "strategies": summary}, output, indent=2)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    run()
