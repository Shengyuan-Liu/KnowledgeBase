"""Offline evaluation accounting, evidence coverage, and audit-trail tests."""

import json
from pathlib import Path
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


def assessment():
    return {"points": [{"answer_quotes": ["A requirement."], "reason": "The answer states the requirement.", "score": 2}],
            "claims": [{"answer_quote": "A requirement. [1]", "sources": [{"source_id": 1, "quote": "A requirement."}],
                        "reason": "Source [1] supports this sentence.", "groundedness": 2, "citation_support": 2}],
            "abstention": {"verdict": "not_applicable", "answer_quotes": [], "reason": "Answerable question."}}


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


def test_revised_questions_explicitly_request_scored_details():
    cases, _, _ = ev.load_inputs(ev.EVALS / "nyu-test-cases.jsonl")
    indexed = {c["id"]: c for c in cases}
    assert "what materials" in indexed["msds-waiver"]["question"]
    assert "course availability" in indexed["msds-credits"]["question"]
    assert "after the first year" not in indexed["msds-cpt-source-context"]["question"]
    assert "external" not in indexed["missing-exact-tuition-bill"]["expected_answer_points"][1]


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
    judge = Mock(side_effect=[json.dumps(assessment()), "not JSON"])
    summary = ev.grade(path, "test-judge", judge=judge, model="fake-offline-model")
    events = ev.read_jsonl(path / "reviews.jsonl")
    assert events[0]["messages"] == judge.call_args_list[0].args[0]
    payload = json.loads(events[0]["messages"][1]["content"])
    assert payload["case"]["question"] == case()["question"]
    assert payload["answer"]["sources"][0]["text"] == "A requirement."
    assert events[1]["raw_response"] == "not JSON"
    assert events[1]["error_type"] == "JSONDecodeError"
    assert events[0]["assessment"] == assessment()
    assert events[0]["judge_protocol_version"] == 3
    assert summary["scored"] == 1
    assert summary["review_errors"] == 1
    assert summary["pass_rate"] is None
    rendered = next((path / "reports").glob("*.md")).read_text()
    assert "### Judge evidence" in rendered
    assert "Point 1 (2/2), answer quotes:" in rendered


@pytest.mark.parametrize("answerable", [True, False])
def test_judge_schema_makes_abstention_applicability_explicit(answerable):
    messages = ev.judge_messages(case(answerable=answerable), answer())
    payload = json.loads(messages[1]["content"])
    properties = payload["schema"]["properties"]
    verdicts = payload["schema"]["$defs"]["AbstentionAssessment"]["properties"]["verdict"]["enum"]
    assert ("not_applicable" in verdicts) == answerable
    assert properties["points"]["minItems"] == properties["points"]["maxItems"] == 1
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
    ev.grade(after, "different-reviewer", judge=lambda messages: json.dumps(assessment()), model="fake-model")
    assert not ev.compare(before, after)["comparable"]


def test_interruption_preserves_completed_questions(tmp_path):
    path = tmp_path / "run"
    path.mkdir()
    ask = Mock(side_effect=[answer(), KeyboardInterrupt()])
    with pytest.raises(KeyboardInterrupt):
        ev.collect_answers(path, [case(), case("two")], ask)
    assert [r["case_id"] for r in ev.read_jsonl(path / "answers.jsonl")] == ["one"]


@pytest.mark.parametrize("explicit_options", [False, True])
@pytest.mark.parametrize("strategy", ["structural", "character", "parent_child"])
def test_runner_uses_real_services_fresh_indexes_and_no_reference_leakage(tmp_path, monkeypatch, explicit_options, strategy):
    import openai

    monkeypatch.setattr(ev, "ROOT", tmp_path)
    monkeypatch.setattr(ev, "EVALS", tmp_path / "evals")
    monkeypatch.setattr(ev, "git_state", lambda: {"commit": "test", "dirty": False})
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    (tmp_path / ".env").write_text(
        "ANSWER_MODEL=env-generator\nEMBEDDING_MODEL=env-embeddings\n"
        "CHUNK_SIZE=64\nCHUNK_OVERLAP=8\nRETRIEVAL_TOP_K=2\n"
        "EVAL_TIMEOUT_SECONDS=17\nEVAL_MAX_RETRIES=1\n"
        f"CHUNKING_STRATEGY={strategy}\nCHUNK_MAX_TOKENS=32\nCHUNK_TOKENIZER=cl100k_base\n"
        "PARENT_MAX_TOKENS=96\nEVIDENCE_MAX_TOKENS=192\n"
        "RETRIEVAL_STRATEGY=hybrid\nRETRIEVAL_CANDIDATE_LIMIT=9\nBM25_K1=0.8\nBM25_B=0.4\nRRF_K=12\n"
    )
    data_case = case()
    data_case["expected_answer_points"] = ["REFERENCE_ONLY_DO_NOT_SEND_TO_GENERATOR"]
    text = "# GPA\n\nThe requirement is a GPA of 3.0."
    data_case["evidence"] = [{"file": "notes.md", "start_offset": 0, "end_offset": len(text)}]
    monkeypatch.setattr(ev, "load_inputs", lambda path: ([data_case], {"corpus_id": "test"}, {"notes.md": text}))
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
                           chunking_strategy={"structural": "character", "character": "parent_child", "parent_child": "structural"}[strategy],
                           chunk_max_tokens=64, chunk_tokenizer="o200k_base", parent_max_tokens=128, evidence_max_tokens=256,
                           overlap=64, model="offline-generator", embedding_model="offline-embeddings",
                           retrieval_strategy="vector" if explicit_options else None,
                           retrieval_candidate_limit=7 if explicit_options else None,
                           bm25_k1=None, bm25_b=None, rrf_k=None)
    if not explicit_options:
        for name in ("model", "embedding_model", "chunk_size", "overlap", "top_k",
                     "chunking_strategy", "chunk_max_tokens", "chunk_tokenizer", "parent_max_tokens", "evidence_max_tokens"):
            setattr(args, name, None)
    first, second = ev.run(args), ev.run(args)
    assert first != second
    for path in (first, second):
        summary = ev.summarize(path)
        recorded = summary["run"]["config"]
        assert recorded["model"] == ("offline-generator" if explicit_options else "env-generator")
        assert recorded["embedding_model"] == ("offline-embeddings" if explicit_options else "env-embeddings")
        assert recorded["chunk_size"] == (256 if explicit_options else 64)
        assert recorded["overlap"] == (64 if explicit_options else 8)
        assert recorded["top_k"] == (5 if explicit_options else 2)
        assert recorded["timeout_seconds"] == 17
        assert recorded["max_retries"] == 1
        assert recorded["chunking_strategy"] == args.chunking_strategy
        assert recorded["chunk_max_tokens"] == (64 if explicit_options else 32)
        assert recorded["chunk_tokenizer"] == ("o200k_base" if explicit_options else "cl100k_base")
        assert recorded["effective_overlap"] == (args.overlap if args.chunking_strategy == "character" else 0)
        assert (tmp_path / "data" / "evals" / path.name / "knowledgebase.db").exists()
        row = summary["rows"][0]["answer"]
        assert row["answer"] == "A GPA of 3.0. [1]"
        assert row["citation_check"] == {"valid_source_ids": [1], "invalid_source_ids": [], "no_citations": False}
        assert summary["citation_checks_recorded"] == 1
        assert len(row["sources"]) == 1
        assert row["sources"][0]["start_offset"] == 0
        assert row["sources"][0]["end_offset"] == len(text)
        if args.chunking_strategy != "character":
            assert row["sources"][0]["heading_path"] == ["GPA"]
            assert row["sources"][0]["tokenizer"] == args.chunk_tokenizer
            assert row["sources"][0]["max_tokens"] == (args.parent_max_tokens if args.chunking_strategy == "parent_child" else args.chunk_max_tokens)
        assert recorded["parent_max_tokens"] == args.parent_max_tokens
        assert recorded["evidence_max_tokens"] == args.evidence_max_tokens
        options = {"strategy": "vector" if explicit_options else "hybrid",
                   "candidate_limit": 7 if explicit_options else 9, "bm25_k1": 0.8, "bm25_b": 0.4, "rrf_k": 12}
        assert row["retrieval_diagnostics"]["options"] == recorded["retrieval_options"] == options
        assert row["retrieval_diagnostics"]["max_tokens"] == args.evidence_max_tokens
        if args.chunking_strategy == "parent_child":
            assert row["sources"][0]["parent_id"] == row["sources"][0]["chunk_id"]
            assert row["sources"][0]["matched_child_ids"] == [row["retrieval_diagnostics"]["candidates"][0]["chunk_id"]]
        assert summary["annotated_char_recall"] == 1
        assert summary["pass_rate"] is None
    for call in sdk.embeddings.create.call_args_list:
        assert call.kwargs["model"] == args.embedding_model
    assert all(call.kwargs["timeout"] == 17 and call.kwargs["max_retries"] == 1
               for call in openai.OpenAI.call_args_list)
    for call in sdk.responses.create.call_args_list:
        assert call.kwargs["model"] == args.model
        prompt = json.dumps(call.kwargs["input"])
        assert "REFERENCE_ONLY" not in prompt
        assert any(text in message["content"] for message in call.kwargs["input"])


def test_citation_diagnostics_preserve_unchecked_history_and_do_not_assign_grades(tmp_path):
    cases = [case("legacy"), case("invalid"), case("refusal", False)]
    path = make_run(tmp_path / "run", cases[:1])
    ev.write_json(path / "cases.json", cases)
    results = [
        {**answer(), "answer": "A requirement. [1][5]", "citation_check": {
            "valid_source_ids": [1], "invalid_source_ids": [5], "no_citations": False}},
        {"answer": "Insufficient evidence.", "sources": [], "citation_check": {
            "valid_source_ids": [], "invalid_source_ids": [], "no_citations": True}},
    ]
    ev.collect_answers(path, cases[1:], Mock(side_effect=results))
    recorded = ev.read_jsonl(path / "answers.jsonl")
    assert "citation_check" not in recorded[0]
    assert recorded[1]["citation_check"]["invalid_source_ids"] == [5]
    assert recorded[1]["answer"] == "A requirement. [1][5]"
    summary = ev.report(path)
    assert summary["citation_checks_recorded"] == 2
    assert summary["answers_with_invalid_citation_ids"] == 1
    assert summary["answers_without_numbered_citations"] == 1
    assert summary["scored"] == 0
    assert summary["pass_rate"] is None
    report = next((path / "reports").glob("*.md")).read_text()
    assert "Not recorded for this answer." in report
    assert "Invalid source IDs: [5]" in report


def recorded_case(case_id, candidate=True):
    run_id = "20260920T235545Z-199abacb" if candidate else "20260920T235448Z-2d9f6276"
    path = ev.EVALS / "runs" / run_id
    data_case = next(c for c in json.loads((path / "cases.json").read_text()) if c["id"] == case_id)
    recorded = next(a for a in ev.read_jsonl(path / "answers.jsonl") if a["case_id"] == case_id)
    return data_case, recorded


def test_judge_context_excludes_gold_excerpts_metrics_and_old_ratings():
    data_case, recorded = recorded_case("msds-online")
    recorded["previous_rating"] = rating()
    payload = json.loads(ev.judge_messages(data_case, recorded)[1]["content"])
    assert set(payload["case"]) == {"id", "question", "answerable", "expected_answer_points", "scoring_notes"}
    assert set(payload["answer"]) == {"answer", "sources"}
    assert all(set(s) == {"source_id", "file_name", "text"} for s in payload["answer"]["sources"])
    assert payload["case"]["expected_answer_points"] == data_case["expected_answer_points"]


@pytest.mark.parametrize("quotes", [[], ["Submit transcripts and syllabi for review."]])
def test_missing_waiver_instructions_cannot_receive_credit_without_answer_evidence(quotes):
    data_case, recorded = recorded_case("msds-waiver")
    value = assessment()
    value["points"] = [
        {"answer_quotes": ["DS-GA 1002"], "reason": "Names the course.", "score": 2},
        {"answer_quotes": quotes, "reason": "Incorrectly credits omitted instructions.", "score": 2}]
    with pytest.raises(ev.JudgeEvidenceError):
        ev.validate_assessment(data_case, recorded, value)


def test_gold_only_online_statement_cannot_be_used_as_retrieved_evidence():
    data_case, recorded = recorded_case("msds-online")
    value = assessment()
    value["points"] = [{"answer_quotes": [], "reason": "Does not answer online availability.", "score": 0}]
    value["claims"] = [{"answer_quote": recorded["answer"],
                        "sources": [{"source_id": 1, "quote": "No, we do not have an online program."}],
                        "reason": "Erroneously treats a gold reference as retrieved.", "groundedness": 0, "citation_support": 0}]
    with pytest.raises(ev.JudgeEvidenceError, match="exact nonempty substring"):
        ev.validate_assessment(data_case, recorded, value)
    value["claims"] = []
    result, _ = ev.validate_assessment(data_case, recorded, value)
    assert result["point_scores"] == [0]
    assert result["groundedness"] == result["citation_support"] == 2
    assert result["abstention"] is None


def test_single_sentence_end_citation_can_support_both_gpa_facts():
    data_case, recorded = recorded_case("msds-gpa", candidate=False)
    value = assessment()
    value["points"] = [
        {"answer_quotes": ["minimum GPA of 3.0 each semester"], "reason": "GPA is stated.", "score": 2},
        {"answer_quotes": ["at least 66% of their attempted credits"], "reason": "Completion is stated.", "score": 2}]
    value["claims"] = [{"answer_quote": recorded["answer"], "sources": [{"source_id": 3,
        "quote": "students must maintain a minimum GPA of 3.0 and must successfully complete 66% of credits attempted."}],
        "reason": "One sentence-end citation supports both facts.", "groundedness": 2, "citation_support": 2}]
    result, _ = ev.validate_assessment(data_case, recorded, value)
    assert result["point_scores"] == [2, 2]
    assert result["citation_support"] == 2


@pytest.mark.parametrize("case_id,verdict,expected", [
    ("missing-personal-capstone-team", "explicit_missing_information", 2),
    ("missing-exact-tuition-bill", "invented_specifics", 0),
])
def test_observed_refusal_classifications_map_to_scores_without_an_independent_grade(case_id, verdict, expected):
    data_case, recorded = recorded_case(case_id)
    value = assessment()
    value["points"] = [{"answer_quotes": [], "reason": "Fixture tests abstention mapping only.", "score": 0}
                       for _ in data_case["expected_answer_points"]]
    value["claims"] = []
    value["abstention"] = {"verdict": verdict, "answer_quotes": [recorded["answer"]],
                           "reason": "Acknowledges missing personal information." if expected == 2 else "Invents a zero-dollar bill."}
    result, _ = ev.validate_assessment(data_case, recorded, value)
    assert result["abstention"] == expected


def test_invalid_judge_evidence_is_pending_and_preserves_the_previous_review(tmp_path):
    path = make_run(tmp_path / "run")
    human_grade(path)
    old = (path / "reviews.jsonl").read_bytes()
    bad = assessment()
    bad["points"][0]["answer_quotes"] = ["An instruction the answer never gave."]
    result = ev.grade(path, "test-judge", judge=lambda messages: json.dumps(bad), model="fake-model")
    assert (path / "reviews.jsonl").read_bytes().startswith(old)
    event = ev.read_jsonl(path / "reviews.jsonl")[-1]
    assert event["raw_response"] == json.dumps(bad)
    assert event["error_type"] == "JudgeEvidenceError" and "validation_error" in event
    assert result["scored"] == 0 and result["pass_rate"] is None


@pytest.mark.parametrize("change", [
    {"sources": [{"source_id": 99, "quote": "A requirement."}]},
    {"sources": [], "groundedness": 2},
    {"groundedness": 0, "citation_support": 2},
])
def test_factual_support_cannot_be_credited_without_matching_source_evidence(change):
    value = assessment()
    value["claims"][0].update(change)
    with pytest.raises(ev.JudgeEvidenceError):
        ev.validate_assessment(case(), answer(), value)


def test_comparison_rejects_different_protocols_even_with_the_same_reviewer(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "EVALS", tmp_path)
    before, after = make_run(tmp_path / "before"), make_run(tmp_path / "after")
    judge = lambda messages: json.dumps(assessment())
    ev.grade(before, "same-reviewer", judge=judge, model="fake-model")
    monkeypatch.setattr(ev, "JUDGE_PROTOCOL_VERSION", 4)
    ev.grade(after, "same-reviewer", judge=judge, model="fake-model")
    result = ev.compare(before, after)
    assert not result["comparable"] and result["deltas"] == {}


def test_live_judge_requests_strict_schema_and_does_not_repair_raw_output():
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(output_text='{"unexpected": "retained"}')
    messages = ev.judge_messages(case(), answer())
    assert ev.request_judgment(client, "fake-model", messages) == '{"unexpected": "retained"}'
    kwargs = client.responses.create.call_args.kwargs
    assert kwargs["model"] == "fake-model" and kwargs["input"] == messages
    format_spec = kwargs["text"]["format"]
    assert format_spec["type"] == "json_schema" and format_spec["strict"] is True
    assert format_spec["schema"] == json.loads(messages[1]["content"])["schema"]
    assert format_spec["schema"]["additionalProperties"] is False
    assert "issues" not in format_spec["schema"]["properties"]


@pytest.mark.parametrize("model_arg", [[], ["explicit-judge"]])
def test_grading_uses_configured_judge_unless_explicitly_overridden(tmp_path, monkeypatch, model_arg):
    import sys
    import openai
    from unittest.mock import MagicMock

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    (tmp_path / ".env").write_text("JUDGE_MODEL=env-judge\nEVAL_TIMEOUT_SECONDS=17\nEVAL_MAX_RETRIES=1\n")
    sdk = MagicMock()
    sdk.__enter__.return_value = sdk
    sdk.responses.create.return_value = SimpleNamespace(output_text="{}")
    sdk_factory = Mock(return_value=sdk)
    monkeypatch.setattr(openai, "OpenAI", sdk_factory)
    recorded = {}

    def grade(run_dir, reviewer, *, judge, model):
        recorded["model"] = model
        judge(ev.judge_messages(case(), answer()))

    monkeypatch.setattr(ev, "grade", grade)
    monkeypatch.setattr(sys, "argv", ["evaluate", "grade", "run", "--reviewer", "test", "--judge-model", *model_arg])
    ev.main()
    expected = model_arg[0] if model_arg else "env-judge"
    assert recorded["model"] == expected
    assert sdk.responses.create.call_args.kwargs["model"] == expected
    sdk_factory.assert_called_once_with(api_key="offline-test", base_url=None, timeout=17, max_retries=1)


def test_offline_eval_commands_do_not_require_settings_or_credentials(tmp_path, monkeypatch):
    import sys
    from knowledgebase import config

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = Mock(side_effect=AssertionError("Offline reports must not read credentials"))
    monkeypatch.setattr(config, "Settings", settings)
    reporter = Mock()
    monkeypatch.setattr(ev, "report", reporter)
    monkeypatch.setattr(sys, "argv", ["evaluate", "report", "saved-run"])
    ev.main()
    reporter.assert_called_once_with(Path("saved-run"))
    settings.assert_not_called()
