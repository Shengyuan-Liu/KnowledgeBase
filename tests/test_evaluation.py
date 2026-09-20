"""Offline evaluation accounting, evidence coverage, and audit-trail tests."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from evals import evaluate as ev


def case(case_id="one", answerable=True):
    return {"id": case_id, "question": "What is required?", "category": "factual" if answerable else "unanswerable",
            "answerable": answerable, "expected_answer_points": ["A requirement."],
            "evidence": [{"file": "notes.txt", "start_offset": 10, "end_offset": 20}] if answerable else []}


def rating(answerable=True, score=2):
    return {"point_scores": [score], "groundedness": 2, "citation_support": 2 if answerable else None,
            "abstention": None if answerable else 2, "notes": "Verified the requirement in source [1].", "issues": []}


def answer():
    return {"answer": "A requirement. [1]", "sources": [
        {"source_id": 1, "file_name": "notes.txt", "text": "A requirement.", "start_offset": 10, "end_offset": 20}
    ]}


def make_run(path, cases=None, status="completed"):
    path.mkdir()
    cases = cases or [case()]
    ev.write_json(path / "run.json", {"run_id": path.name, "label": "Test fixture, not a quality result",
                  "status": status, "git": {"commit": "test"}, "rubric": ev.RUBRIC,
                  "cases_sha256": "cases", "corpus_sha256": "corpus", "config": {"top_k": 5}})
    ev.write_json(path / "cases.json", cases)
    ev.collect_answers(path, cases, lambda question: answer())
    return path


def human_grade(path, score=2):
    cases = json.loads((path / "cases.json").read_text())
    scores = path / "input.json"
    ev.write_json(scores, [{"case_id": c["id"], "rating": rating(c["answerable"], score)} for c in cases])
    return ev.grade(path, "test-reviewer", scores=scores)


def test_frozen_dataset_and_all_reference_spans_are_valid():
    cases, manifest, documents = ev.load_inputs(ev.EVALS / "nyu-test-cases.jsonl")
    assert len(cases) == 25
    assert sum(not c["answerable"] for c in cases) == 5
    assert len(documents) == manifest["document_count"] == 16
    assert all(name.endswith(".txt") for name in documents)


def test_coverage_unions_overlapping_chunks_and_excludes_wrong_files():
    sources = [{"file_name": "notes.txt", "start_offset": 9, "end_offset": 16},
               {"file_name": "notes.txt", "start_offset": 14, "end_offset": 18},
               {"file_name": "other.txt", "start_offset": 0, "end_offset": 100}]
    assert ev.retrieval_metrics(case(), sources) == {"annotated_char_recall": .8, "full_evidence_recall": 0}
    sources.append({"file_name": "notes.txt", "start_offset": 18, "end_offset": 21})
    assert ev.retrieval_metrics(case(), sources)["full_evidence_recall"] == 1
    assert ev.retrieval_metrics(case(answerable=False), sources) == {"annotated_char_recall": None, "full_evidence_recall": None}
    assert ev.retrieval_metrics(case(), [sources[2]])["annotated_char_recall"] == 0


def test_pending_scores_are_not_zero_and_failed_calls_are_retained(tmp_path):
    path = make_run(tmp_path / "run")
    ev.collect_answers(path, [case("error")], Mock(side_effect=RuntimeError("secret provider text")))
    cases = [case(), case("error")]
    ev.write_json(path / "cases.json", cases)
    summary = ev.summarize(path)
    assert summary["errors"] == 1
    assert summary["attempted"] == 2
    assert summary["scored"] == 0
    assert summary["pass_rate"] is None
    assert summary["answer_point_score_pct"] is None
    assert "secret provider text" not in (path / "answers.jsonl").read_text()
    scores = path / "input.json"
    ev.write_json(scores, [{"case_id": "one", "rating": rating()}])
    summary = ev.grade(path, "test-reviewer", scores=scores)
    assert summary["pass_rate"] == .5
    assert summary["answer_point_score_pct"] == 100
    assert summary["scored"] == 1


def test_review_revisions_and_reports_never_overwrite_history(tmp_path):
    path = make_run(tmp_path / "run", [case(), case("unknown", False)])
    first = human_grade(path)
    assert first["pass_rate"] == 1
    assert first["rating_dimensions"]["abstention"] == {"n": 1, "mean_score_out_of_2": 2, "full_credit_rate": 1}
    second = human_grade(path, score=1)
    assert second["pass_rate"] == 0
    assert second["answer_point_score_pct"] == 50
    assert len(ev.read_jsonl(path / "reviews.jsonl")) == 4
    assert len(list((path / "reports").glob("*.json"))) == 2
    assert second["latency_p95_seconds"] >= second["latency_p50_seconds"]


@pytest.mark.parametrize("changes", [
    {"point_scores": []}, {"point_scores": [3]}, {"point_scores": [True]},
    {"groundedness": "2"}, {"abstention": 2}, {"citation_support": None}, {"notes": " "},
])
def test_invalid_human_import_does_not_append_partial_scores(tmp_path, changes):
    path = make_run(tmp_path / "run", [case(), case("two")])
    scores = path / "input.json"
    ev.write_json(scores, [{"case_id": "one", "rating": rating()},
                          {"case_id": "two", "rating": {**rating(), **changes}}])
    with pytest.raises(ValueError):
        ev.grade(path, "test-reviewer", scores=scores)
    assert not (path / "reviews.jsonl").exists()


def test_judge_records_exact_prompts_raw_outputs_and_parse_failures(tmp_path):
    path = make_run(tmp_path / "run", [case(), case("two")])
    judge = Mock(side_effect=[json.dumps(rating()), "not JSON"])
    summary = ev.grade(path, "test-judge", judge=judge, model="fake-offline-model")
    events = ev.read_jsonl(path / "reviews.jsonl")
    assert events[0]["messages"] == judge.call_args_list[0].args[0]
    payload = json.loads(events[0]["messages"][1]["content"])
    assert payload["case"]["question"] == case()["question"]
    assert payload["answer"]["sources"][0]["text"] == "A requirement."
    assert events[1]["raw_response"] == "not JSON"
    assert events[1]["error_type"] == "JSONDecodeError"
    assert summary["scored"] == 1
    assert summary["review_errors"] == 1
    assert summary["pass_rate"] is None


@pytest.mark.parametrize("answerable", [True, False])
def test_judge_schema_makes_abstention_applicability_explicit(answerable):
    messages = ev.judge_messages(case(answerable=answerable), answer())
    payload = json.loads(messages[1]["content"])
    properties = payload["schema"]["properties"]
    assert properties["abstention"]["type"] == ("null" if answerable else "integer")
    assert properties["point_scores"]["minItems"] == properties["point_scores"]["maxItems"] == 1
    assert "Only answer.sources was available" in messages[0]["content"]


def test_changed_answers_cannot_reuse_old_scores(tmp_path):
    path = make_run(tmp_path / "run")
    human_grade(path)
    row = ev.read_jsonl(path / "answers.jsonl")[0]
    row["answer"] = "A changed answer."
    (path / "answers.jsonl").write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="changed after grading"):
        ev.summarize(path)


def test_comparison_reports_regressions_and_rejects_changed_datasets(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "EVALS", tmp_path)
    before, after = make_run(tmp_path / "before"), make_run(tmp_path / "after")
    human_grade(before)
    human_grade(after, score=1)
    result = ev.compare(before, after)
    assert result["comparable"]
    assert result["deltas"]["answer_point_score_pct"] == -50
    assert result["deltas"]["pass_rate"] == -1
    assert result["case_changes"][0]["before_passed"] is True
    assert result["case_changes"][0]["after_passed"] is False
    metadata = json.loads((after / "run.json").read_text())
    metadata["cases_sha256"] = "different"
    ev.write_json(after / "run.json", metadata)
    result = ev.compare(before, after)
    assert not result["comparable"]
    assert result["deltas"] == {}
    assert len(list((tmp_path / "comparisons").glob("*.json"))) == 2


def test_comparison_rejects_incomplete_and_different_judges(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "EVALS", tmp_path)
    before, after = make_run(tmp_path / "before"), make_run(tmp_path / "after")
    human_grade(before)
    assert not ev.compare(before, after)["comparable"]
    ev.grade(after, "different-reviewer", judge=lambda messages: json.dumps(rating()), model="fake-model")
    assert not ev.compare(before, after)["comparable"]


def test_interruption_preserves_completed_questions(tmp_path):
    path = tmp_path / "run"
    path.mkdir()
    ask = Mock(side_effect=[answer(), KeyboardInterrupt()])
    with pytest.raises(KeyboardInterrupt):
        ev.collect_answers(path, [case(), case("two")], ask)
    assert [r["case_id"] for r in ev.read_jsonl(path / "answers.jsonl")] == ["one"]


def test_runner_uses_real_services_fresh_indexes_and_no_reference_leakage(tmp_path, monkeypatch):
    import openai
    from knowledgebase import config

    monkeypatch.setattr(ev, "ROOT", tmp_path)
    monkeypatch.setattr(ev, "EVALS", tmp_path / "evals")
    monkeypatch.setattr(ev, "git_state", lambda: {"commit": "test", "dirty": False})
    monkeypatch.setattr(config, "Settings", lambda: SimpleNamespace(openai_api_key="offline-test"))
    data_case = case()
    data_case["expected_answer_points"] = ["REFERENCE_ONLY_DO_NOT_SEND_TO_GENERATOR"]
    text = "The requirement is a GPA of 3.0."
    data_case["evidence"] = [{"file": "notes.txt", "start_offset": 0, "end_offset": len(text)}]
    monkeypatch.setattr(ev, "load_inputs", lambda path: ([data_case], {"corpus_id": "test"}, {"notes.txt": text}))
    sdk = Mock()
    sdk.embeddings.create.side_effect = lambda **kwargs: SimpleNamespace(
        data=[SimpleNamespace(embedding=[1.0, 0.0]) for item in kwargs["input"]])
    sdk.responses.create.return_value = SimpleNamespace(output_text="A GPA of 3.0. [1]")
    context = Mock()
    context.__enter__ = Mock(return_value=sdk)
    context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(openai, "OpenAI", Mock(return_value=context))
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text(json.dumps(data_case) + "\n")
    args = SimpleNamespace(cases=cases_path, label="Offline fixture", top_k=5, chunk_size=256,
                           overlap=64, model="offline-generator", embedding_model="offline-embeddings")
    first, second = ev.run(args), ev.run(args)
    assert first != second
    for path in (first, second):
        summary = ev.summarize(path)
        row = summary["rows"][0]["answer"]
        assert row["answer"] == "A GPA of 3.0. [1]"
        assert len(row["sources"]) == 1
        assert row["sources"][0]["start_offset"] == 0
        assert row["sources"][0]["end_offset"] == len(text)
        assert summary["annotated_char_recall"] == 1
        assert summary["pass_rate"] is None
    for call in sdk.responses.create.call_args_list:
        prompt = json.dumps(call.kwargs["input"])
        assert "REFERENCE_ONLY" not in prompt
        assert text in prompt
