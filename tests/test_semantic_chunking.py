"""Fixed-vector boundary decisions and the shared ingestion/storage contract."""

from unittest.mock import Mock

import pytest
import tiktoken
from sqlalchemy import select

from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.parsing import parse_markdown, parse_txt
from knowledgebase.rag.semantic_chunking import split_semantic
from knowledgebase.services.files import delete_file, ingest_file
from knowledgebase.storage.models import DocumentIndexRecord
from knowledgebase.storage.operations import get_chunks, get_document_source, get_files, get_parents


def split(text, vectors=None, threshold=0.5, child_budget=64, parent_budget=256, markdown=False):
    blocks = parse_markdown(text) if markdown else parse_txt(text)
    embed = Mock(side_effect=lambda texts: [[1., 0.] for _ in texts])
    if vectors is not None:
        embed.side_effect = None
        embed.return_value = vectors
    result, details = split_semantic(
        text, blocks, "file", embed, parent_max_tokens=parent_budget,
        child_max_tokens=child_budget, encoding_name="cl100k_base",
        similarity_threshold=threshold, batch_size=2 if vectors is None else 32,
    )
    control = split_parent_child(text, blocks, "file", parent_max_tokens=parent_budget,
                                 child_max_tokens=child_budget, encoding_name="cl100k_base")
    assert result.parents == control.parents
    encoding = tiktoken.get_encoding("cl100k_base")
    end = 0
    parents = {p.parent_id: p for p in result.parents}
    for index, child in enumerate(result.children):
        assert child.text == text[child.start_offset:child.end_offset]
        assert not text[end:child.start_offset].strip()
        assert child.token_count == len(encoding.encode_ordinary(child.text)) <= child_budget
        assert child.index == index
        parent = parents[child.parent_id]
        assert parent.start_offset <= child.start_offset < child.end_offset <= parent.end_offset
        assert child.heading_path == parent.heading_path
        assert child.source_block_indices == [i for i, b in enumerate(blocks)
            if b.start_offset < child.end_offset and b.end_offset > child.start_offset]
        end = child.end_offset
    assert not text[end:].strip()
    return result, details, embed, control


def test_topic_change_splits_but_similar_sentences_stay_together():
    text = "Cats sleep. Cats purr. Databases store records."
    result, trace, embed, _ = split(text, [[1, 0], [1, 0], [0, 1]])
    assert [c.text for c in result.children] == ["Cats sleep. Cats purr. ", "Databases store records."]
    assert [b["semantic_split"] for b in trace["boundaries"]] == [False, True]
    assert [b["cosine_similarity"] for b in trace["boundaries"]] == [1, 0]
    assert embed.call_args.args[0] == [text[a:b] for a, b in trace["input_spans"]]


def test_threshold_is_strict_and_cosine_is_normalized():
    result, trace, _, _ = split("First topic. Second topic.", [[2, 0], [0, 3]], threshold=0)
    assert len(result.children) == 1
    assert trace["boundaries"][0]["cosine_similarity"] == 0
    result, _, _, _ = split("First topic. Second topic.", [[2, 0], [0, 3]], threshold=.01)
    assert len(result.children) == 2


def test_embedding_batches_and_hard_budget_apply_even_without_topic_breaks():
    text = "".join(f"Sentence number {i} describes a step. " for i in range(12))
    result, trace, embed, _ = split(text, child_budget=18, parent_budget=48)
    assert len(result.parents) > 1
    assert len(result.children) > len(result.parents)
    assert all(len(c.args[0]) <= 2 for c in embed.call_args_list)
    assert trace["embedding_calls"] == embed.call_count
    assert not any(b["semantic_split"] for b in trace["boundaries"])


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_unicode_wrapped_prose_and_structural_blocks_preserve_source(newline):
    text = newline.join(["# Café", "", "A sentence wraps", "onto this line. Another follows.", "",
        "- First item.", "- Second item.", "", "```python", "print('hello')", "```", "",
        "| Key | Value |", "| --- | --- |", "| a | b |", "", "## Next", "", "One more sentence."])
    result, trace, embed, control = split(text, child_budget=16, parent_budget=48, markdown=True)
    inputs = [s for call in embed.call_args_list for s in call.args[0]]
    assert all("print(" not in s and "|" not in s and "- First" not in s for s in inputs)
    blocks = parse_markdown(text)
    for index, block in enumerate(blocks):
        if block.kind not in ("heading", "paragraph"):
            assert [c for c in result.children if index in c.source_block_indices] or not block.text.strip()
            assert [(c.start_offset, c.end_offset) for c in result.children if index in c.source_block_indices] == [
                (c.start_offset, c.end_offset) for c in control.children if index in c.source_block_indices]


@pytest.mark.parametrize("text", ["", " \n", "One sentence.", "```text\nCode only.\n```"])
def test_no_embedding_for_empty_single_sentence_or_code_only(text):
    _, trace, embed, _ = split(text, markdown=True)
    embed.assert_not_called()
    assert trace["embedding_calls"] == 0


def test_long_unbroken_units_use_existing_bounded_source_splits():
    split("café🙂" * 40, child_budget=8, parent_budget=24)


def test_semantic_upload_records_configuration_and_delete_cascades(storage, embeddings):
    sessions, store, collection = storage
    text = "Cats sleep. Cats purr. Databases store records."
    embeddings.embed_documents.side_effect = lambda texts: [
        [0., 1.] if "Databases" in value else [1., 0.] for value in texts]
    file_id = ingest_file("topics.txt", text.encode(), sessions, embeddings, store,
        chunking_strategy="semantic", chunk_max_tokens=64, parent_max_tokens=128,
        semantic_similarity_threshold=.25, semantic_batch_size=2, embedding_model="fixed-vectors")
    with sessions() as session:
        source = get_document_source(session, file_id)
        children = get_chunks(session, file_id)
        parents = get_parents(session, file_id)
        assert source.indexing["strategy"] == "semantic"
        assert source.indexing["embedding_model"] == "fixed-vectors"
        assert source.indexing["semantic"]["similarity_threshold"] == .25
        assert source.indexing["semantic"]["embedding_calls"] == 2
    assert len(parents) == 1 and len(children) == 2
    assert set(collection.get()["ids"]) == {c.chunk_id for c in children}
    assert embeddings.embed_documents.call_args.args[0] == [c.text for c in children]
    delete_file(file_id, sessions, store)
    with sessions() as session:
        assert session.scalars(select(DocumentIndexRecord)).all() == []
        assert get_document_source(session, file_id) is None


def test_semantic_embedding_failure_keeps_file_failed_and_library_clean(storage, embeddings):
    sessions, store, collection = storage
    embeddings.embed_documents.side_effect = RuntimeError("Observed provider failure")
    with pytest.raises(RuntimeError, match="provider failure"):
        ingest_file("topics.txt", b"Cats sleep. Databases store records.", sessions, embeddings, store,
                    chunking_strategy="semantic")
    with sessions() as session:
        file = get_files(session)[0]
        assert file.status == "failed"
        assert not get_chunks(session, file.file_id)
        assert get_document_source(session, file.file_id) is None
    assert collection.count() == 0
