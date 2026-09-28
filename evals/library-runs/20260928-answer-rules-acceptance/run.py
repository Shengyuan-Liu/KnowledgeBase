"""Observe live production components on frozen evidence without new retrieval."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter
from types import SimpleNamespace

from openai import OpenAI
from knowledgebase.config import Settings
from knowledgebase.providers.llm import LLMClient
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.rag.context import build_context
from knowledgebase.rag.generation import generate_answer
from knowledgebase.rag.planned_retrieval import PlannedEvidence
from knowledgebase.services.hops import HopController
from knowledgebase.services.planning import PreparedPlanning, RequestControl

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
SOURCE = PROJECT / "evals/library-runs/20260927-blank-plan-acceptance/grouped-and-blank-cells-planned.json"


def write(name, value):
    with (ROOT / name).open("x") as file:
        file.write(json.dumps(value, indent=2) + "\n")


class Observer:
    def __init__(self, sdk, case):
        self.sdk, self.case = sdk, case
        self.responses = SimpleNamespace(create=self.call)

    def with_options(self, **kwargs):
        return Observer(self.sdk.with_options(**kwargs), self.case)

    def log(self, value):
        with (ROOT / "provider-events.jsonl").open("a") as file:
            file.write(json.dumps(dict(case=self.case, at=datetime.now(timezone.utc).isoformat(), **value)) + "\n")

    def call(self, **kwargs):
        started = perf_counter()
        self.log(dict(kind="start", input=kwargs))
        try:
            result = self.sdk.responses.create(**kwargs)
            self.log(dict(kind="complete", seconds=perf_counter()-started, result=result.model_dump(mode="json")))
            return result
        except Exception as error:
            self.log(dict(kind="error", seconds=perf_counter()-started,
                          error_type=type(error).__name__, status_code=getattr(error, "status_code", None)))
            raise


def frozen():
    original = json.loads(SOURCE.read_text())
    evidence = PlannedEvidence.model_validate(original["answer"]["retrieval"]["planning"]["hops"]["rounds"][0])
    return original, evidence


if __name__ == "__main__":
    settings = Settings(openai_timeout_seconds=180, openai_max_retries=0)
    original, evidence = frozen()
    cases = json.loads((ROOT / "cases.json").read_text())
    hashes = {str(p.relative_to(PROJECT)): sha256(p.read_bytes()).hexdigest()
              for p in [SOURCE, ROOT / "cases.json", ROOT / "protocol.md", ROOT / "run.py",
                        *sorted((PROJECT / "knowledgebase").rglob("*.py"))]}
    if sys.argv[1:] == ["prepare"]:
        assert settings.openai_api_key.strip()
        assert subprocess.check_output(["git", "branch", "--show-current"], text=True).strip() == "v2"
        assert not subprocess.check_output(["git", "diff", "HEAD", "--", "knowledgebase"], text=True)
        fixture = json.loads((PROJECT / "evals/check-runs/20260927-answer-rules/frozen-case.json").read_text())
        assert sha256(SOURCE.read_bytes()).hexdigest() == fixture["sha256"]
        assert cases[0]["question"] == fixture["question"]
        assert len(cases) == 4
        write("preparation.json", dict(at=datetime.now(timezone.utc).isoformat(), hashes=hashes,
            code_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            device=platform.platform(), python=platform.python_version(),
            settings=settings.model_dump(mode="json", exclude={"openai_api_key", "openai_base_url"}),
            context_sha256=sha256(build_context(evidence.evidence.chunks).encode()).hexdigest(),
            credential_authorization="Previously authorized existing key; no credential writes.",
            concurrency=1, provider_retries=0, local_model_loading=False, provider_queue_included=True))
        write("frozen-evidence.json", evidence.model_dump(mode="json"))
        print("Prepared four frozen questions, committed implementation, exact evidence and safe runtime; no provider calls.")
        raise SystemExit()
    preparation = json.loads((ROOT / "preparation.json").read_text())
    assert hashes == preparation["hashes"]
    assert not (ROOT / "run-start.json").exists()
    write("run-start.json", dict(at=datetime.now(timezone.utc).isoformat(), case_count=len(cases), max_calls=12))
    with OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                timeout=180, max_retries=0) as sdk:
        for case in cases:
            started = perf_counter()
            row = dict(case=case, status="running", stage_seconds={})
            try:
                control = RequestControl(settings.planning, settings.chunk_tokenizer)
                observed = Observer(sdk, case["id"])
                planner = PlannerClient(observed, settings.planner_model or settings.answer_model,
                                        settings.planning, settings.chunk_tokenizer)
                stage = perf_counter()
                generated = planner.plan(case["question"], case["question"], control.before_answer)
                row["stage_seconds"]["planning"] = perf_counter()-stage
                row["planner_record"] = generated.record
                row["plan"] = generated.plan.model_dump(mode="json")
                prepared = PreparedPlanning(generated.plan, original["answer"]["retrieval"]["planning"]["trace"]["allowed_file_ids"], generated.record)
                controller = HopController(prepared, None, None, None, planner, control)
                controller.result = evidence.model_copy(deep=True)
                controller.result.trace.plan = generated.plan
                controller.result.trace.runs = []
                controller.round_index = settings.planning.max_rounds
                controller.progressed = True
                stage = perf_counter()
                controller.assess()
                row["stage_seconds"]["assessment"] = perf_counter()-stage
                row["assessment"] = controller.assessment
                row["trace"] = controller.trace
                llm = LLMClient(observed, settings.answer_model, reasoning_effort=settings.answer_reasoning_effort)
                stage = perf_counter()
                row["answer"] = generate_answer(case["question"], evidence.evidence.chunks,
                    llm.bounded(control.generation_limits()), assessment=controller.assessment)
                row["stage_seconds"]["generation_or_abstention"] = perf_counter()-stage
                row["status"] = "completed"
            except Exception as error:
                row.update(status="error", error_type=type(error).__name__, status_code=getattr(error, "status_code", None))
            row["component_complete_seconds"] = perf_counter()-started
            write(case["id"] + ".json", row)
            print(case["id"], row["status"], round(row["component_complete_seconds"], 2), flush=True)
    write("run-finished.json", dict(at=datetime.now(timezone.utc).isoformat()))
