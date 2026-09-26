"""Source locations are based on canonical documents and survive file deletion."""

from unittest.mock import Mock

import pytest

from knowledgebase.services.chat import answer_in_conversation
from knowledgebase.services.files import delete_file, ingest_file
from knowledgebase.storage.operations import get_conversation_detail


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_exact_line_ranges_and_diagnostics_survive_restore_and_deletion(storage, embeddings, newline):
    sessions, store, _ = storage
    text = newline.join(["# First", "", "First sentence.", "", "# Second", "", "Last sentence.", ""])
    file_id = ingest_file("guide.md", text.encode(), sessions, embeddings, store)
    llm = Mock()
    llm.generate.return_value = "First sentence. [1]"
    answer = answer_in_conversation("First sentence?", sessions, embeddings, store, llm)
    assert {s.text: (s.start_line, s.end_line) for s in answer.sources} == {
        newline.join(["# First", "", "First sentence.", ""]): (1, 3), text[text.index("# Second"):]: (5, 7),
    }
    assert answer.retrieval.retrieval_seconds >= answer.retrieval.embedding_seconds >= 0
    delete_file(file_id, sessions, store)
    with sessions() as session:
        saved = get_conversation_detail(session, answer.conversation_id).messages[-1]
    assert saved.retrieval == answer.retrieval
    assert [(s.start_line, s.end_line) for s in saved.sources] == [(s.start_line, s.end_line) for s in answer.sources]
    assert all(s.file_deleted for s in saved.sources)
