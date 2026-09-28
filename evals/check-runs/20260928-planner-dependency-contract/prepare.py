"""Freeze prior requests and outputs, with explicitly authored plan expectations."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
SOURCE = PROJECT / "evals/library-runs/20260928-planner-fact-scope-acceptance"
events = [json.loads(line) for line in (SOURCE / "provider-events.jsonl").read_text().splitlines()]
cases = json.loads((SOURCE / "cases.json").read_text())
rows = []
for case in cases:
    identity = case["id"]
    request = next(e["input"] for e in events if e["case"] == identity and e["kind"] == "start")
    response = next(e["result"] for e in events if e["case"] == identity and e["kind"] == "complete")
    output = "".join(c["text"] for item in response["output"] for c in item.get("content", []) if c["type"] == "output_text")
    original = json.loads(output)
    expected = deepcopy(original)
    if identity == "factual-condition":
        expected["route"] = "decomposed"
        expected["queries"] += [dict(query_id=d["query_id"], text=d["query_template"],
                                    requirement_ids=d["requirement_ids"]) for d in expected["dependencies"]]
        expected["dependencies"] = []
    if identity == "missing-year":
        expected["requirements"][1]["description"] = expected["requirements"][1]["description"].replace(
            "ungrouped Pre-Pawn Handgun", "Pre-Pawn Handgun")
        expected["queries"][1]["text"] = expected["queries"][1]["text"].replace(
            "ungrouped Pre-Pawn Handgun", "Pre-Pawn Handgun")
    rows.append(dict(case=case, original_request=request, original_output=output,
                     original_decision=original, annotated_decision=expected))

sources = [SOURCE / name for name in ["cases.json", "provider-events.jsonl", "frozen-evidence.json",
                                     "failure-replay-correction.json"]]
fixture = dict(source_hashes={str(p.relative_to(PROJECT)): sha256(p.read_bytes()).hexdigest() for p in sources},
    annotation_author="Codex /root; development expectations, not model outputs or human ground truth.",
    annotation_method="For the logical condition, move the two fully specified queries to initial queries without changing any requirement or query text. For missing-year, remove only the wrongly transferred qualifier from R2/Q2. Other cases are unchanged. No production output repair is added.",
    corpus_scope="Same frozen one-page November 2015 table; no retrieval, assessment or generation executed by this planner-only replay.",
    rows=rows)
with (HERE / "frozen-cases.json").open("x") as file:
    file.write(json.dumps(fixture, indent=2) + "\n")
print("Preserved four prior requests/outputs and source hashes, with two explicit development annotations. Paid calls: 0.")
