"""Recorded conditional-dependency failures and column-scope development controls."""
import json
from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from knowledgebase.rag.planning import DependentQuery
from test_period_rule_constraints import planner_with

FIXTURE = Path(__file__).resolve().parents[1] / "evals/check-runs/20260928-planner-dependency-contract/frozen-cases.json"


def recorded(identity):
    return next(row for row in json.loads(FIXTURE.read_text())["rows"] if row["case"]["id"] == identity)


def replay(row, *, annotated=False):
    output = json.dumps(row["annotated_decision"]) if annotated else row["original_output"]
    planner, sdk = planner_with(output)
    result = planner.plan(row["case"]["question"], row["case"]["question"], lambda: 30)
    return result, sdk


def test_recorded_targetless_dependencies_fail_the_transmitted_pattern_without_repair():
    row = recorded("factual-condition")
    planner, sdk = planner_with(row["original_output"])
    with pytest.raises(ValidationError) as failure:
        planner.plan(row["case"]["question"], row["case"]["question"], lambda: 30)
    errors = failure.value.errors()
    assert [e["loc"] for e in errors] == [("dependencies", 0, "query_template"), ("dependencies", 1, "query_template")]
    assert all(e["type"] == "string_pattern_mismatch" for e in errors)
    schema = sdk.responses.create.call_args.kwargs["text"]["format"]["schema"]
    field = schema["$defs"]["DependentQuery"]["properties"]["query_template"]
    before = row["original_request"]["text"]["format"]["schema"]["$defs"]["DependentQuery"]["properties"]["query_template"]
    assert "pattern" not in before
    assert field["pattern"] == r"\{target\}"
    assert all(not re.search(field["pattern"], d["query_template"]) for d in row["original_decision"]["dependencies"])
    sdk.responses.create.assert_called_once()
    assert sdk.with_options.call_args.kwargs["max_retries"] == 0


@pytest.mark.parametrize("template", ["Who employs {target}?", 'In "people.txt", where does {target} work?'])
def test_source_derived_target_contract_remains_usable(template):
    query = DependentQuery(query_id="employer", query_template=template, requirement_ids=["employer"], depends_on=["winner"])
    assert query.query_template == template
    assert re.search(DependentQuery.model_json_schema()["properties"]["query_template"]["pattern"], template)


def test_presence_pattern_does_not_replace_exactly_one_runtime_validation():
    with pytest.raises(ValidationError, match="exactly one"):
        DependentQuery(query_id="employer", query_template="Who employs {target}, and where is {target}?",
                       requirement_ids=["employer"], depends_on=["winner"])


def test_annotated_condition_keeps_three_known_fact_queries_and_explicit_explanation():
    row = recorded("factual-condition")
    result, sdk = replay(row, annotated=True)
    assert result.plan.route == "decomposed"
    assert result.plan.dependencies == []
    assert len(result.plan.queries) == 3
    assert [q.text for q in result.plan.queries] == [row["original_decision"]["queries"][0]["text"],
        *[q["query_template"] for q in row["original_decision"]["dependencies"]]]
    assert [q.requirement_ids for q in result.plan.queries] == [["R1"], ["R2"], ["R3"]]
    assert [r.model_dump() for r in result.plan.requirements] == row["original_decision"]["requirements"]
    assert "explains why" in result.plan.requirements[2].description
    assert result.plan.answer_rules == []
    assert result.plan.original_question == row["case"]["question"]
    assert "added_coverage_query" not in result.record
    assert result.record["prompt_version"] == "dependent-planner-v7"
    instructions = result.record["input"][0]["content"]
    assert "A logical condition alone does not create a retrieval dependency" in instructions
    assert "do not replace a known row or field with {target}" in instructions
    sdk.responses.create.assert_called_once()


def test_column_annotation_preserves_scope_while_raw_semantic_error_stays_visible():
    row = recorded("missing-year")
    before, _ = replay(row)
    after, sdk = replay(row, annotated=True)
    assert "ungrouped Pre-Pawn Handgun" in before.plan.requirements[1].description
    assert "ungrouped Pre-Pawn Handgun" in before.plan.queries[1].text
    assert [r.model_dump() for r in after.plan.requirements] == row["annotated_decision"]["requirements"]
    assert "ungrouped Handgun" in after.plan.requirements[0].description
    assert "ungrouped" not in after.plan.requirements[1].description
    assert "ungrouped" not in after.plan.queries[1].text
    assert len(after.plan.requirements) == len(after.plan.queries) == 2
    assert before.plan.answer_rules == after.plan.answer_rules == row["case"]["expected_answer_rules"]
    assert before.plan.original_question == after.plan.original_question
    assert all(all(term in q.text for term in ["Alabama", "background-checks.pdf", "November 2016"])
               for q in after.plan.queries)
    assert '"ungrouped Handgun" and "Pre-Pawn Handgun"' in after.record["input"][0]["content"]
    sdk.responses.create.assert_called_once()


@pytest.mark.parametrize("identity", ["original-rule", "paraphrased-rule"])
def test_latest_successful_plans_are_preserved(identity):
    row = recorded(identity)
    result, sdk = replay(row)
    assert [r.model_dump() for r in result.plan.requirements] == row["original_decision"]["requirements"]
    assert result.plan.answer_rules == row["case"]["expected_answer_rules"]
    assert result.record["output_text"] == row["original_output"]
    assert "added_coverage_query" not in result.record
    sdk.responses.create.assert_called_once()
