"""One judge-only batch; compare protocols without grading identical answers twice."""

from pathlib import Path

from openai import OpenAI

from evals import automatic, judge, metrics
from evals.evaluate import EVALS, git_state, identifier, read_jsonl, timestamp, write_json
from knowledgebase.config import Settings


def main():
    settings = Settings(judge_reasoning_effort="high")
    cases, manifest, _ = automatic.load_benchmark()
    original = EVALS / "runs/20260924T161009Z-f2950a8f-automatic"
    directory = EVALS / "calibration-runs" / (identifier() + "-saved-answers-high")
    directory.mkdir(parents=True)
    metadata = {"runner": "judge-regrade-v1", "status": "running", "started_at": timestamp(),
        "git": git_state(), "top_k": settings.retrieval_top_k,
        "config": settings.model_dump(mode="json", exclude={"openai_api_key", "openai_base_url"}),
        "judge_protocol": judge.PROTOCOL, "judge_protocol_sha256": judge.protocol_hash(),
        "effective_max_retries": 0, "judge_concurrency": settings.judge_concurrency,
        "scope": "Only judge calls are fresh. All RAG observations/usage are copied unchanged from rag_reused_from.",
        "warmup": "none; provider caches/load uncontrolled"}
    automatic.reuse_answers(original, directory, metadata, cases, manifest)
    write_json(directory / "run.json", metadata)
    write_json(directory / "cases.json", cases)
    write_json(directory / "corpus.json", manifest)
    (directory / "judge-source.py").write_bytes(Path(judge.__file__).read_bytes())
    print(f"High-effort saved-answer regrade: {directory}", flush=True)
    answers = read_jsonl(directory / "answers.jsonl")
    with OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                timeout=settings.judge_timeout_seconds, max_retries=0) as sdk:
        reviews = automatic.grade(sdk, settings, cases, answers, directory)
    metadata.update(status="completed", finished_at=timestamp())
    write_json(directory / "run.json", metadata)
    summary = metrics.summarize(cases, answers, reviews, metadata, read_jsonl(directory / "calls.jsonl"))
    write_json(directory / "summary.json", summary)
    lines = ["# High-effort saved-answer regrade", "", metadata["scope"], "",
             "Protocol/configuration changed: score differences are judge behavior, not RAG improvements.", "",
             *metrics.console_lines(summary), ""]
    (directory / "README.md").write_text("\n".join(lines))
    print("\n".join(lines), flush=True)
    return 0 if len(reviews) == len(cases) and all(r["status"] == "ok" for r in reviews) else 1


if __name__ == "__main__":
    raise SystemExit(main())
