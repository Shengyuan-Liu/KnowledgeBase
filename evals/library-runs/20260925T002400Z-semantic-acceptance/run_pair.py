"""Run one frozen paired acceptance experiment without automatic historical regrading."""
import asyncio
import json
from pathlib import Path
import platform
import sqlite3
import sys
from time import perf_counter

from openai import AsyncOpenAI, OpenAI

from evals import judge, metrics
from evals.automatic import collect, grade, load_benchmark
from evals.evaluate import append_jsonl, digest, git_state, read_jsonl, timestamp, write_json
from knowledgebase.config import Settings

DIRECTORY = Path(__file__).parent


def load_inputs():
    plan = json.loads((DIRECTORY / "plan.json").read_text())
    cases = json.loads((DIRECTORY / "cases.json").read_text())
    _, manifest, documents = load_benchmark()
    assert digest(json.dumps(cases, sort_keys=True).encode()) == plan["cases_sha256"]
    assert digest(json.dumps(manifest, sort_keys=True).encode()) == plan["corpus_sha256"]
    assert judge.protocol_hash() == plan["judge_protocol_sha256"]
    return plan, cases, manifest, documents


def summaries(directory, metadata, cases):
    answers, reviews, calls = (read_jsonl(directory / name) for name in ("answers.jsonl", "reviews.jsonl", "calls.jsonl"))
    for split in ("all", "development-regression", "new-frozen-acceptance"):
        subset = [case for case in cases if split == "all" or case["split"] == split]
        ids = {case["id"] for case in subset}
        subset_meta = dict(metadata)
        if split != "all":
            subset_meta.pop("rag_wall_seconds", None)
        summary = metrics.summarize(subset, [a for a in answers if a["case_id"] in ids],
            [r for r in reviews if r["case_id"] in ids], subset_meta,
            [c for c in calls if c.get("case_id") in ids or c.get("stage") == "ingestion"])
        summary["limitations"][0] = ("Six newly frozen acceptance questions on the same familiar corpus; Codex-authored, not independent human labels. No tuning after outputs."
            if split == "new-frozen-acceptance" else "Development/regression cases included; not general RAG accuracy.")
        write_json(directory / f"summary-{split}.json", summary)


async def run(phase):
    plan, cases, manifest, documents = load_inputs()
    for strategy in plan["order"]:
        directory = DIRECTORY / strategy
        settings = Settings(**{**plan["base_config"], "chunking_strategy": strategy})
        options = dict(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                       timeout=settings.eval_timeout_seconds, max_retries=0)
        calls = []
        if phase == "collect":
            directory.mkdir()
            metadata = {"runner": "semantic-acceptance-v1", "status": "running", "started_at": timestamp(),
                "git": git_state(), "platform": platform.platform(), "top_k": settings.retrieval_top_k,
                "config": settings.model_dump(mode="json", exclude={"openai_api_key", "openai_base_url"}),
                "cases_sha256": plan["cases_sha256"], "corpus_sha256": plan["corpus_sha256"],
                "judge_protocol": judge.PROTOCOL, "judge_protocol_sha256": judge.protocol_hash(),
                "timing_scope": plan["timing_scope"], "concurrency": 1, "effective_max_retries": 0}
            for name, value in (("run.json", metadata), ("cases.json", cases), ("corpus.json", manifest)):
                write_json(directory / name, value)
            started = perf_counter()
            try:
                with OpenAI(**options) as sdk:
                    async with AsyncOpenAI(**options) as async_sdk:
                        await collect(settings, directory, metadata, cases, documents, sdk, async_sdk, calls)
                db = settings.data_dir / "evals" / strategy / "knowledgebase.db"
                with sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True) as connection:
                    connection.row_factory = sqlite3.Row
                    parents = [dict(row) for row in connection.execute(
                        'SELECT p.*, f.file_name FROM parent_chunks p JOIN files f USING(file_id) ORDER BY f.file_name, p."index"')]
                write_json(directory / "parents.json", parents)
                metadata["status"] = "collected"
            except Exception as error:
                metadata.update(status="failed", error_type=type(error).__name__)
                print(f"{strategy} collection failed: {type(error).__name__}", flush=True)
            finally:
                persisted = {c.get("call_id") for c in read_jsonl(directory / "calls.jsonl")}
                for call in calls:
                    if call["call_id"] not in persisted:
                        append_jsonl(directory / "calls.jsonl", call)
                metadata.update(collection_finished_at=timestamp(), collection_wall_seconds=perf_counter() - started)
                write_json(directory / "run.json", metadata)
                summaries(directory, metadata, cases)
            if metadata["status"] == "failed":
                return 1
        else:
            metadata = json.loads((directory / "run.json").read_text())
            if (directory / "reviews.jsonl").exists():
                raise ValueError("This batch was already judged; preserve it and use a new run for another attempt.")
            try:
                with OpenAI(**options) as sdk:
                    reviews = grade(sdk, settings, cases, read_jsonl(directory / "answers.jsonl"), directory)
                metadata["status"] = "completed" if len(reviews) == len(cases) and all(r["status"] == "ok" for r in reviews) else "pending_reviews"
            except Exception as error:
                metadata.update(status="judge_failed", error_type=type(error).__name__)
                print(f"{strategy} judge failed: {type(error).__name__}", flush=True)
            finally:
                metadata["finished_at"] = timestamp()
                write_json(directory / "run.json", metadata)
                summaries(directory, metadata, cases)
        print(f"{strategy}: {metadata['status']}", flush=True)
    return 0


if __name__ == "__main__":
    phase = sys.argv[1]
    if phase not in {"collect", "grade"}:
        raise SystemExit("Choose collect or grade.")
    raise SystemExit(asyncio.run(run(phase)))
