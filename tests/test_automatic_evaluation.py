"""Offline regression checks for automated evaluation, not live quality scores."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from evals import automatic as run, judge, metrics


def sample():
    case = {"id": "credits", "category": "factual", "answerable": True,
            "question": "How many credits?", "expected_answer_points": ["36 credits."]}
    answer = {"case_id": "credits", "status": "ok", "answer": "36 credits. [1]\nThree required courses. [1]",
              "sources": [{"source_id": 1, "file_name": "plan.md", "text": "36 credits.\nTwo required courses and one elective."}]}
    inventory = {"units": [
        {"unit_id": "u1", "reason": "Credit requirement.",
         "claims": [{"kind": "factual", "statement": "36 credits are required."}]},
        {"unit_id": "u2", "reason": "Extra course-type assertion.",
         "claims": [{"kind": "factual", "statement": "Three courses are required."}]}]}
    assessment = {"inventory_issues": [], "claims": [
        {"claim_id": "u1.c1", "verdict": "supported", "evidence": [{"source_id": 1, "unit_ids": [1]}],
         "citations": [{"source_id": 1, "verdict": "supported", "unit_ids": [1], "reason": "Exact fact."}], "reason": "Exact fact."},
        {"claim_id": "u2.c1", "verdict": "contradicted", "evidence": [{"source_id": 1, "unit_ids": [2]}],
         "citations": [{"source_id": 1, "verdict": "contradicted", "unit_ids": [2], "reason": "Elective is not required."}], "reason": "Elective is not required."}],
        "points": [{"present": True, "correctness": 2, "answer_unit_ids": ["u1"], "reason": "Expected point present."}],
        "relevance": 2, "relevance_reason": "On topic.", "abstains": False, "abstention_unit_ids": [],
        "refusal_justified": False, "appropriate_abstention": False, "abstention_reason": "Answers question."}
    return case, answer, inventory, assessment


def test_frozen_benchmark_matches_verified_previous_questions():
    cases, manifest, documents = run.load_benchmark()
    assert len(cases) == 18 and len(manifest) == len(documents) == 17
    assert sum(c["answerable"] for c in cases) == 16
    previous = json.loads((run.EVALS / "library-runs/20260924T150609Z-source-metadata-v2/cases.json").read_text())
    assert run.normalized_cases(previous) == cases


def test_extra_false_fact_cannot_hide_behind_perfect_expected_points():
    case, answer, inventory, assessment = sample()
    _, claims = judge.validate_inventory(inventory, answer["answer"])
    value = judge.validate_assessment(assessment, case, answer, claims)
    result = metrics.quality({"status": "ok", "assessment": value}, case)
    assert result["answer_correctness"] == result["answer_completeness"] == 1
    assert result["faithfulness"] == result["citation_coverage"] == .5
    assert result["contradicted_claims"] == 1
    assert not result["strict_pass"]


@pytest.mark.parametrize("mutation", ["missing_unit", "empty_claims"])
def test_inventory_rejects_observed_claim_omissions(mutation):
    _, answer, inventory, _ = sample()
    if mutation == "missing_unit":
        inventory["units"].pop()
    elif mutation == "empty_claims":
        inventory["units"][1]["claims"] = []
    with pytest.raises(ValueError):
        judge.validate_inventory(inventory, answer["answer"])


@pytest.mark.parametrize("mutation", ["missing_claim", "audit_omission", "fake_source", "fake_quote", "fake_citation", "point_without_quote"])
def test_judge_rejects_incomplete_or_untraceable_review(mutation):
    case, answer, inventory, assessment = sample()
    _, claims = judge.validate_inventory(inventory, answer["answer"])
    if mutation == "missing_claim":
        assessment["claims"].pop()
    elif mutation == "audit_omission":
        assessment["inventory_issues"] = ["Extra course type detail"]
    elif mutation == "fake_source":
        assessment["claims"][0]["evidence"][0]["source_id"] = 99
    elif mutation == "fake_quote":
        assessment["claims"][0]["evidence"][0]["unit_ids"] = [99]
    elif mutation == "fake_citation":
        assessment["claims"][0]["citations"][0]["source_id"] = 99
    else:
        assessment["points"][0]["answer_unit_ids"] = []
    with pytest.raises(ValueError):
        judge.validate_assessment(assessment, case, answer, claims)


def test_raw_failed_judgment_preserved_and_no_retry():
    case, answer, inventory, _ = sample()
    inventory["units"].pop()
    raw = json.dumps({"units": {u["unit_id"]: {k: v for k, v in u.items() if k != "unit_id"} for u in inventory["units"]}})
    sdk = SimpleNamespace(responses=SimpleNamespace(create=Mock(return_value=SimpleNamespace(output_text=raw, model="fake", usage=None))))
    row = judge.review(sdk, "fake", case, answer)
    assert row["status"] == "error" and len(row["calls"]) == 1
    assert row["calls"][0]["raw_response"] == raw
    assert "every answer unit" in row["validation_error"]
    assert metrics.quality(row, case) is None


def test_no_credential_or_provider_message_in_judge_error():
    case, answer, _, _ = sample()
    sdk = SimpleNamespace(responses=SimpleNamespace(create=Mock(side_effect=RuntimeError("secret-value"))))
    row = judge.review(sdk, "fake", case, answer)
    assert "secret-value" not in json.dumps(row)
    assert row["status"] == "error"


def test_rank_misses_fewer_than_k_and_unanswerable():
    case = {"answerable": True, "evidence": [{"file": "a", "start_offset": 0, "end_offset": 5}]}
    chunks = [{"chunk_id": "yes", "file_name": "a", "start_offset": 0, "end_offset": 5},
              {"chunk_id": "no", "file_name": "b", "start_offset": 0, "end_offset": 5}]
    r = metrics.ranking(case, [chunks[1], chunks[0]], chunks, 5)
    assert r["recall_at_k"] == 1 and r["precision_at_k"] == .2 and r["mrr_at_k"] == .5
    assert metrics.ranking(case, [], chunks, 5)["ndcg_at_k"] == 0
    assert metrics.ranking({"answerable": False}, [], chunks, 5) is None


def test_comparison_suppresses_changed_judge_and_timing_scope():
    entries = {k: metrics.measured(.5, "fraction", 18, "test") for k in
               ("faithfulness", "annotated_char_recall", "total_seconds", "generation_seconds")}
    summary = {"metrics": entries, "cases": []}
    result = metrics.compare(summary, summary, quality_compatible=False, timing_compatible=False)
    assert set(result["deltas"]) == {"annotated_char_recall", "generation_seconds"}


def test_missing_quality_not_zero_or_pass_and_inventory_printed():
    case, answer, _, _ = sample()
    result = metrics.summarize([case], [answer], [], {"top_k": 5}, [])
    assert result["metrics"]["faithfulness"]["status"] == "unavailable"
    assert result["metrics"]["strict_pass_rate"]["value"] is None
    assert result["metrics"]["judge_reliability"]["value"]["pending"] == 1
    output = "\n".join(metrics.console_lines(result))
    assert "faithfulness | unavailable" in output and "token_usage.judge" in output


def test_latest_compatible_automatic_run_selected(tmp_path, monkeypatch):
    cases, manifest, documents = run.load_benchmark()
    monkeypatch.setattr(run, "RUNS", tmp_path)
    for name, status, corpus in [("001", "completed", manifest), ("002", "failed", manifest), ("003", "completed", [])]:
        p = tmp_path / name
        p.mkdir()
        (p / "run.json").write_text(json.dumps({"runner": "automatic-v1", "status": status}))
        (p / "cases.json").write_text(json.dumps(cases))
        (p / "corpus.json").write_text(json.dumps(corpus))
    previous, kind = run.previous_run(cases, manifest, documents, tmp_path / "current")
    assert previous.name == "001" and kind == "automatic"


def test_make_eval_calls_automated_entrypoint():
    text = (run.ROOT / "Makefile").read_text()
    assert "eval:\n\tuv run --locked python -m evals.automatic $(EVAL_ARGS)" in text


def test_strict_schemas_require_units_and_prevent_invented_citations():
    case, answer, inventory, _ = sample()
    units = judge.answer_units(answer["answer"])
    schema = judge.inventory_schema(units)
    assert schema["properties"]["units"]["required"] == ["u1", "u2"]
    _, claims = judge.validate_inventory(inventory, answer["answer"])
    units["u2"] = "Three required courses."
    schema = judge.assessment_schema(claims, units, 1, answer["sources"])
    entries = schema["properties"]["claims"]["properties"]
    assert entries["u2.c1"]["anyOf"][0]["properties"]["citations"]["properties"] == {}
    assert entries["u1.c1"]["anyOf"][0]["properties"]["citations"]["required"] == ["1"]
    assert schema["$defs"]["Source1Line"]["enum"] == [1, 2]
    assert schema["properties"]["points"]["minItems"] == 1


def test_complete_two_pass_review_preserves_claim_level_failure():
    case, answer, inventory, assessment = sample()
    wire_inventory = {"units": {u["unit_id"]: {k: v for k, v in u.items() if k != "unit_id"} for u in inventory["units"]}}
    assessment["claims"] = {c["claim_id"]: {**{k: v for k, v in c.items() if k != "claim_id"},
        "citations": {str(x["source_id"]): {k: v for k, v in x.items() if k != "source_id"} for x in c["citations"]}} for c in assessment["claims"]}
    sdk = SimpleNamespace(responses=SimpleNamespace(create=Mock(side_effect=[
        SimpleNamespace(output_text=json.dumps(wire_inventory), model="fake", usage=None),
        SimpleNamespace(output_text=json.dumps(assessment), model="fake", usage=None)])))
    row = judge.review(sdk, "fake", case, answer)
    assert row["status"] == "ok" and len(row["calls"]) == 2
    assert metrics.quality(row, case)["strict_pass"] is False


def test_chunk_boundary_changes_suppress_ranking_deltas():
    entry = metrics.measured(.5, "fraction", 18, "test")
    summary = {"metrics": {"recall_at_k": entry, "annotated_char_recall": entry}, "cases": []}
    result = metrics.compare(summary, summary, quality_compatible=True, timing_compatible=True, ranking_compatible=False)
    assert set(result["deltas"]) == {"annotated_char_recall"}


@pytest.mark.parametrize("judge_error", [False, True])
def test_one_command_orchestration_saves_report_and_exit_status(tmp_path, monkeypatch, capsys, judge_error):
    import asyncio
    from knowledgebase.config import Settings
    case, answer, _, assessment = sample()
    settings = Settings(_env_file=None, openai_api_key="test-secret", data_dir=tmp_path / "data")
    monkeypatch.setattr(run, "Settings", lambda: settings)
    monkeypatch.setattr(run, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(run, "load_benchmark", lambda: ([case], [], {}))
    monkeypatch.setattr(run, "previous_run", lambda *args: (None, None))
    monkeypatch.setattr(run, "git_state", lambda: {"commit": "test"})

    class SDK:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass

    async def collect(settings, directory, metadata, cases, documents, sdk, async_sdk, calls):
        run.append_jsonl(directory / "answers.jsonl", answer)

    def grade(sdk, settings, cases, answers, directory):
        review = {"case_id": case["id"], "seconds": .1, "status": "error" if judge_error else "ok", "assessment": assessment}
        run.append_jsonl(directory / "reviews.jsonl", review)
        return [review]

    monkeypatch.setattr(run, "OpenAI", SDK)
    monkeypatch.setattr(run, "AsyncOpenAI", SDK)
    monkeypatch.setattr(run, "collect", collect)
    monkeypatch.setattr(run, "grade", grade)
    code = asyncio.run(run.run(SimpleNamespace(label="Offline wiring test")))
    assert code == int(judge_error)
    directory = next((tmp_path / "runs").iterdir())
    assert (directory / "summary.json").exists() and (directory / "README.md").exists()
    assert "test-secret" not in (directory / "run.json").read_text()
    output = capsys.readouterr().out
    assert "Previous: none" in output and "faithfulness" in output


def test_mixed_refusal_and_fact_inventory_keeps_actual_facts():
    answer = "The plan lists a course, but no room is given."
    inventory = {"units": [{"unit_id": "u1", "reason": "Mixed assertion and missing detail.", "claims": [
        {"kind": "factual", "statement": "A course is listed."},
        {"kind": "missing_information", "statement": "The room is not specified."}]}]}
    recorded, claims = judge.validate_inventory(inventory, answer)
    assert len(recorded["units"][0]["claims"]) == 2
    assert len(claims) == 1 and claims[0]["kind"] == "factual"


def test_existing_citations_cannot_be_silently_omitted():
    case, answer, inventory, assessment = sample()
    _, claims = judge.validate_inventory(inventory, answer["answer"])
    assessment["claims"][0]["citations"] = []
    with pytest.raises(ValueError, match="Every citation ID"):
        judge.validate_assessment(assessment, case, answer, claims)


def test_provider_usage_does_not_invent_missing_fields():
    case, answer, _, _ = sample()
    result = metrics.summarize([case], [answer], [], {"top_k": 5},
        [{"stage": "ingestion", "usage": {"prompt_tokens": 7, "total_tokens": 7}}])
    usage = result["metrics"]["token_usage"]["ingestion"]["value"]
    assert usage == {"prompt_tokens": 7, "total_tokens": 7}


def test_regrading_copies_answers_and_records_original_configuration(tmp_path):
    case, answer, _, _ = sample()
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir(); new.mkdir()
    original = {"runner": "automatic-v1", "git": {"commit": "old"}, "config": {"answer_model": "old-model", "judge_model": "old-judge"},
                "timing_scope": "original scope", "top_k": 3}
    for name, value in (("run.json", original), ("cases.json", [case]), ("corpus.json", []), ("chunks.json", [])):
        (old / name).write_text(json.dumps(value))
    run.append_jsonl(old / "answers.jsonl", answer)
    run.append_jsonl(old / "calls.jsonl", {"stage": "generation"})
    run.append_jsonl(old / "calls.jsonl", {"stage": "judge"})
    metadata = {"config": {"answer_model": "unused-current-model", "judge_model": "new-judge"}}
    run.reuse_answers(old, new, metadata, [case], [])
    assert (old / "answers.jsonl").read_bytes() == (new / "answers.jsonl").read_bytes()
    assert metadata["config"] == {"answer_model": "old-model", "judge_model": "new-judge"}
    assert metadata["rag_git"] == {"commit": "old"} and metadata["top_k"] == 3
    assert run.read_jsonl(new / "calls.jsonl") == [{"stage": "generation"}]


def test_all_frozen_cases_report_even_without_optional_categories():
    cases, _, _ = run.load_benchmark()
    answers = [{"case_id": c["id"], "status": "error"} for c in cases]
    report = metrics.summarize(cases, answers, [], {"top_k": 5}, [])
    assert len(report["cases"]) == 18
    assert "uncategorized" in {c["category"] for c in report["cases"]}


def test_strict_schema_references_have_no_unsupported_sibling_keywords():
    case, answer, inventory, _ = sample()
    _, claims = judge.validate_inventory(inventory, answer["answer"])
    schema = judge.assessment_schema(claims, judge.answer_units(answer["answer"]), 1, answer["sources"])
    def visit(node):
        if isinstance(node, dict):
            if "$ref" in node:
                assert set(node) == {"$ref"}
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)
    visit(schema)


def test_partial_comparison_uses_only_matching_valid_review_pairs():
    case, answer, inventory, assessment = sample()
    _, claims = judge.validate_inventory(inventory, answer["answer"])
    q = metrics.quality({"status": "ok", "assessment": judge.validate_assessment(assessment, case, answer, claims)}, case)
    before = {"metrics": {}, "cases": [{"case_id": "both", "quality": q}, {"case_id": "only_old", "quality": q}]}
    after = {"metrics": {}, "cases": [{"case_id": "both", "quality": q}, {"case_id": "only_old", "quality": None}]}
    result = metrics.compare(before, after, quality_compatible=False, timing_compatible=True, same_judge_protocol=True)
    assert result["paired_quality"]["faithfulness"]["n"] == 1
    assert result["paired_quality"]["faithfulness"]["delta"] == 0
    assert not result["quality_compatible"]
