"""Replay assessor input construction and contract validation without a model."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import sys
from time import perf_counter
from types import SimpleNamespace

from knowledgebase.providers.limits import input_tokens
from knowledgebase.rag.planning import AnswerRequirement
from knowledgebase.schemas import RetrievedChunk, StructuredChunk

DIRECTORY = Path(__file__).parent
PACKED_PATH = Path("evals/check-runs/20260927-pdf-evidence-packing/after-2.json")
MANIFEST = json.loads((DIRECTORY / "frozen-manifest.json").read_text())
PACKED = json.loads(PACKED_PATH.read_text())
INDEX = json.loads(Path("evals/library-runs/20260927-v2-pdf-live/index-snapshot.json").read_text())
FILES = {d["file"]["file_id"]: d for d in INDEX["files"]}
CHUNKS = {c["chunk_id"]: c for d in INDEX["files"] for c in d["chunks"]}
CHUNKS.update({p["parent_id"]: {"chunk_id": p["parent_id"], **{k: v for k, v in p.items() if k != "parent_id"}}
               for d in INDEX["files"] for p in d["parents"]})


def load_baseline():
    spec = importlib.util.spec_from_file_location("frozen_sufficiency", DIRECTORY / "baseline-sufficiency.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_result(row):
    # Nested base-model snapshots omit subclass metadata; restore the frozen typed
    # chunk so rendered headings are identical to the retained answer context.
    return SimpleNamespace(evidence=SimpleNamespace(chunks=[RetrievedChunk.model_validate({**h,
        "chunk": StructuredChunk.model_validate(CHUNKS[h["chunk"]["chunk_id"]])}) for h in row["result"]["chunks"]]))


def base_payload(row):
    payload = deepcopy(MANIFEST["historical_assessor_payloads"][row["case_id"] + "-planned"])
    payload["context"] = row["context"]
    return payload


def request(module, payload):
    return {"messages": [{"role": "developer", "content": module.ASSESSMENT_INSTRUCTIONS},
                         {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            "schema": module.SufficiencyAssessment.model_json_schema()}


def write(name, value):
    target = DIRECTORY / name
    assert not target.exists(), "Choose a new append-only output name."
    target.write_text(json.dumps(value, indent=2) + "\n")


def historic_failure():
    module = load_baseline()
    observations = json.loads((DIRECTORY / "historical-invalid-quote.json").read_text())
    start = next(o for o in observations if o["kind"] == "sdk_start")
    completion = next(o for o in observations if o["kind"] == "sdk_complete")
    payload = json.loads(start["input"]["input"][1]["content"])
    raw = next(c["text"] for message in completion["result"]["output"] for c in message.get("content", []) if c["type"] == "output_text")
    stages = [json.loads(line) for line in Path("evals/library-runs/20260927-v2-pdf-live/repair-1/server-observations.jsonl").read_text().splitlines()]
    stage = next(o for o in stages if o.get("request") == "apple-income-planned" and o["kind"] == "stage")
    excerpts = module.assessment_excerpts(source_result({"result": stage["result"]["evidence"]}))
    try:
        module.validate_assessment(module.SufficiencyAssessment.model_validate_json(raw),
            [AnswerRequirement.model_validate(r) for r in payload["requirements"]], excerpts)
    except ValueError as error:
        return {"request": start["request"], "call_id": start["call_id"],
                "response_source": "historical-invalid-quote.json", "validated": False,
                "error": str(error), "raw_response": raw,
                "scope": "Original historical context and actual model response; preserved failure, not rewritten."}
    raise AssertionError("The recorded invalid quote unexpectedly passed its original contract.")


def replay_before(name):
    for path, expected in MANIFEST["referenced_artifacts"].items():
        assert sha256(Path(path).read_bytes()).hexdigest() == expected
    module = load_baseline()
    input_tokens({}, "cl100k_base")  # Warm tokenizer before timing either version.
    rows = []
    for row in PACKED["rows"]:
        result = source_result(row)
        payload = base_payload(row)
        start = perf_counter()
        catalog = module.assessment_excerpts(result)
        payload["evidence_catalog"] = [{k: v for k, v in e.items() if k != "text"} for e in catalog]
        actual_request = request(module, payload)
        count = input_tokens(actual_request, "cl100k_base")
        seconds = perf_counter() - start
        assert count <= 8192
        rows.append({"case_id": row["case_id"], "arm": row["arm"], "question": row["question"],
                     "selected_ids": row["selected_ids"], "facts": row["facts"],
                     "answer_context_sha256": sha256(row["context"].encode()).hexdigest(),
                     "input_token_count": count, "catalog": catalog, "request": actual_request,
                     "catalog_input_seconds": seconds})
    write(name, {"phase": "before", "baseline_commit": MANIFEST["baseline_commit"],
                 "packed_input_sha256": sha256(PACKED_PATH.read_bytes()).hexdigest(),
                 "model_calls": 0, "encoding": "cl100k_base", "max_input_tokens": 8192,
                 "scope": "Frozen current answer contexts. Planned requirement/control metadata from the last historical assessment for the same case; single-arm contexts assessed hypothetically. No decisions or answer quality scored.",
                 "stage_boundary": "Catalog construction, schema/request serialization and local input-token counting; source restoration and payload copying excluded. Tokenizer prewarmed, no model/network/queue.",
                 "rows": rows, "historical_failure": historic_failure()})
    print(f"Captured {len(rows)} baseline assessor inputs; max {max(r['input_token_count'] for r in rows)} tokens. Historical invalid quote remains rejected.")


def manual_income_contract(module, catalog, *, ids_only):
    """A hand-authored contract fixture, never an observed model decision."""
    needles = ["Three Months Ended\tTwelve Months Ended", "September 28, 2024\tSeptember 30, 2023",
               "Net income\t$ 14,736\t$ 22,956\t$ 93,736\t$ 96,995", "(In millions, except number of shares"]
    references = []
    for needle in needles:
        excerpt = next(e for e in catalog if needle in e["text"])
        reference = {"evidence_id": excerpt["evidence_id"]}
        if not ids_only:
            reference["quote"] = next(line for line in excerpt["text"].splitlines(keepends=True) if needle in line)
        references.append(reference)
    requirements = [AnswerRequirement(requirement_id="answer", description=MANIFEST["historical_assessor_payloads"]["apple-income-planned"]["resolved_question"])]
    raw = {"requirements": [{"requirement_id": "answer", "status": "supported", "gap": "", "references": references}], "queries": []}
    normalized, queries = module.validate_assessment(module.SufficiencyAssessment.model_validate(raw), requirements, catalog)
    for ref in normalized[0]["references"]:
        assert ref["quote"] == FILES[ref["file_id"]]["extraction"]["text"][ref["start_offset"]:ref["end_offset"]]
    return {"authorship": "Deterministic selections hand-authored by Codex; no provider call, no correctness or live-success claim.",
            "request": "apple-income-planned", "raw_decision": raw, "validated_requirements": normalized, "validated_queries": queries}


def replay_after(name):
    from knowledgebase.rag import sufficiency as module
    from knowledgebase.rag.context import build_context

    for path, expected in MANIFEST["referenced_artifacts"].items():
        assert sha256(Path(path).read_bytes()).hexdigest() == expected
    before = json.loads((DIRECTORY / "before.json").read_text())
    input_tokens({}, "cl100k_base")
    rows = []
    for row, prior in zip(PACKED["rows"], before["rows"], strict=True):
        result = source_result(row)
        assert build_context(result.evidence.chunks) == row["context"]
        payload = base_payload(row)
        payload.pop("evidence_catalog")
        start = perf_counter()
        catalog = module.assessment_excerpts(result)
        payload["context"] = module.assessment_context(result, catalog)
        actual_request = request(module, payload)
        count = input_tokens(actual_request, "cl100k_base")
        seconds = perf_counter() - start
        assert count <= 8192, (row["case_id"], row["arm"], count)
        assert re.sub(r"\[p\d+\] ", "", payload["context"]) == row["context"]
        for passage in catalog:
            assert passage["text"] == FILES[passage["file_id"]]["extraction"]["text"][passage["start_offset"]:passage["end_offset"]]
            assert any(old["file_id"] == passage["file_id"] and old["start_offset"] <= passage["start_offset"]
                       and passage["end_offset"] <= old["end_offset"] for old in prior["catalog"])
            assert passage["page_indices"], (row["case_id"], passage)
        rows.append({"case_id": row["case_id"], "arm": row["arm"], "question": row["question"],
                     "selected_ids": row["selected_ids"], "facts": row["facts"],
                     "answer_context_sha256": sha256(row["context"].encode()).hexdigest(),
                     "input_token_count": count, "catalog": catalog, "request": actual_request,
                     "catalog_input_seconds": seconds})
    income_after = next(r for r in rows if r["case_id"] == "apple-income" and r["arm"] == "planned")
    income_before = next(r for r in before["rows"] if r["case_id"] == "apple-income" and r["arm"] == "planned")
    manual_before = manual_income_contract(load_baseline(), income_before["catalog"], ids_only=False)
    manual_after = manual_income_contract(module, income_after["catalog"], ids_only=True)
    assert [(r["start_offset"], r["end_offset"], r["quote"]) for r in manual_before["validated_requirements"][0]["references"]] == [
        (r["start_offset"], r["end_offset"], r["quote"]) for r in manual_after["validated_requirements"][0]["references"]]
    write(name, {"phase": "after", "packed_input_sha256": sha256(PACKED_PATH.read_bytes()).hexdigest(),
                 "code_hashes": {str(p): sha256(p.read_bytes()).hexdigest() for p in Path("knowledgebase").rglob("*.py")},
                 "model_calls": 0, "encoding": "cl100k_base", "max_input_tokens": 8192,
                 "scope": before["scope"], "stage_boundary": before["stage_boundary"], "rows": rows,
                 "manual_contract_before": manual_before, "manual_contract_after": manual_after})
    print(f"Captured {len(rows)} ID-only assessor inputs; max {max(r['input_token_count'] for r in rows)} tokens. All source slices, physical pages and original context unchanged; hand-authored income selections resolve exactly.")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        replay_before(sys.argv[1])
    else:
        (replay_before if sys.argv[1] == "before" else replay_after)(sys.argv[2])
