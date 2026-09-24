"""Run the production RAG service, claim judge, and previous-run comparison."""

import argparse
import asyncio
import json
from pathlib import Path
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from types import SimpleNamespace

from openai import AsyncOpenAI, OpenAI

from evals import judge, metrics
from evals.evaluate import EVALS, ROOT, append_jsonl, digest, git_state, identifier, read_jsonl, retrieval_metrics, timestamp, write_json
from knowledgebase.config import Settings
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.services.chat import stream_answer_in_conversation

BENCHMARK = EVALS / "benchmark"
RUNS = EVALS / "runs"


def normalized_cases(cases):
    cases = json.loads(json.dumps(cases))
    for case in cases:
        for e in case.get("evidence", []) + case.get("context_evidence", []):
            e["file"] = Path(e["file"]).name
    return cases


def load_benchmark():
    cases = json.loads((BENCHMARK / "cases.json").read_text())
    manifest = json.loads((BENCHMARK / "corpus.json").read_text())
    documents = {}
    for doc in manifest:
        data = (EVALS / doc["path"]).read_bytes()
        if digest(data) != doc["sha256"]:
            raise ValueError("Frozen corpus hash mismatch.")
        documents[doc["file_name"]] = data.decode()
    for case in cases:
        for span in case.get("evidence", []) + case.get("context_evidence", []):
            text = documents[span["file"]]
            if not 0 <= span["start_offset"] < span["end_offset"] <= len(text):
                raise ValueError("Gold span is outside its document.")
            if "quote" in span and text[span["start_offset"]:span["end_offset"]] != span["quote"]:
                raise ValueError("Gold quote differs from frozen document.")
    return cases, manifest, documents


def previous_run(cases, manifest, documents, current):
    """Prefer the latest complete automated run; otherwise use a verified historical replay."""
    for path in sorted(RUNS.glob("*/run.json"), reverse=True):
        if path.parent == current:
            continue
        meta = json.loads(path.read_text())
        if (meta.get("runner") == "automatic-v1" and meta.get("status") == "completed"
                and json.loads((path.parent / "cases.json").read_text()) == cases
                and json.loads((path.parent / "corpus.json").read_text()) == manifest):
            return path.parent, "automatic"
    for path in sorted((EVALS / "library-runs").glob("*/answers.jsonl"), reverse=True):
        directory = path.parent
        if not all((directory / name).exists() for name in ("cases.json", "chunks.json", "run.json")):
            continue
        if normalized_cases(json.loads((directory / "cases.json").read_text())) != cases:
            continue
        rows = [r for r in read_jsonl(path) if r.get("strategy") == "candidate"]
        if {r["case_id"] for r in rows} != {c["id"] for c in cases} or any(r.get("status") != "ok" for r in rows):
            continue
        snapshot = json.loads((directory / "chunks.json").read_text())
        if {f["file"]["file_name"] for f in snapshot} != set(documents):
            continue
        if all(documents[f["file"]["file_name"]][c["start_offset"]:c["end_offset"]] == c["text"]
               for f in snapshot for c in f["chunks"] + f.get("parents", [])):
            return directory, "legacy_generation"
    return None, None


class RecordedEmbeddings:
    def __init__(self, sdk, calls):
        self.sdk, self.calls = sdk, calls
        self.stage, self.case_id = "ingestion", None

    def create(self, **kwargs):
        row = {"call_id": identifier(), "stage": self.stage, "case_id": self.case_id, "model": kwargs["model"]}
        started = perf_counter()
        try:
            response = self.sdk.embeddings.create(**kwargs)
            row.update(status="ok", resolved_model=response.model,
                       usage=response.usage.model_dump() if response.usage else None)
            return response
        except Exception as error:
            row.update(status="error", error_type=type(error).__name__)
            raise
        finally:
            row["seconds"] = perf_counter() - started
            self.calls.append(row)


class RecordedStream:
    def __init__(self, stream, row, start):
        self.stream, self.row, self.start = stream, row, start

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            event = await anext(self.stream)
        except StopAsyncIteration:
            raise
        except Exception as error:
            self.row["error_type"] = type(error).__name__
            raise
        if event.type == "response.output_text.delta":
            self.row.setdefault("deltas", []).append({"seconds": perf_counter() - self.start, "delta": event.delta})
        elif event.type == "response.completed":
            self.row.update(status="ok", resolved_model=event.response.model,
                            usage=event.response.usage.model_dump() if event.response.usage else None)
        return event

    async def close(self):
        await self.stream.close()
        self.row["seconds"] = perf_counter() - self.start


class RecordedResponses:
    def __init__(self, sdk, calls):
        self.sdk, self.calls, self.case_id = sdk, calls, None

    async def create(self, **kwargs):
        row = {"call_id": identifier(), "stage": "generation", "case_id": self.case_id, "model": kwargs["model"],
               "messages": kwargs["input"], "status": "error"}
        self.calls.append(row)
        started = perf_counter()
        try:
            stream = await self.sdk.responses.create(**kwargs)
            return RecordedStream(stream, row, started)
        except Exception as error:
            row.update(error_type=type(error).__name__, seconds=perf_counter() - started)
            raise


def chunk_units_hash(chunks):
    units = sorted((c["file_name"], c["start_offset"], c["end_offset"], c["text"]) for c in chunks)
    return digest(json.dumps(units, ensure_ascii=False).encode())


def chunk_snapshot(sessions):
    from knowledgebase.storage.operations import get_files, get_chunks
    with sessions() as session:
        return [{**c.model_dump(), "file_name": f.file_name} for f in get_files(session) for c in get_chunks(session, f.file_id)]


async def collect(settings, directory, metadata, cases, documents, sdk, async_sdk, calls):
    from knowledgebase.providers.reranker import RerankerClient
    from knowledgebase.services.files import ingest_file
    from knowledgebase.storage.runtime import open_storage

    embeddings_api = RecordedEmbeddings(sdk, calls)
    embeddings = EmbeddingClient(SimpleNamespace(embeddings=embeddings_api), settings.embedding_model)
    response_api = RecordedResponses(async_sdk, calls)
    streaming = StreamingLLMClient(SimpleNamespace(responses=response_api), settings.answer_model)
    llm = LLMClient(sdk, settings.answer_model)
    started = perf_counter()
    reranker = RerankerClient(settings.rerank_model, device=settings.rerank_device,
        batch_size=settings.rerank_batch_size, max_pair_tokens=settings.rerank_max_pair_tokens) if settings.rerank_enabled else None
    metadata["model_load_seconds"] = perf_counter() - started
    metadata["reranker"] = {"model": reranker.model, "revision": reranker.model_revision,
                             "device": reranker.device} if reranker else None
    work_dir = settings.data_dir / "evals" / directory.name
    with open_storage(work_dir) as (sessions, store):
        ingested = []
        start = perf_counter()
        for name, content in documents.items():
            t = perf_counter()
            ingest_file(name, content.encode(), sessions, embeddings, store,
                chunk_size=settings.chunk_size, overlap=settings.chunk_overlap,
                chunking_strategy=settings.chunking_strategy, chunk_max_tokens=settings.chunk_max_tokens,
                chunk_tokenizer=settings.chunk_tokenizer, parent_max_tokens=settings.parent_max_tokens)
            ingested.append({"file_name": name, "seconds": perf_counter() - t, "bytes": len(content.encode())})
            print(f"Indexed {name}", flush=True)
        metadata["ingestion"] = {"seconds": perf_counter() - start, "files": ingested,
            "index_bytes": sum(p.stat().st_size for p in work_dir.rglob("*") if p.is_file())}
        chunks = chunk_snapshot(sessions)
        metadata["ingestion"]["indexed_chunks"] = len(chunks)
        metadata["chunk_units_sha256"] = chunk_units_hash(chunks)
        write_json(directory / "chunks.json", chunks)
        write_json(directory / "run.json", metadata)
        for call in calls:
            append_jsonl(directory / "calls.jsonl", call)
        batch = perf_counter()
        for case in cases:
            embeddings_api.stage, embeddings_api.case_id = "query_embedding", case["id"]
            response_api.case_id = case["id"]
            call_start = len(calls)
            row = {"case_id": case["id"], "question": case["question"], "status": "error",
                   "events": [], "answer": "", "sources": [], "first_delta_seconds": None}
            start = perf_counter()
            try:
                stream = await stream_answer_in_conversation(case["question"], identifier(), sessions,
                    embeddings, store, llm, streaming, top_k=settings.retrieval_top_k,
                    evidence_max_tokens=settings.evidence_max_tokens, encoding_name=settings.chunk_tokenizer,
                    retrieval_options=settings.retrieval_options, reranker_client=reranker)
                async for event in stream:
                    elapsed = perf_counter() - start
                    row["events"].append({"seconds": elapsed, **event.model_dump(mode="json")})
                    if event.event == "sources":
                        row["sources"] = event.data["sources"]
                        row["retrieval_seconds"] = elapsed
                    elif event.event == "answer_delta":
                        row["answer"] += event.data["delta"]
                        if event.data["delta"] and row["first_delta_seconds"] is None:
                            row["first_delta_seconds"] = elapsed
                    elif event.event == "complete":
                        row.update(event.data)
                        row["status"] = "ok"
                    elif event.event == "error":
                        row["error_type"] = "ServiceStreamError"
            except Exception as error:
                row["error_type"] = type(error).__name__
            row["total_seconds"] = perf_counter() - start
            observed = calls[call_start:]
            for call in observed:
                append_jsonl(directory / "calls.jsonl", call)
            row["embedding_seconds"] = sum(c["seconds"] for c in observed if c["stage"] == "query_embedding")
            generated = next((c for c in observed if c["stage"] == "generation"), {})
            row["generation_seconds"] = generated.get("seconds")
            row["generation_first_delta_seconds"] = next((d["seconds"] for d in generated.get("deltas", []) if d["delta"]), None)
            if row["status"] == "ok":
                row["coverage"] = retrieval_metrics(case, row["sources"])
                row["ranking"] = metrics.ranking(case, row["retrieval"]["candidates"], chunks, settings.retrieval_top_k)
                for field in ("rerank_seconds", "packing_seconds"):
                    row[field] = row["retrieval"][field]
            else:
                errors = [c.get("error_type") for c in observed if c.get("error_type")]
                if errors:
                    row["error_type"] = errors[-1]
            append_jsonl(directory / "answers.jsonl", row)
            print(f"RAG {case['id']}: {row['status']}, {row['total_seconds']:.2f}s", flush=True)
        metadata["rag_wall_seconds"] = perf_counter() - batch
        write_json(directory / "run.json", metadata)


def grade(sdk, settings, cases, answers, directory, prefix=""):
    by_case = {c["id"]: c for c in cases}
    reviews = []
    def assess(answer):
        return judge.review(sdk.with_options(timeout=settings.judge_timeout_seconds), settings.judge_model,
                            by_case[answer["case_id"]], answer,
                            reasoning_effort=None if settings.judge_reasoning_effort == "off" else settings.judge_reasoning_effort)

    started = perf_counter()
    with ThreadPoolExecutor(max_workers=settings.judge_concurrency) as pool:
        futures = [pool.submit(assess, answer) for answer in answers if answer["status"] == "ok"]
        for future in as_completed(futures):
            row = future.result()
            append_jsonl(directory / f"{prefix}reviews.jsonl", row)
            for call in row["calls"]:
                append_jsonl(directory / f"{prefix}calls.jsonl", {"stage": "judge", "case_id": row["case_id"], **call})
            reviews.append(row)
            print(f"Judge {prefix}{row['case_id']}: {row['status']}" +
                  (f" ({row.get('validation_error', row.get('error_type'))})" if row["status"] != "ok" else ""), flush=True)
    write_json(directory / f"{prefix}judge-batch.json", {"wall_seconds": perf_counter() - started,
        "concurrency": settings.judge_concurrency, "reviews": len(reviews), "max_retries": 0})
    return reviews


def baseline(directory, kind, cases, current):
    if kind == "automatic":
        return read_jsonl(directory / "answers.jsonl"), json.loads((directory / "run.json").read_text())
    snapshots = json.loads((directory / "chunks.json").read_text())
    chunks = [{**c, "file_name": f["file"]["file_name"]} for f in snapshots for c in f["chunks"]]
    by_case = {c["id"]: c for c in cases}
    rows = []
    for original in read_jsonl(directory / "answers.jsonl"):
        if original.get("strategy") != "candidate":
            continue
        row = dict(original)
        row["generation_seconds"] = row.pop("total_seconds")
        row["generation_first_delta_seconds"] = row.pop("first_delta_seconds")
        row["packing_seconds"] = row["retrieval"].get("packing_seconds")
        row["ranking"] = metrics.ranking(by_case[row["case_id"]], row["retrieval"]["candidates"], chunks, 5)
        rows.append(row)
    write_json(current / "baseline-source-metadata.json", json.loads((directory / "run.json").read_text()))
    return rows, {"top_k": 5, "timing_scope": "legacy generation only", "chunk_units_sha256": chunk_units_hash(chunks),
                  "config": json.loads((directory / "run.json").read_text())}


def reuse_answers(source, directory, metadata, cases, manifest):
    """Regrade an observed RAG batch without repeating paid answering requests."""
    original = json.loads((source / "run.json").read_text())
    if original.get("runner") != "automatic-v1":
        raise ValueError("Answer reuse requires an automatic run.")
    if json.loads((source / "cases.json").read_text()) != cases or json.loads((source / "corpus.json").read_text()) != manifest:
        raise ValueError("Answer reuse requires identical frozen cases and corpus.")
    answers = read_jsonl(source / "answers.jsonl")
    if len(answers) != len(cases) or {a["case_id"] for a in answers} != {c["id"] for c in cases} or any(a["status"] != "ok" for a in answers):
        raise ValueError("Answer reuse requires a complete successful RAG batch.")
    for key in ("answers.jsonl", "chunks.json"):
        (directory / key).write_bytes((source / key).read_bytes())
    for call in read_jsonl(source / "calls.jsonl"):
        if call.get("stage") != "judge":
            append_jsonl(directory / "calls.jsonl", call)
    for key in ("model_load_seconds", "reranker", "ingestion", "chunk_units_sha256", "rag_wall_seconds", "top_k"):
        if key in original:
            metadata[key] = original[key]
    metadata.update(rag_reused_from=str(source.resolve()), rag_git=original["git"],
                    rag_config=original["config"], timing_scope=original["timing_scope"])
    # Report the measured RAG configuration rather than current settings not exercised.
    judge_keys = {k: v for k, v in metadata["config"].items() if k.startswith("judge_")}
    metadata["config"] = {**original["config"], **judge_keys}
    print(f"Reusing recorded RAG observations: {source}; only judgments are fresh.", flush=True)


async def run(args):
    settings = Settings()
    cases, manifest, documents = load_benchmark()
    directory = RUNS / (identifier() + "-automatic")
    directory.mkdir(parents=True)
    previous, previous_kind = previous_run(cases, manifest, documents, directory)
    metadata = {"runner": "automatic-v1", "status": "running", "started_at": timestamp(), "label": args.label,
        "git": git_state(), "platform": platform.platform(), "top_k": settings.retrieval_top_k,
        "config": settings.model_dump(mode="json", exclude={"openai_api_key", "openai_base_url"}),
        "effective_max_retries": 0, "concurrency": 1, "warmup": "none; provider/OS/model cache uncontrolled",
        "timing_scope": "in-process production stream service, start to iterator completion, excluding HTTP and judge",
        "judge_concurrency": settings.judge_concurrency, "judge_protocol": judge.PROTOCOL, "judge_protocol_sha256": judge.protocol_hash(),
        "cases_sha256": digest(json.dumps(cases, sort_keys=True).encode()),
        "corpus_sha256": digest(json.dumps(manifest, sort_keys=True).encode()),
        "previous_run": str(previous.relative_to(ROOT)) if previous else None, "previous_kind": previous_kind}
    for name, data in (("run.json", metadata), ("cases.json", cases), ("corpus.json", manifest)):
        write_json(directory / name, data)
    print(f"Evaluation: {directory}\nPrevious: {metadata['previous_run'] or 'none'}", flush=True)
    print(f"Answer model: {settings.answer_model}; judge: {settings.judge_model} "
          f"({settings.judge_reasoning_effort}); RAG concurrency: 1; judge concurrency: {settings.judge_concurrency}", flush=True)
    options = {"api_key": settings.openai_api_key, "base_url": settings.openai_base_url,
               "timeout": settings.eval_timeout_seconds, "max_retries": 0}
    all_calls = []
    comparison = None
    try:
        with OpenAI(**options) as sdk:
            if getattr(args, "answers_from", None):
                reuse_answers(args.answers_from, directory, metadata, cases, manifest)
            else:
                async with AsyncOpenAI(**options) as async_sdk:
                    await collect(settings, directory, metadata, cases, documents, sdk, async_sdk, all_calls)
            answers = read_jsonl(directory / "answers.jsonl")
            reviews = grade(sdk, settings, cases, answers, directory)
            if previous:
                old_answers, old_meta = baseline(previous, previous_kind, cases, directory)
                write_json(directory / "baseline-answers.json", old_answers)
                prior_reviews = read_jsonl(previous / "reviews.jsonl") if previous_kind == "automatic" else []
                old_by_case = {a["case_id"]: a for a in old_answers}
                resolved_now = {c["resolved_model"] for r in reviews for c in r["calls"] if c.get("resolved_model")}
                resolved_before = {c["resolved_model"] for r in prior_reviews for c in r["calls"] if c.get("resolved_model")}
                compatible = (bool(resolved_now) and resolved_now == resolved_before and len(prior_reviews) == len(old_answers) and all(
                    r.get("reasoning_effort") == (None if settings.judge_reasoning_effort == "off" else settings.judge_reasoning_effort)
                    and r.get("status") == "ok" and r.get("protocol_sha256") == judge.protocol_hash() and r.get("model") == settings.judge_model
                    and r.get("answer_sha256") == digest(json.dumps(old_by_case[r["case_id"]], sort_keys=True).encode())
                    for r in prior_reviews))
                if compatible:
                    old_reviews = prior_reviews
                    write_json(directory / "baseline-reviews-reused.json", old_reviews)
                else:
                    print("Rejudging saved previous answers under the current protocol; previous artifacts remain unchanged.", flush=True)
                    old_reviews = grade(sdk, settings, cases, old_answers, directory, "baseline-")
                old_calls = read_jsonl(previous / "calls.jsonl") if previous_kind == "automatic" else [
                    {"stage": "generation", "usage": a.get("usage")} for a in old_answers]
                if not compatible:
                    old_calls = [c for c in old_calls if c.get("stage") != "judge"] + read_jsonl(directory / "baseline-calls.jsonl")
                old_summary = metrics.summarize(cases, old_answers, old_reviews, old_meta, old_calls)
                write_json(directory / "baseline-summary.json", old_summary)
                current_summary = metrics.summarize(cases, answers, reviews, metadata, read_jsonl(directory / "calls.jsonl"))
                all_valid = all(r["status"] == "ok" for r in reviews + old_reviews) and len(reviews) == len(old_reviews) == len(cases)
                comparison = metrics.compare(old_summary, current_summary, quality_compatible=all_valid,
                                             timing_compatible=previous_kind == "automatic",
                    same_judge_protocol=True, ranking_compatible=old_meta.get("chunk_units_sha256") == metadata.get("chunk_units_sha256") and old_meta["top_k"] == metadata["top_k"])
                comparison.update(previous_run=metadata["previous_run"], previous_kind=previous_kind,
                    limitations=["Historical replays freeze retrieval; no full-pipeline latency comparison. Stored corpus slices match, but historical full-document hashes are unavailable."] if previous_kind != "automatic" else [],
                    config_before=old_meta.get("config", {}), config_after=metadata["config"])
                write_json(directory / "comparison.json", comparison)
            metadata["status"] = "completed"
    except BaseException as error:
        metadata.update(status="failed", error_type=type(error).__name__)
        if not isinstance(error, Exception):
            raise
        print(f"Evaluation failed: {type(error).__name__}; completed records were retained.", flush=True)
    finally:
        persisted = {c.get("call_id") for c in read_jsonl(directory / "calls.jsonl")}
        for call in all_calls:
            if call["call_id"] not in persisted:
                append_jsonl(directory / "calls.jsonl", call)
        metadata["finished_at"] = timestamp()
        write_json(directory / "run.json", metadata)
        answers, reviews = read_jsonl(directory / "answers.jsonl"), read_jsonl(directory / "reviews.jsonl")
        summary = metrics.summarize(cases, answers, reviews, metadata, read_jsonl(directory / "calls.jsonl"))
        write_json(directory / "summary.json", summary)
        lines = ["# Automated RAG evaluation", "", f"Run: `{directory.name}`", "", f"RAG observation origin: {metadata.get('rag_reused_from', 'fresh production execution')}", "", *summary["limitations"], "",
                 *metrics.console_lines(summary), "", "## Previous evaluation", "",
                 f"Previous: `{metadata['previous_run'] or 'none found'}`"]
        pending = [r for r in reviews if r["status"] != "ok"]
        if pending:
            lines += ["", "## Pending judge reviews", "", "Case | Reason", "--- | ---"]
            lines += [f"{r['case_id']} | {r.get('validation_error', r.get('error_type', 'No valid review'))}" for r in pending]
        if comparison:
            lines += ["", "Metric | Previous | Current | Delta", "--- | --- | --- | ---"]
            for name, value in comparison["deltas"].items():
                lines.append(f"{name} | {value['before']} | {value['after']} | {value['delta']}")
            if comparison["paired_quality"]:
                lines += ["", "### Paired valid-review subset", "", comparison["paired_quality_scope"], "",
                          "Metric | Previous | Current | Delta | Pairs", "--- | --- | --- | --- | ---"]
                for name, value in comparison["paired_quality"].items():
                    lines.append(f"{name} | {value['before']:.4f} | {value['after']:.4f} | {value['delta']:+.4f} | {value['n']}")
            lines += ["", comparison["note"], f"Quality comparable: {comparison['quality_compatible']}; full-pipeline timing comparable: {comparison['end_to_end_timing_compatible']}."]
            lines += ["", "### Per-question quality", "", "Case | Previous correctness | Current correctness | Previous faithfulness | Current faithfulness", "--- | --- | --- | --- | ---"]
            for pair in comparison["cases"]:
                values = []
                for metric in ("answer_correctness", "faithfulness"):
                    for side in ("before", "after"):
                        q = (pair[side] or {}).get("quality")
                        value = q[metric] if q else None
                        values.append(f"{value:.4f}" if value is not None else "unavailable")
                lines.append(f"{pair['case_id']} | " + " | ".join(values))
        lines += ["", "Definitions: [metrics guide](../../metrics.md).", ""]
        (directory / "README.md").write_text("\n".join(lines))
        print("\n" + "\n".join(lines), flush=True)
        print(f"\nFull records: {directory}", flush=True)
    # Operational failure is distinct from low quality; failed reviews never look like successful evaluation.
    return 0 if metadata["status"] == "completed" and len(answers) == len(cases) and all(a["status"] == "ok" for a in answers) and len(reviews) == len(cases) and all(r["status"] == "ok" for r in reviews) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers-from", type=Path, help="Regrade a complete saved automatic RAG batch without rerunning answers (judge API calls only)")
    parser.add_argument("--label", default="Default frozen RAG regression evaluation")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
