"""Retain Codex's case-by-case semantic judgments after reading the actual outputs."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
cases = json.loads((ROOT / "cases.json").read_text())
review = []
observations = {
    "original-rule": "Four correct cells and their inline citations remain; actual answer rule is separate and no duplicate evidence requirement appears.",
    "paraphrased-rule": "Four correct cells and their inline citations remain under the paraphrased answering instruction.",
    "factual-condition": "Recovers from a planner validation failure to three independent known-input queries and a complete three-point answer. However, the planner now copies the factual conditional question into answer_rules; text provenance passes but semantic classification regresses.",
    "missing-year": "The transferred ungrouped qualifier disappears from Pre-Pawn Handgun in both requirement and query. Exactly two missing facts remain, with the unchanged user rule and local full-question refusal; this gate now passes.",
}
for case in cases:
    identity = case["id"]
    row = json.loads((ROOT / (identity + ".json")).read_text())
    assert row["status"] == "completed"
    lines = row["answer"].splitlines()
    condition = identity == "factual-condition"
    missing = identity == "missing-year"
    point_text = [row["answer"]] * 2 if missing else lines
    assert len(point_text) == len(case["expected_points"])
    points = [dict(expected=expected, score=1, delivered_score=1, evidence=text,
        reason=("The frozen rubric accepts refusal of the whole unanswerable question; generic wording names neither field nor year."
                if missing else "Matches the expected value, blank cell, or explicit absence of an explanation in the supplied sources."))
        for expected, text in zip(case["expected_points"], point_text)]
    factual_lines = [] if missing else lines[:2] if condition else lines
    claims = [dict(text=text, supported=True, citation_ids=[int(n) for n in re.findall(r"\[(\d+)\]", text)],
        citation_supported=True, evidence="Source 1, Alabama row p5 at 364:457, November 2015 header p2 and source-bound full column paths in the frozen cell annotations.",
        reason="The cited source supplies the requested cell value or explicit blank for the correct row, column and period.") for text in factual_lines]
    limitations = []
    if condition:
        limitations.append(dict(text=lines[2], correct=True, citation_ids=[1, 2],
            reason="The supplied table and footnotes contain no explanation of Alabama's blank Rentals Handgun cell. This absence statement is reviewed separately from positive factual claim groups; no cause is invented."))
    if missing:
        limitations.append(dict(text=row["answer"], correct=True,
            reason="Both requested November 2016 values are absent; only November 2015 evidence is supplied. The local response refuses the whole question without asserting values or citations."))
    rules = row["plan"]["answer_rules"]
    review.append(dict(case_id=identity,
        classification_pass=not condition,
        classification_basis=("The factual conditional question is incorrectly duplicated into answer_rules even though it already defines all three source facts. This is not a user instruction about how to report evidence or format the answer."
                              if condition else "Only the actual user answering instruction is copied to answer_rules; requested facts remain separate."),
        rule_provenance_pass=all(rule in case["question"] for rule in rules),
        actual_answer_rules=rules, expected_answer_rules=case["expected_answer_rules"],
        route_pass=True, column_scope_pass=True,
        factual_plan_observation=("Three independent queries retain cell contents, known Handgun value and the explicit document-explanation question. No dependencies or unknown targets are invented."
                                 if condition else "Correct document, Alabama row, period and separately scoped column names; no additional evidence-sufficiency requirement."),
        expected_point_review=points, factual_claims=claims, limitation_statements=limitations,
        semantic_quality_status="measured", semantic_quality_reason=None,
        assessment_semantics_pass=True,
        assessment_review=("Two November 2016 values correctly missing with explicit period-mismatch gaps and no references."
                           if missing else "Blank and Handgun value supported by p5 plus attached period/header context; explanation correctly missing."
                           if condition else "Four requested values/blanks supported by p5 plus attached period/header context."),
        answer_relevance=1, relevance_rubric="Directly addresses requested dimensions or appropriately refuses, without unrelated material.",
        full_abstention=missing, explicit_partial_limitation=condition,
        case_gate_pass=not condition, comparison_observation=observations[identity]))

result = dict(reviewer="Codex /root; model-assisted semantic review, not human ground truth",
    method="Read every current plan/query/rule, assessment, answer, supplied table and footnotes against the unchanged questions and frozen cell annotations. Scores below are explicit reviewer judgments; the script only retains them with exact output excerpts.",
    independent_second_review=False,
    score_rubric="Unchanged 0/0.5/1 expected-point rubric, null only for unavailable answers; all-intended delivery separate. Positive factual sentence/list-item support and citation support; absence statements reviewed separately. Correct final answers do not override a failed classification gate.",
    cases=review)
with (ROOT / "review.json").open("x") as file:
    file.write(json.dumps(result, indent=2) + "\n")
print("Retained review: 13/13 expected points delivered, 10/10 positive factual groups supported and cited; 3/4 case gates. Factual-condition answer-rule misclassification is retained as a regression.")
