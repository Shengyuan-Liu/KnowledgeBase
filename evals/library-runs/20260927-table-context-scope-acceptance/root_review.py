"""Serialize the root reviewer's independent judgments after inspecting raw answers."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

RUN = Path(__file__).resolve().parent
assert not (RUN / "root-review.json").exists()
frozen = json.loads((RUN / "frozen-cases.json").read_text())
observations = [json.loads(line) for line in (RUN / "server-observations.jsonl").read_text().splitlines()]
rows = []
for case in frozen["cases"]:
    for arm in ["single", "planned"]:
        identity = case["id"] + "-" + arm
        path = RUN / (identity + ".json")
        raw = json.loads(path.read_text())
        answer = raw["answer"]
        supported = set(case["expected_fact_ids"])
        if case["id"] == "grouped-and-blank-cells":
            supported = {"alabama_handgun"}
            if arm == "single":
                supported.add("alabama_prepawn_handgun")
        points = [dict(fact_id=fact, reference_correctness=int(fact in supported),
                       completeness=int(fact in supported), supplied_evidence_coverage=1)
                  for fact in case["expected_fact_ids"]]
        factual_lines = [line.strip()[2:] for line in answer["answer"].splitlines()
                         if line.strip().startswith("- ") and re.search(r"\[\d+\]", line)]
        claims = []
        for index, text in enumerate(factual_lines):
            correct = case["id"] != "grouped-and-blank-cells" or index < (2 if arm == "single" else 1)
            claims.append(dict(text=text, faithfulness=int(correct), citation_support=int(correct),
                               citation_coverage=int(correct), source_ids=[int(value) for value in re.findall(r"\[(\d+)\]", text)]))
        generation = [(number, record) for number, record in enumerate(observations, 1)
                      if record["kind"] == "sdk_start" and record["request"] == identity and record["input"].get("stream")]
        assert len(generation) == 1
        line, sdk = generation[0]
        user = next(message["content"] for message in sdk["input"]["input"] if message["role"] == "user")
        table_source = next(source for source in answer["sources"] if source["chunk_id"].endswith(":child:0"))
        assert table_source["text"] in user
        assert "[6,7,16,17,434,434]" in user and "[6,7,17,18,435,435]" in user
        if case["id"] == "dense-table":
            note = "All four values match original Alabama row and exact column positions. The separately cited disclaimer states checks rather than sales and no one-to-one correspondence. Each numeric bullet and disclaimer has its own supporting citation; the uncited heading only frames the following bullets."
        elif case["id"] == "state-totals":
            note = "All three state totals match the original rows in the supplied first child: Alabama71,137, Alaska7,095, Arizona27,087. Each separate bullet cites that child. No additional arithmetic or ranking claim is generated."
        elif arm == "single":
            note = "Ungrouped Handgun23,022 and Pre-Pawn Handgun14 are correct. One bullet wrongly labels Redemption Handgun2,179 and Redemption LongGun2,307 as Rentals. Original Rentals columns16 and17 are blank with zero-width canonical positions434 and435. Those positions, full row, Rentals parent and leaf headers are actually supplied. The two wrong cell values form one unsupported factual bullet with citation[1]."
        else:
            note = "Only ungrouped Handgun23,022 is correct. Pre-Pawn Handgun is14; the answer substitutes Redemption Handgun2,179. Rentals Handgun and LongGun are printed blank, not0; both exact empty positions, grouped header and full row are supplied. The three wrong bullets cite[1] but that table does not support those associations."
        saved = raw["saved_message"]["sources"]
        common = [{key: value for key, value in source.items() if key != "file_deleted"} for source in saved]
        rows.append(dict(case_id=case["id"], arm=arm, raw_sha256=sha256(path.read_bytes()).hexdigest(),
            answer_text=answer["answer"], points=points, claim_groups=claims,
            incorrect_full_abstention=False, answer_relevance=1, review_note=note,
            actual_generation=dict(artifact="server-observations.jsonl", line=line, call_id=sdk["call_id"]),
            table_source_id=table_source["source_id"], table_span=[0, 942], page_indices=[0],
            raw_history_sources_match=raw["history_sources_match"],
            history_common_source_fields_match=common == answer["sources"]))
result = dict(reviewer="Root Codex model reviewer; not human; no paid judge",
    reviewed_at=datetime.now(timezone.utc).isoformat(),
    method="Independently read all six exact answers, supplied sources, original-page gold, row/header/cell mapping and actual generation inputs before receiving primary judgments. Scores below serialize those manual model-review judgments, not a substring scorer.",
    expected_points=24, correct_complete_points=sum(point["reference_correctness"] for row in rows for point in row["points"]),
    supplied_evidence_points=24, claims_supported=sum(claim["faithfulness"] for row in rows for claim in row["claim_groups"]),
    claim_count=sum(len(row["claim_groups"]) for row in rows), rows=rows)
assert result["correct_complete_points"] == 19
assert result["claims_supported"] == 19 and result["claim_count"] == 23
(RUN / "root-review.json").write_text(json.dumps(result, indent=2) + "\n")
print("Independent root review retained: 19/24 requested points;19/23 supported factual groups;24/24 supplied structural points;no full refusal. No provider calls.")
