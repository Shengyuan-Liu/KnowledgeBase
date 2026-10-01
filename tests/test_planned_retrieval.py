"""Independent-plan contracts with real SQLite/Chroma and offline query vectors."""

from pathlib import Path
import json
from unittest.mock import Mock

import pytest
import tiktoken
from pydantic import ValidationError

from knowledgebase.config import RetrievalOptions
from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.context import build_context
from knowledgebase.rag.parsing import parse_markdown
from knowledgebase.schemas import (
    AnswerRequirement, PlannedQuery, RetrievalPlan, direct_plan, PlannedEvidence, QueryRun, Chunk,
    RetrievedEvidence, RetrievedChunk, RetrievalDiagnostics,
)
from knowledgebase.rag.planned_retrieval import _select_representatives, merge_query_runs, retrieve_plan
from knowledgebase.rag.retrieval import retrieve_candidates, retrieve_evidence
from knowledgebase.storage.operations import (
    create_file, save_document_source, save_parent_child_chunks, update_file_status,
)


def plan_for(queries, *, question="Explain the methods and results."):
    return RetrievalPlan(
        original_question=question, resolved_question=question, route="decomposed",
        requirements=[AnswerRequirement(requirement_id=identity, description=identity)
                      for identity in dict.fromkeys(identity for query in queries for identity in query.requirement_ids)],
        queries=queries,
    )


def query(identity, text, requirement=None, file_ids=None):
    return PlannedQuery(query_id=identity, text=text, requirement_ids=[requirement or identity], file_ids=file_ids)


def index_document(session, store, identity, text, vector, status="ready"):
    create_file(session, identity, f"{identity}.md")
    blocks = parse_markdown(text)
    hierarchy = split_parent_child(text, blocks, identity, parent_max_tokens=90,
                                   child_max_tokens=18, encoding_name="cl100k_base")
    save_document_source(session, identity, "md", text, blocks)
    save_parent_child_chunks(session, hierarchy)
    store.upsert_chunks(hierarchy.children, [vector] * len(hierarchy.children))
    update_file_status(session, identity, status)
    return hierarchy


@pytest.fixture
def library(storage, embeddings):
    sessions, store, _ = storage
    with sessions.begin() as session:
        index_document(session, store, "alpha", "# Alpha\n\nThe method trains with labeled examples.\n\nAccuracy was ninety percent.", [1.0, 0.0])
        index_document(session, store, "beta", "# Beta\n\nThe method uses unlabeled examples.\n\nAccuracy was eighty percent.", [0.0, 1.0])
        index_document(session, store, "unfinished", "Hidden results", [1.0, 0.0], "processing")
    embeddings.embed_query.side_effect = lambda text: [0.0, 1.0] if "beta" in text.lower() else [1.0, 0.0]
    return sessions, store, embeddings


def test_plan_validation_and_direct_constructor():
    plan = direct_plan("What about its results?", resolved_question="What were Alpha's results?")
    assert plan.original_question == "What about its results?"
    assert plan.queries[0].text == plan.resolved_question
    assert RetrievalPlan.model_validate_json(plan.model_dump_json()) == plan
    valid = plan_for([query("q1", "methods", "method"), query("q2", "results", "result")]).model_dump()
    invalid = []
    unknown = {**valid, "queries": [{**valid["queries"][0], "requirement_ids": ["unknown"]}]}
    invalid.append(unknown)
    invalid.append({**valid, "queries": [valid["queries"][0]]})
    invalid.append({**valid, "queries": [valid["queries"][0], valid["queries"][0], valid["queries"][1]]})
    invalid.append({**valid, "requirements": valid["requirements"] * 2})
    invalid.append({**valid, "route": "direct"})
    invalid.append({**valid, "queries": [{**valid["queries"][0], "depends_on": ["q2"]}, valid["queries"][1]]})
    invalid.append({**valid, "queries": [{**valid["queries"][0], "text": "  "}, valid["queries"][1]]})
    invalid.append({**valid, "queries": [{**valid["queries"][0], "query_id": f"q{i}"} for i in range(7)]})
    for value in invalid:
        with pytest.raises(ValidationError):
            RetrievalPlan.model_validate(value)


def test_unpacked_candidates_do_not_spend_context_budget(library):
    sessions, store, embeddings = library
    with sessions() as session:
        hits = retrieve_candidates("method", session, embeddings, store, evidence_max_tokens=1)
    assert hits.chunks
    assert hits.diagnostics.packing_seconds is None
    assert not hits.diagnostics.excluded
    assert all(hit.chunk.chunk_id != hit.parent_id for hit in hits.chunks)


@pytest.mark.parametrize("strategy", ["vector", "hybrid"])
@pytest.mark.parametrize("scoped", [False, True])
def test_direct_plan_preserves_existing_evidence(library, strategy, scoped):
    sessions, store, embeddings = library
    options = RetrievalOptions(strategy=strategy)
    kwargs = {"retrieval_options": options, "file_ids": ["alpha", "beta"] if scoped else None, "top_k": 3}
    with sessions() as session:
        baseline = retrieve_evidence("method", session, embeddings, store, **kwargs)
        planned = retrieve_plan(direct_plan("method"), session, embeddings, store, **kwargs)
    assert planned.evidence.chunks == baseline.chunks
    assert build_context(planned.evidence.chunks) == build_context(baseline.chunks)
    assert planned.evidence.diagnostics.evidence_tokens == baseline.diagnostics.evidence_tokens
    assert len(planned.trace.runs) == 1
    assert PlannedEvidence.model_validate_json(planned.model_dump_json()).model_dump() == planned.model_dump()


def fake_run(text, identities):
    hits = [RetrievedChunk(chunk=Chunk(chunk_id=identity, file_id=identity[0], text=identity, index=0,
                                      start_offset=0, end_offset=len(identity)),
                           file_name=identity[0], distance=None) for identity in identities]
    return QueryRun(query_ids=[text], requirement_ids=[text], text=text, requested_file_ids=None,
                    result=RetrievedEvidence(chunks=hits, diagnostics=RetrievalDiagnostics(max_tokens=10, tokenizer="cl100k_base")), seconds=0)


def test_cross_query_rrf_and_repeated_text_votes():
    runs = [fake_run("first", ["a1", "b1"]), fake_run("second", ["b1", "a1"])]
    merged = merge_query_runs(runs, k=60)
    assert [hit.chunk_id for hit in merged] == ["a1", "b1"]
    assert [hit.score for hit in merged] == pytest.approx([1/61 + 1/62] * 2)
    # A repeated query in another scope uses its best rank, not another vote.
    merged = merge_query_runs([*runs, fake_run(" first ", ["b1"])], k=60)
    assert merged[0].chunk_id == "b1" and merged[0].score == pytest.approx(2/61)
    assert len(merged[0].votes) == 2


@pytest.mark.parametrize("case", json.loads(
    (Path(__file__).parent / "fixtures/planned_pdf_rankings.json").read_text())["cases"],
    ids=lambda case: case["case"])
def test_pdf_answer_points_keep_their_query_local_leaders(case):
    """Replay live rankings that previously lost grades and guest lecturers."""
    runs = []
    for row in case["runs"]:
        hits = [RetrievedChunk(chunk=Chunk(**hit, index=0, start_offset=0,
                                          end_offset=len(hit["text"])),
                               file_name="ml-lecture.pdf", distance=None) for hit in row["hits"]]
        runs.append(QueryRun(**{k: v for k, v in row.items() if k != "hits"},
                             requested_file_ids=None, seconds=0,
                             result=RetrievedEvidence(chunks=hits, diagnostics=RetrievalDiagnostics(
                                 max_tokens=4096, tokenizer="cl100k_base"))))
    selected = _select_representatives(merge_query_runs(runs, k=60), runs,
                                      RetrievalPlan.model_validate(case["plan"]), 5)
    assert set(case["required_child_suffixes"]) <= {identity.split(":")[-1] for identity in selected}
    assert len(selected) == len(set(selected)) == 5


def test_duplicate_queries_execute_once_and_keep_both_requirements(library):
    sessions, store, embeddings = library
    plan = plan_for([query("one", "method", "method"), query("two", "method", "result")])
    with sessions() as session:
        result = retrieve_plan(plan, session, embeddings, store)
    embeddings.embed_query.assert_called_once_with("method")
    assert result.trace.runs[0].query_ids == ["one", "two"]
    assert all(len(hit.votes) == 1 for hit in result.trace.merged)
    assert all(item.supplied_ids for item in result.trace.requirements)
    assert result.trace.requirements[0].supplied_ids == result.trace.requirements[1].supplied_ids
    assert not any(hit.file_id == "unfinished" for hit in result.trace.merged)


def test_independent_queries_have_one_budget_and_record_what_was_excluded(library):
    sessions, store, embeddings = library
    plan = plan_for([query("a", "alpha method", file_ids=["alpha"]), query("b", "beta method", file_ids=["beta"])])
    with sessions() as session:
        complete = retrieve_plan(plan, session, embeddings, store, top_k=2)
        tiny = retrieve_plan(plan, session, embeddings, store, top_k=2, evidence_max_tokens=1)
    assert {hit.chunk.file_id for hit in complete.evidence.chunks} == {"alpha", "beta"}
    assert len({hit.chunk.chunk_id for hit in complete.evidence.chunks}) == len(complete.evidence.chunks)
    for result in [complete, tiny]:
        actual = len(tiktoken.get_encoding("cl100k_base").encode_ordinary(build_context(result.evidence.chunks)))
        assert actual == result.evidence.diagnostics.evidence_tokens <= result.trace.max_evidence_tokens
        assert all(run.result.diagnostics.packing_seconds is None for run in result.trace.runs)
    assert not tiny.evidence.chunks
    assert all(item.budget_excluded_ids and not item.supplied_ids for item in tiny.trace.requirements)


def test_multiple_query_hits_share_one_parent(library):
    sessions, store, embeddings = library
    plan = plan_for([query("one", "labeled", file_ids=["alpha"]), query("two", "accuracy", file_ids=["alpha"])])
    with sessions() as session:
        result = retrieve_plan(plan, session, embeddings, store, top_k=5)
    assert len(result.evidence.chunks) == 1
    assert len(set(result.trace.selected_ids)) == len(result.trace.selected_ids)
    assert set(result.evidence.chunks[0].matched_child_ids) == set(result.trace.selected_ids)


def test_scope_expansion_is_rejected_before_any_query(library):
    sessions, store, embeddings = library
    plan = plan_for([query("allowed", "method", file_ids=["alpha"]), query("outside", "results", file_ids=["beta"])])
    with sessions() as session, pytest.raises(ValueError, match="expand"):
        retrieve_plan(plan, session, embeddings, store, file_ids=["alpha"])
    embeddings.embed_query.assert_not_called()


@pytest.mark.parametrize("question", ['In "alpha.md", describe methods.', 'Describe methods.'])
def test_textual_subquery_cannot_escape_parent_scope(library, question):
    sessions, store, embeddings = library
    plan = plan_for([query("outside", 'In "beta.md", describe results.')], question=question)
    with sessions() as session:
        result = retrieve_plan(plan, session, embeddings, store, file_ids=["alpha"])
    assert not result.evidence.chunks
    assert result.trace.runs[0].result.diagnostics.document_scope.status == "not_found"
    assert result.trace.requirements[0].candidate_ids == []
    embeddings.embed_query.assert_not_called()


def test_empty_scope_is_not_global_scope(library):
    sessions, store, embeddings = library
    with sessions() as session:
        result = retrieve_plan(direct_plan("method"), session, embeddings, store, file_ids=[])
        narrowed = retrieve_plan(plan_for([query("empty", "method", file_ids=[])]), session, embeddings, store)
    assert not result.trace.runs and result.trace.stop_reason == "no_ready_files"
    assert not narrowed.evidence.chunks
    embeddings.embed_query.assert_not_called()


def test_unknown_scope_does_not_query(library):
    sessions, store, embeddings = library
    with sessions() as session:
        result = retrieve_plan(direct_plan('In "unknown.md", describe results.'), session, embeddings, store)
    assert result.trace.stop_reason == "scope_unresolved"
    assert not result.trace.runs
    embeddings.embed_query.assert_not_called()


def test_provider_error_propagates_without_retry(library):
    sessions, store, embeddings = library
    embeddings.embed_query.side_effect = RuntimeError("offline provider failed")
    with sessions() as session, pytest.raises(RuntimeError, match="offline provider failed"):
        retrieve_plan(plan_for([query("a", "alpha"), query("b", "beta")]), session, embeddings, store)
    embeddings.embed_query.assert_called_once_with("alpha")


def test_query_candidate_ranks_remain_fusion_ranks_in_multiple_file_scope(library):
    sessions, store, embeddings = library
    with sessions() as session:
        result = retrieve_plan(plan_for([query("a", "labeled examples"), query("b", "accuracy")]), session, embeddings, store,
                               file_ids=["alpha", "beta"], retrieval_options=RetrievalOptions(candidate_limit=3))
    for run in result.trace.runs:
        assert [hit.chunk.chunk_id for hit in run.result.chunks] == [hit.chunk_id for hit in run.result.diagnostics.fused_matches[:3]]


def test_pdf_supplements_remain_inside_final_shared_budget(storage, embeddings):
    from knowledgebase.schemas import File
    from knowledgebase.services.files import DocumentChunker, FileService
    from knowledgebase.storage.pdf_assets import PdfAssets
    from tempfile import TemporaryDirectory

    sessions, store, _ = storage
    root = Path(__file__).resolve().parents[1]
    extraction = File.model_validate({"type": "pdf", **json.loads((root / "evals/check-runs/20260926-pdf-parser-selection/adapter-2/apple-fy24.json").read_text())})
    with TemporaryDirectory() as directory:
        identity = FileService(sessions, store, embeddings=embeddings, assets=PdfAssets(Path(directory)), pdf_parser=Mock(parse=Mock(return_value=extraction)), chunker=DocumentChunker(chunk_max_tokens=48, parent_max_tokens=96)).ingest("apple.pdf", (root / "evals/materials/pdf-v2/apple-fy24.pdf").read_bytes())
        with sessions() as session:
            result = retrieve_plan(plan_for([query("sales", "net sales"), query("income", "net income")]),
                                   session, embeddings, store, file_ids=[identity], evidence_max_tokens=1800)
    assert result.evidence.chunks
    assert all(hit.pdf and hit.pdf.revision_id == extraction.revision_id for hit in result.evidence.chunks)
    assert any(hit.pdf.supplements for hit in result.evidence.chunks)
    from knowledgebase.rag.dependencies import dependency_evidence, validate_binding
    from knowledgebase.schemas import TargetDecision
    excerpts = dependency_evidence(result, ["sales", "income"])
    supplement = next(extra for hit in result.evidence.chunks for extra in hit.pdf.supplements)
    excerpt = next(e for e in excerpts if e["start_offset"] == supplement.start_offset and e["text"] == supplement.text)
    refs = validate_binding(TargetDecision(query_id="next", status="resolved", target=supplement.text,
        references=[{"evidence_id": excerpt["evidence_id"], "quote": supplement.text}]), excerpts)
    assert refs[0]["start_offset"] == supplement.start_offset
    assert refs[0]["end_offset"] == supplement.end_offset
    assert dependency_evidence(result, ["unrelated-query"]) == []
    assert len(tiktoken.get_encoding("cl100k_base").encode_ordinary(build_context(result.evidence.chunks))) <= 1800


def test_round_robin_gives_later_requirements_a_slot(library):
    sessions, store, embeddings = library
    with sessions.begin() as session:
        index_document(session, store, "gamma", "A third method uses more examples.", [1.0, 0.0])
    plan = plan_for([query("a", "methods", file_ids=["alpha", "gamma"]),
                     query("b", "beta results", file_ids=["beta"])])
    with sessions() as session:
        result = retrieve_plan(plan, session, embeddings, store, top_k=2)
    assert all(requirement.selected_ids for requirement in result.trace.requirements)
    assert len(result.trace.selected_ids) == 2
    assert any(hit.chunk.file_id == "beta" for hit in result.evidence.chunks)


def test_no_ready_library_has_no_execution(storage, embeddings):
    sessions, store, _ = storage
    with sessions() as session:
        result = retrieve_plan(direct_plan("method"), session, embeddings, store)
    assert result.trace.stop_reason == "no_ready_files"
    assert not result.trace.runs and not result.evidence.chunks
    embeddings.embed_query.assert_not_called()


def test_original_scope_survives_resolved_question_rewrite(library):
    sessions, store, embeddings = library
    plan = direct_plan('In "alpha.md", explain the method.', resolved_question="Explain training methods.")
    with sessions() as session:
        result = retrieve_plan(plan, session, embeddings, store)
    assert result.trace.allowed_file_ids == ["alpha"]
    assert {hit.chunk.file_id for hit in result.evidence.chunks} == {"alpha"}
