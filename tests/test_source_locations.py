"""Source locations are based on canonical documents and survive file deletion."""

from unittest.mock import Mock

import pytest

from knowledgebase.rag.retrieval import Retriever
from knowledgebase.services.chat import ChatService
from knowledgebase.services.files import FileService
from knowledgebase.services.rag import RagClient
from knowledgebase.storage.operations import get_conversation_detail


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_exact_line_ranges_and_diagnostics_survive_restore_and_deletion(
    storage, embeddings, newline
):
    sessions, store, _ = storage
    text = newline.join(
        ["# First", "", "First sentence.", "", "# Second", "", "Last sentence.", ""]
    )
    file_id = FileService(sessions, store, embeddings=embeddings).ingest("guide.md", text.encode())
    llm = Mock()
    llm.generate.return_value = "First sentence. [1]"
    answer = ChatService(sessions, RagClient(sessions, Retriever(embeddings, store), llm)).answer(
        "First sentence?"
    )
    assert {s.text: (s.start_line, s.end_line) for s in answer.sources} == {
        newline.join(["# First", "", "First sentence.", ""]): (1, 3),
        text[text.index("# Second") :]: (5, 7),
    }
    assert answer.retrieval.retrieval_seconds >= answer.retrieval.embedding_seconds >= 0
    FileService(sessions, store).delete(file_id)
    with sessions() as session:
        saved = get_conversation_detail(session, answer.conversation_id).messages[-1]
    assert saved.retrieval == answer.retrieval
    assert [(s.start_line, s.end_line) for s in saved.sources] == [
        (s.start_line, s.end_line) for s in answer.sources
    ]
    assert all(s.file_deleted for s in saved.sources)
