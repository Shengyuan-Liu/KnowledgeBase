"""Regressions for losing complete selected facts when their parents do not fit."""

import json

import pytest
import tiktoken
from fastapi.testclient import TestClient

from knowledgebase import bootstrap
from knowledgebase.api import app as api_module
from knowledgebase.schemas.options import RetrievalOptions
from knowledgebase.rag.context import build_context
from knowledgebase.rag.packing import pack_evidence
from knowledgebase.schemas import (
    Chunk,
    ExcludedEvidence,
    RetrievalDiagnostics,
    RetrievedChunk,
    VectorMatch,
)
from knowledgebase.storage.operations import get_chunks


def region(identity, text, parent_id=None, matched=(), offset=0):
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id=identity,
            file_id=identity.split(":")[0],
            text=text,
            index=0,
            start_offset=offset,
            end_offset=offset + len(text),
        ),
        file_name="facts.md",
        distance=0.1,
        parent_id=parent_id,
        matched_child_ids=list(matched),
    )


def tokens(regions):
    return len(tiktoken.get_encoding("cl100k_base").encode_ordinary(build_context(regions)))


def pack(selected, expanded, budget, strategy="parent_then_child"):
    return pack_evidence(
        selected,
        expanded,
        RetrievalDiagnostics(
            max_tokens=budget,
            tokenizer="cl100k_base",
            options=RetrievalOptions(packing_strategy=strategy),
        ),
    )


def test_preserves_parent_and_two_whole_siblings_without_duplicate_evidence():
    a = region("a:child:0", "First fact.", "a:parent:0", ["a:child:0"])
    a_parent = region(
        "a:parent:0", "First fact. " + "Context. " * 20, "a:parent:0", a.matched_child_ids
    )
    b = region("b:child:0", "Internships after the first year.\r\n", "b:parent:0", ["b:child:0"])
    c = region("b:child:1", "Consult OGS.\n", "b:parent:0", ["b:child:1"], len(b.chunk.text))
    b_parent = region(
        "b:parent:0",
        b.chunk.text + c.chunk.text + "Other material. " * 100,
        "b:parent:0",
        [b.chunk.chunk_id, c.chunk.chunk_id],
    )
    flat = region("flat", "Legacy fact.")
    selected, expanded = [a, b, c, flat], [a_parent, b_parent, flat]
    budget = tokens([a_parent, b, c, flat])
    old = pack(selected, expanded, budget, "parent_first")
    assert old.chunks == [a_parent, flat]
    new = pack(selected, expanded, budget)
    assert new.chunks == [a_parent, b, c, flat]
    assert new.diagnostics.evidence_tokens == budget
    assert new.diagnostics.excluded == []
    assert [p.chunk_id for p in new.diagnostics.unexpanded_parents] == ["b:parent:0"]
    assert all(s.chunk.chunk_id != "b:parent:0" for s in new.chunks)
    assert new.diagnostics.packing_seconds >= 0
    short = pack(selected, expanded, budget - 1)
    assert short.chunks == [a_parent, b, c]
    assert [s.chunk_id for s in short.diagnostics.excluded] == ["flat"]
    assert short.diagnostics.evidence_tokens <= budget - 1


def test_high_ranked_child_is_considered_before_a_lower_ranked_parent():
    """The live financial failure packed cash flows before selected sales rows."""
    sales = region("sales:child:0", "Total net sales: 94,930.", "sales:parent:0", ["sales:child:0"])
    sales_parent = region(
        "sales:parent:0",
        sales.chunk.text + "Other rows. " * 200,
        sales.parent_id,
        sales.matched_child_ids,
    )
    cash = region("cash:child:0", "Cash flow totals.", "cash:parent:0", ["cash:child:0"])
    cash_parent = region(
        "cash:parent:0",
        cash.chunk.text + "Other cash flows. " * 20,
        cash.parent_id,
        cash.matched_child_ids,
    )
    budget = tokens([cash_parent])
    assert tokens([sales, cash_parent]) > budget
    result = pack([sales, cash], [sales_parent, cash_parent], budget)
    assert result.chunks == [sales, cash]
    assert result.diagnostics.excluded == []
    assert {p.chunk_id for p in result.diagnostics.unexpanded_parents} == {
        sales.parent_id,
        cash.parent_id,
    }
    assert pack([sales, cash], [sales_parent, cash_parent], budget, "parent_first").chunks == [
        cash_parent
    ]


def test_oversize_parent_keeps_complete_code_child_and_ample_budget_deduplicates():
    text = '```python\r\nprint("café")\r\n```\r\n'
    child = region("a:child:0", text, "a:parent:0", ["a:child:0"])
    parent = region(
        "a:parent:0", text + "Surrounding material. " * 50, "a:parent:0", child.matched_child_ids
    )
    small = pack([child], [parent], tokens([child]))
    assert small.chunks == [child]
    assert small.chunks[0].chunk.text == text
    assert small.diagnostics.excluded == []
    large = pack([child], [parent], tokens([parent]))
    assert large.chunks == [parent]
    assert large.diagnostics.unexpanded_parents == []
    empty = pack([child], [parent], 1)
    assert empty.chunks == []
    assert empty.diagnostics.excluded[0].chunk_id == child.chunk.chunk_id
    assert empty.diagnostics.excluded[0].trial_context_tokens == tokens([child])
    assert small.diagnostics.unexpanded_parents[0].trial_context_tokens == tokens([parent])


def test_exclusion_records_the_entire_attempted_context_and_old_snapshots_remain_readable():
    first = region("first", "A retained fact.")
    second = region("second", "Another fact.")
    result = pack([first, second], [first, second], tokens([first, second]) - 1)
    omitted = result.diagnostics.excluded[0]
    assert omitted.chunk_id == "second"
    assert omitted.trial_context_tokens == tokens([first, second]) > result.diagnostics.max_tokens
    assert omitted.token_count == len(
        tiktoken.get_encoding("cl100k_base").encode_ordinary(second.chunk.text)
    )
    old = omitted.model_dump(exclude={"trial_context_tokens"})
    assert ExcludedEvidence.model_validate(old).trial_context_tokens is None


def test_table_parent_upgrade_replaces_all_siblings_without_displacing_other_sources():
    from knowledgebase.schemas import PdfEvidence, PdfRegion, PdfTableSpan

    first = region("table:child:0", "First table row.\n", "table:parent:0", ["table:child:0"])
    second = region(
        "table:child:1",
        "Second table row.\n",
        "table:parent:0",
        ["table:child:1"],
        len(first.chunk.text),
    )
    parent = region(
        "table:parent:0",
        first.chunk.text + second.chunk.text + "Table detail. " * 30,
        first.parent_id,
        [first.chunk.chunk_id, second.chunk.chunk_id],
    )
    cells = [
        (row, row + 1, 0, 1, hit.chunk.start_offset, hit.chunk.end_offset)
        for row, hit in enumerate([first, second])
    ]
    for hit, selected_cells in [(first, cells[:1]), (second, cells[1:]), (parent, cells)]:
        hit.pdf = PdfEvidence(
            revision_id="revision",
            source_hash="source",
            page_count=1,
            regions=[
                PdfRegion(
                    start_offset=hit.chunk.start_offset,
                    end_offset=hit.chunk.end_offset,
                    page_index=0,
                    bbox=(0, 0, 100, 100),
                    precision="table",
                )
            ],
            tables=[PdfTableSpan(table_id="table", cells=selected_cells)],
        )
    unrelated = region("other", "Another document fact.")
    selected = [first, unrelated, second]
    expanded = [parent, unrelated]
    budget = tokens([parent, unrelated])
    assert tokens(selected) < budget

    upgraded = pack(selected, expanded, budget)
    assert upgraded.chunks == [parent, unrelated]
    assert upgraded.diagnostics.evidence_tokens == budget
    assert upgraded.diagnostics.excluded == upgraded.diagnostics.unexpanded_parents == []

    retained = pack(selected, expanded, budget - 1)
    assert retained.chunks == selected
    assert retained.diagnostics.excluded == []
    assert retained.diagnostics.unexpanded_parents[0].chunk_id == parent.chunk.chunk_id
    assert retained.diagnostics.unexpanded_parents[0].trial_context_tokens == budget


def test_source_identity_is_in_budget_and_historical_format_is_unknown():
    child = region("flat", "A complete fact.")
    text_only = len(
        tiktoken.get_encoding("cl100k_base").encode_ordinary("[1]\n" + child.chunk.text)
    )
    assert pack([child], [child], text_only).chunks == []
    result = pack([child], [child], tokens([child]))
    assert result.chunks == [child]
    assert result.diagnostics.evidence_tokens == tokens([child])
    assert result.diagnostics.context_format == "source-metadata-v1"
    old = result.diagnostics.model_dump(exclude={"context_format"})
    assert RetrievalDiagnostics.model_validate(old).context_format is None


@pytest.mark.parametrize("streaming", [False, True])
def test_api_retained_child_offsets_provenance_and_history_survive_delete(
    configured_app, monkeypatch, streaming
):
    app, _, sdk = configured_app
    sdk.responses.create.return_value.output_text = "Internships after the first year. [1]"

    async def stream(messages):
        yield "Internships after the first year. [1]"

    from unittest.mock import Mock

    monkeypatch.setattr(bootstrap, "StreamingLLMClient", Mock(return_value=Mock(stream=stream)))
    text = "# Timing\n\nInternships after the first year.\n\n" + "Unrelated context. " * 80
    with TestClient(app) as client:
        resources = app.state.resources
        resources.files.chunker.chunk_max_tokens = 16
        file_id = client.post("/api/files", files={"file": ("timing.md", text.encode())}).json()[
            "file_id"
        ]
        with resources.sessions() as session:
            child = next(c for c in get_chunks(session, file_id) if "Internships" in c.text)
        resources.retriever.options.strategy = "vector"
        resources.retriever.top_k = 1
        resources.retriever.evidence_max_tokens = tokens(
            [
                RetrievedChunk(chunk=child, file_name="timing.md", distance=0.2),
            ]
        )
        resources.store.search = Mock(
            return_value=[VectorMatch(chunk_id=child.chunk_id, distance=0.2)]
        )
        response = client.post(
            "/api/chat/stream" if streaming else "/api/chat",
            json={
                "question": "Internship timing?",
                "request_id": "packing-test",
            },
        )
        assert response.status_code == 200
        result = (
            json.loads(response.text.strip().split("\n\n")[-1].split("\ndata: ")[1])
            if streaming
            else response.json()
        )
        source = result["sources"][0]
        assert source["chunk_id"] == child.chunk_id != source["parent_id"]
        assert source["text"] == text[source["start_offset"] : source["end_offset"]] == child.text
        assert source["matched_child_ids"] == [child.chunk_id]
        assert source["distance"] == 0.2
        assert result["retrieval"]["excluded"] == []
        assert result["retrieval"]["unexpanded_parents"][0]["chunk_id"] == child.parent_id
        assert result["retrieval"]["options"]["packing_strategy"] == "parent_then_child"
    with TestClient(api_module.create_app()) as client:
        assert client.delete(f"/api/files/{file_id}").status_code == 204
        saved = client.get(f"/api/conversations/{result['conversation_id']}").json()["messages"][-1]
        assert saved["sources"] == [{**source, "file_deleted": True}]
        assert saved["retrieval"] == result["retrieval"]
