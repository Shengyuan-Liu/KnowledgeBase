import json
import subprocess
import sys
from pathlib import Path

import pytest

from knowledgebase.rag.chunking import split_text
from knowledgebase.storage.vectordb import ChromaStore


@pytest.fixture
def chunks():
    return split_text("First. Second.", "file-1", chunk_size=7, overlap=0) + split_text(
        "Third.", "file-2"
    )


def test_upsert_stores_vectors_and_file_ids(collection, chunks):
    embeddings = [[1.0, 0.0], [0.8, 0.6], [0.0, 1.0]]
    ChromaStore(collection).upsert_chunks(chunks, embeddings)

    result = collection.get(include=["embeddings", "metadatas", "documents"])
    rows = {
        chunk_id: (vector, metadata, document)
        for chunk_id, vector, metadata, document in zip(
            result["ids"], result["embeddings"], result["metadatas"], result["documents"]
        )
    }
    assert set(rows) == {chunk.chunk_id for chunk in chunks}
    for chunk, embedding in zip(chunks, embeddings):
        vector, metadata, document = rows[chunk.chunk_id]
        assert vector == pytest.approx(embedding)
        assert metadata == {"file_id": chunk.file_id}
        assert document is None


def test_search_returns_nearest_chunk_ids_and_cosine_distances(collection, chunks):
    store = ChromaStore(collection)
    store.upsert_chunks(chunks, [[1.0, 0.0], [0.8, 0.6], [0.0, 1.0]])

    matches = store.search([1.0, 0.0], top_k=2)

    assert [match.chunk_id for match in matches] == ["file-1:0", "file-1:1"]
    assert [match.distance for match in matches] == pytest.approx([0.0, 0.2])


def test_upsert_updates_existing_vector_without_duplicate(collection, chunks):
    store = ChromaStore(collection)
    store.upsert_chunks(chunks, [[1.0, 0.0], [0.8, 0.6], [0.0, 1.0]])

    store.upsert_chunks([chunks[0]], [[-1.0, 0.0]])

    assert collection.count() == 3
    assert collection.get(ids=[chunks[0].chunk_id], include=["embeddings"])[
        "embeddings"
    ][0] == pytest.approx([-1.0, 0.0])
    assert store.search([-1.0, 0.0], top_k=1)[0].chunk_id == chunks[0].chunk_id


@pytest.mark.parametrize(
    ("file_ids", "expected_ids"),
    [
        (["file-2"], ["file-2:0"]),
        (["file-1", "file-2"], ["file-1:0", "file-1:1"]),
    ],
)
def test_search_filters_files_before_selecting_nearest_results(
    collection, chunks, file_ids, expected_ids
):
    store = ChromaStore(collection)
    store.upsert_chunks(chunks, [[1.0, 0.0], [0.8, 0.6], [0.0, 1.0]])

    matches = store.search([1.0, 0.0], top_k=2, file_ids=file_ids)

    assert [match.chunk_id for match in matches] == expected_ids


def test_delete_removes_only_the_requested_file(collection, chunks):
    store = ChromaStore(collection)
    store.upsert_chunks(chunks, [[1.0, 0.0], [0.8, 0.6], [0.0, 1.0]])

    store.delete_by_file_id("file-1")

    assert collection.get()["ids"] == ["file-2:0"]
    assert store.search([0.0, 1.0], top_k=1)[0].chunk_id == "file-2:0"


def test_vectors_can_be_searched_from_another_process(collection, chunks, tmp_path):
    ChromaStore(collection).upsert_chunks([chunks[0]], [[1.0, 0.0]])

    result = subprocess.run(
        [sys.executable, "-", str(tmp_path / "chroma")],
        input="""
import json
import sys
import chromadb
from knowledgebase.storage.vectordb import ChromaStore

client = chromadb.PersistentClient(path=sys.argv[1])
collection = client.get_collection("test-chunks", embedding_function=None)
matches = ChromaStore(collection).search([1.0, 0.0], top_k=1)
print(json.dumps([match.model_dump() for match in matches]))
""",
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=True,
    )

    matches = json.loads(result.stdout)
    assert matches[0]["chunk_id"] == "file-1:0"
    assert matches[0]["distance"] == pytest.approx(0.0)
