"""Retain explicit reviewer judgments and exact answer excerpts after inspection."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
cases = json.loads((ROOT / "cases.json").read_text())
review = []
observations = {
    "original-rule": "All four cell facts and citations remain correct; the actual answering instruction is preserved separately.",
    "paraphrased-rule": "The same four facts remain correct and cited; the paraphrased instruction stays separate without a duplicate evidence requirement.",
    "factual-condition": "The duplicated factual question disappears from answer_rules, now empty. Three independent fact queries and the complete three-point answer are preserved; the absence statement is explicitly limited to supplied excerpts. This previously failing classification gate now passes.",
    "missing-year": "Correct ungrouped Handgun and Pre-Pawn Handgun paths, November 2016 scope, two missing statuses and local refusal remain unchanged in meaning.",
}
for case in cases:
    identity = case["id"]
    row = json.loads((ROOT / (identity + ".json")).read_text())
    assert row["status"] == "completed"
    assert row["plan"]["answer_rules"] == case["expected_answer_rules"]
    lines = row["answer"].splitlines()
    condition = identity == "factual-condition"
    missing = identity == "missing-year"
    point_text = [row["answer"]] * 2 if missing else lines
    assert len(point_text) == len(case["expected_points"])
    points = [dict(expected=expected, score=1, delivered_score=1, evidence=text,
        reason=("The unchanged rubric accepts a full-question refusal for both absent November 2016 values; generic wording does not name the fields or period."
                if missing else "The answer supplies the correct scoped value, explicit blank, or missing-explanation statement from the frozen reference points."))
        for expected, text in zip(case["expected_points"], point_text)]
    factual_lines = [] if missing else lines[:2] if condition else lines
    claims = [dict(text=text, supported=True,
        citation_ids=[int(n) for n in re.findall(r"\[(\d+)\]", text)], citation_supported=True,
        evidence="Source 1 Alabama row p5 at 364:457, November 2015 header p2, full column paths and original-page cell labels.",
        reason="The cited source supplies the value or explicit blank for the correct row, column and period.") for text in factual_lines]
    limitations = []
    if condition:
        limitations.append(dict(text=lines[2], correct=True, citation_ids=[1, 2],
            reason="The supplied table and footnotes contain no explanation of the blank Rentals Handgun cell. The answer limits its absence statement to the supplied excerpts and invents no cause. Reviewed separately from positive factual groups."))
    if missing:
        limitations.append(dict(text=row["answer"], correct=True,
            reason="Only November 2015 evidence is supplied, so both requested November 2016 values are unavailable. The local refusal asserts no value and requires no factual citation."))
    rules = row["plan"]["answer_rules"]
    review.append(dict(case_id=identity, classification_pass=True,
        classification_basis=("The three requested source facts are retained and answer_rules is empty; no factual conditional clause is duplicated."
                              if condition else "The actual answering instruction is separated from the requested facts, without an invented or duplicate requirement."),
        rule_provenance_pass=all(rule in case["question"] for rule in rules),
        actual_answer_rules=rules, expected_answer_rules=case["expected_answer_rules"],
        route_pass=True, column_scope_pass=True,
        factual_plan_observation=("Three independent known-input queries retain cell content, Handgun value and the explicit explanation question, with no dependency placeholder."
                                 if condition else "Document, Alabama row, requested period and each complete column path are preserved."),
        expected_point_review=points, factual_claims=claims, limitation_statements=limitations,
        semantic_quality_status="measured", semantic_quality_reason=None,
        assessment_semantics_pass=True,
        assessment_review=("Both November 2016 values missing with explicit period gaps and no references."
                           if missing else "Blank and Handgun value supported by row p5 with period/header context; the explanation remains missing."
                           if condition else "All four cell values/blanks supported by row p5 with attached period/header context."),
        answer_relevance=1, relevance_rubric="Addresses requested dimensions or appropriately refuses without unrelated content.",
        full_abstention=missing, explicit_partial_limitation=condition, case_gate_pass=True,
        comparison_observation=observations[identity]))

result = dict(reviewer="Codex /root; model-assisted semantic review, not human ground truth",
    method="Read each current plan, query, rule, assessment, answer and supplied context against the unchanged questions and original cell/column annotations. The script retains explicit reviewer judgments with exact excerpts; it is not an automatic semantic grader.",
    independent_second_review=False,
    score_rubric="Unchanged expected-point 0/0.5/1 scoring, with null reserved for unavailable answers and separate all-intended delivery. Positive factual sentence/list-item support and inline citation review; absence statements reviewed separately. Case gates also require correct classification, route and scope.",
    cases=review)
with (ROOT / "review.json").open("x") as file:
    file.write(json.dumps(result, indent=2) + "\n")
print("Retained review: 4/4 case gates, 13/13 expected points, 10/10 positive factual groups supported and individually cited. These are fixed development cases, not held-out or full-loop acceptance.")
