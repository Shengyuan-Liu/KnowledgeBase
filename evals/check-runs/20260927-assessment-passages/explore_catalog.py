"""Compare proposed passage-catalog encodings on immutable packed contexts."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from statistics import mean
from types import SimpleNamespace

from knowledgebase.providers.limits import input_tokens
from knowledgebase.schemas import RetrievedChunk

DIRECTORY = Path(__file__).parent
spec = importlib.util.spec_from_file_location("frozen_sufficiency", DIRECTORY / "baseline-sufficiency.py")
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
manifest = json.loads((DIRECTORY / "frozen-manifest.json").read_text())
packed = json.loads(Path("evals/check-runs/20260927-pdf-evidence-packing/after-2.json").read_text())
schema = deepcopy(baseline.SufficiencyAssessment.model_json_schema())
schema["$defs"]["EvidenceReference"]["properties"].pop("quote")
schema["$defs"]["EvidenceReference"]["required"].remove("quote")
rows = []
for row in packed["rows"]:
    source = SimpleNamespace(evidence=SimpleNamespace(chunks=[RetrievedChunk.model_validate(h) for h in row["result"]["chunks"]]))
    excerpts = baseline.assessment_excerpts(source)
    payload = deepcopy(manifest["historical_assessor_payloads"].get(row["case_id"] + "-planned", {
        "original_question": row["question"], "resolved_question": row["question"],
        "requirements": [{"requirement_id": "answer", "description": row["question"]}],
        "executed_queries": [row["question"]], "pending_dependencies": [],
        "remaining_rounds": 2, "remaining_queries": 5,
    }))
    payload["context"] = row["context"]
    payload["evidence_catalog"] = [{k:v for k,v in e.items() if k != "text"} for e in excerpts]
    def count(used_schema):
        return input_tokens({"messages": [{"role": "developer", "content": baseline.ASSESSMENT_INSTRUCTIONS},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}], "schema": used_schema}, "cl100k_base")
    baseline_tokens = count(baseline.SufficiencyAssessment.model_json_schema())
    passages = {}
    for e in excerpts:
        offset = e["start_offset"]
        for line in e["text"].splitlines(keepends=True):
            if line.strip():
                identity = f'{e["file_id"]}@{offset}:{offset + len(line)}'
                passages.setdefault(identity, {"evidence_id": identity, "source_number": e["source_number"],
                    "file_name": e["file_name"], "text": line})
            offset += len(line)
    payload["evidence_catalog"] = list(passages.values())
    canonical_tokens = count(schema)
    for number, entry in enumerate(payload["evidence_catalog"], 1):
        entry["evidence_id"] = f"e{number}"
    local_tokens = count(schema)
    rows.append({"case_id": row["case_id"], "arm": row["arm"], "passage_count": len(passages),
        "baseline_tokens": baseline_tokens, "canonical_id_tokens": canonical_tokens, "local_id_tokens": local_tokens})
result = {"method": "Exact PlannerClient serialized messages-plus-schema token counter; cl100k_base; baseline instructions conservatively retained for both hypothetical ID-only schemas. Catalog duplicates text already in unchanged answer context. Historical final assessor control fields are reused by case where available.",
    "input_sha256": sha256(Path("evals/check-runs/20260927-pdf-evidence-packing/after-2.json").read_bytes()).hexdigest(),
    "max_input_tokens": 8192, "rows": rows,
    "summary": {k: {"mean": mean(r[k] for r in rows), "max": max(r[k] for r in rows),
                       "exceeding_limit": sum(r[k] > 8192 for r in rows)}
                for k in ["baseline_tokens", "canonical_id_tokens", "local_id_tokens"]}}
target = DIRECTORY / "catalog-layout-exploration.json"
assert not target.exists()
target.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result["summary"], indent=2))
