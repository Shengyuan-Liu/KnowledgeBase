import json
from unittest.mock import Mock

import pytest
from sqlalchemy import event

from knowledgebase.config import RetrievalOptions
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.generation import INSUFFICIENT_EVIDENCE
from knowledgebase.schemas import ChatAnswer, CitationCheck, RetrievalDiagnostics
from knowledgebase.services.chat import answer_in_conversation, answer_question
from knowledgebase.services.files import delete_file, ingest_file
from knowledgebase.storage.operations import create_conversation, get_conversation, get_messages, save_message


def test_answer_loads_file_metadata_once(storage, embeddings, engine):
    sessions, store, _ = storage
    ingest_file("hours.txt", b"The library closes at 5 PM.", sessions, embeddings, store)
    file_queries = []

    @event.listens_for(engine, "before_cursor_execute")
    def record_query(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("SELECT") and "FROM files" in statement:
            file_queries.append(statement)

    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "5 PM. [1]"
    result = answer_question("Hours?", sessions, embeddings, store, llm)
    assert result.sources[0].file_name == "hours.txt"
    assert len(file_queries) == 1


@pytest.mark.parametrize("top_k", [2, 3])
def test_ingestion_to_answer_keeps_sources_aligned_with_prompt(storage, top_k):
    sessions, store, _ = storage
    embeddings = Mock(spec=EmbeddingClient)
    embeddings.embed_documents.side_effect = [
        [[0.6, 0.8], [0.8, 0.6]],
        [[1.0, 0.0]],
    ]
    embeddings.embed_query.return_value = [1.0, 0.0]
    first_id = ingest_file(
        "notes.txt", b"First. Second.", sessions, embeddings, store,
        chunk_size=7, overlap=0, chunking_strategy="character",
    )
    second_text = "  The café closes at 5 PM.\n"
    second_id = ingest_file(
        "hours.txt", second_text.encode("utf-8"), sessions, embeddings, store
    )
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "The café closes at 5 PM. [1]\n"
    question = "  When does the café close?\n"

    result = answer_question(question, sessions, embeddings, store, llm, top_k=top_k)

    assert isinstance(result, ChatAnswer)
    assert result.answer == "The café closes at 5 PM. [1]\n"
    assert result.citation_check == CitationCheck(valid_source_ids=[1], invalid_source_ids=[], no_citations=False)
    assert [source.source_id for source in result.sources] == list(range(1, top_k + 1))
    assert [source.file_id for source in result.sources] == [
        second_id, first_id, first_id
    ][:top_k]
    assert [source.file_name for source in result.sources] == [
        "hours.txt", "notes.txt", "notes.txt"
    ][:top_k]
    assert [source.chunk_id for source in result.sources] == [
        f"{second_id}:parent:0", f"{first_id}:1", f"{first_id}:0"
    ][:top_k]
    assert [source.text for source in result.sources] == [
        second_text, "Second.", "First. "
    ][:top_k]
    assert [source.distance for source in result.sources] == pytest.approx(
        [0.0, 0.2, 0.4][:top_k]
    )
    embeddings.embed_query.assert_called_once_with(question)
    llm.generate.assert_called_once()
    user_message = llm.generate.call_args.args[0][1]
    expected_context = ('[1]\nSource metadata: {"file_name": "hours.txt", "heading_path": []}\nExcerpt:\n'
                        '  The café closes at 5 PM.\n\n\n'
                        '[2]\nSource metadata: {"file_name": "notes.txt", "heading_path": []}\nExcerpt:\nSecond.')
    if top_k == 3:
        expected_context += '\n\n[3]\nSource metadata: {"file_name": "notes.txt", "heading_path": []}\nExcerpt:\nFirst. '
    assert user_message == {
        "role": "user",
        "content": f"Question:\n{question}\n\nSources:\n{expected_context}",
    }


def test_empty_knowledge_base_returns_no_sources_without_model_calls(storage):
    sessions, store, _ = storage
    embeddings = Mock(spec=EmbeddingClient)
    llm = Mock(spec=LLMClient)

    result = answer_question("When does the café close?", sessions, embeddings, store, llm)

    assert result == ChatAnswer(
        answer=INSUFFICIENT_EVIDENCE, sources=[],
        retrieval=RetrievalDiagnostics(max_tokens=4096, tokenizer="cl100k_base", options=RetrievalOptions(packing_strategy="parent_then_child"), top_k=5,
                                       retrieval_seconds=result.retrieval.retrieval_seconds),
        citation_check=CitationCheck(valid_source_ids=[], invalid_source_ids=[], no_citations=True),
    )
    embeddings.embed_query.assert_not_called()
    llm.generate.assert_not_called()


@pytest.fixture
def conversational_clients(storage):
    sessions, store, _ = storage
    embeddings = Mock(spec=EmbeddingClient)
    embeddings.embed_documents.side_effect = lambda texts: [[1.0, 0.0] for _ in texts]
    embeddings.embed_query.return_value = [1.0, 0.0]
    file_id = ingest_file("msds.txt", b"NYU MSDS is a master's program requiring 36 credits.", sessions, embeddings, store)
    return embeddings, Mock(spec=LLMClient), file_id


def test_followup_uses_resolved_question_and_saves_original_exchange(storage, conversational_clients):
    sessions, store, _ = storage
    embeddings, llm, file_id = conversational_clients
    llm.generate.side_effect = ["NYU MSDS is a master's program. [1]",
                                "How many credits does NYU MSDS require?", "It requires 36 credits. [1]"]
    first = answer_in_conversation("What is NYU MSDS?", sessions, embeddings, store, llm)
    assert first.retrieval_question == first.question == "What is NYU MSDS?"
    assert llm.generate.call_count == 1
    question = "  How many credits does it require?\n"
    second = answer_in_conversation(question, sessions, embeddings, store, llm, conversation_id=first.conversation_id)

    assert second.conversation_id == first.conversation_id
    assert second.message_id > first.message_id
    assert second.question == question
    assert second.retrieval_question == "How many credits does NYU MSDS require?"
    embeddings.embed_query.assert_called_with(second.retrieval_question)
    assert second.sources[0].file_id == file_id
    resolver_payload = json.loads(llm.generate.call_args_list[1].args[0][1]["content"])
    assert resolver_payload["history"] == [
        {"role": "user", "content": first.question}, {"role": "assistant", "content": first.answer}]
    generation = llm.generate.call_args_list[2].args[0][1]["content"]
    assert f"Question:\n{question}" in generation
    assert f"Conversation interpretation (not evidence):\n{second.retrieval_question}" in generation
    assert first.answer not in generation
    with sessions() as session:
        assert get_conversation(session, first.conversation_id) is not None
        messages = get_messages(session, first.conversation_id)
    assert [(m.role, m.content) for m in messages] == [
        ("user", first.question), ("assistant", first.answer), ("user", question), ("assistant", second.answer)]
    assert messages[-1].message_id == second.message_id


def test_only_current_conversation_recent_history_is_sent(storage, conversational_clients):
    sessions, store, _ = storage
    embeddings, llm, _ = conversational_clients
    with sessions.begin() as session:
        for conversation_id in ("one", "two"):
            create_conversation(session, conversation_id)
        save_message(session, "one", "user", "Old message outside the window.")
        save_message(session, "one", "assistant", "Another old message.")
        save_message(session, "one", "user", "What is NYU MSDS?")
        save_message(session, "one", "assistant", "A master's program.")
        save_message(session, "two", "user", "Private topic in another conversation.")
    llm.generate.side_effect = ["How many credits does NYU MSDS require?", "36 credits. [1]"]
    answer_in_conversation("How many credits?", sessions, embeddings, store, llm, conversation_id="one", history_limit=2)
    payload = json.loads(llm.generate.call_args_list[0].args[0][1]["content"])
    assert [m["content"] for m in payload["history"]] == ["What is NYU MSDS?", "A master's program."]
    with sessions() as session:
        assert [m.content for m in get_messages(session, "two")] == ["Private topic in another conversation."]


def test_followup_after_deletion_cannot_answer_from_saved_history(storage, conversational_clients):
    sessions, store, _ = storage
    embeddings, llm, file_id = conversational_clients
    llm.generate.return_value = "It requires 36 credits. [1]"
    first = answer_in_conversation("How many credits does NYU MSDS require?", sessions, embeddings, store, llm)
    delete_file(file_id, sessions, store)
    llm.reset_mock()
    embeddings.reset_mock()
    llm.generate.return_value = "How many credits does NYU MSDS require?"
    second = answer_in_conversation("How many was that?", sessions, embeddings, store, llm, conversation_id=first.conversation_id)
    assert second.answer == INSUFFICIENT_EVIDENCE
    assert second.sources == []
    llm.generate.assert_called_once()  # Reference resolution only, no answer call.
    embeddings.embed_query.assert_not_called()


def test_missing_conversation_rejected_without_calls_or_saved_messages(storage, conversational_clients):
    sessions, store, _ = storage
    embeddings, llm, _ = conversational_clients
    with pytest.raises(LookupError, match="missing"):
        answer_in_conversation("Question?", sessions, embeddings, store, llm, conversation_id="missing")
    llm.generate.assert_not_called()
    embeddings.embed_query.assert_not_called()
    with sessions() as session:
        assert get_messages(session, "missing") == []


@pytest.mark.parametrize("failure_stage", ["resolution", "generation", "saving"])
def test_failed_followup_leaves_previous_history_unchanged(storage, conversational_clients, monkeypatch, failure_stage):
    from knowledgebase.services import chat

    sessions, store, _ = storage
    embeddings, llm, _ = conversational_clients
    with sessions.begin() as session:
        create_conversation(session, "one")
        save_message(session, "one", "user", "What is NYU MSDS?")
        save_message(session, "one", "assistant", "A master's program.")
    failure = RuntimeError("Turn failed.")
    llm.generate.side_effect = ([failure] if failure_stage == "resolution" else
                                ["How many credits does NYU MSDS require?", failure if failure_stage == "generation" else "36 credits. [1]"])
    if failure_stage == "saving":
        def fail_assistant(session, conversation_id, role, content):
            if role == "assistant":
                raise failure
            return save_message(session, conversation_id, role, content)
        monkeypatch.setattr(chat, "save_message", fail_assistant)
    with pytest.raises(RuntimeError) as caught:
        answer_in_conversation("How many credits?", sessions, embeddings, store, llm, conversation_id="one")
    assert caught.value is failure
    with sessions() as session:
        assert [m.content for m in get_messages(session, "one")] == ["What is NYU MSDS?", "A master's program."]


def test_existing_empty_conversation_needs_no_resolution_call(storage):
    sessions, store, _ = storage
    with sessions.begin() as session:
        create_conversation(session, "empty")
    embeddings = Mock(spec=EmbeddingClient)
    llm = Mock(spec=LLMClient)
    result = answer_in_conversation("What is available?", sessions, embeddings, store, llm, conversation_id="empty")
    assert result.conversation_id == "empty"
    assert result.retrieval_question == "What is available?"
    assert result.answer == INSUFFICIENT_EVIDENCE
    llm.generate.assert_not_called()


def test_invalid_citations_are_reported_and_original_conversation_answer_is_saved(storage, conversational_clients):
    sessions, store, _ = storage
    embeddings, llm, _ = conversational_clients
    text = "  It requires 36 credits. [1] An unsupported claim. [5]\n"
    llm.generate.return_value = text
    result = answer_in_conversation("How many credits?", sessions, embeddings, store, llm)
    assert result.answer == text
    assert result.citation_check == CitationCheck(valid_source_ids=[1], invalid_source_ids=[5], no_citations=False)
    assert [source.source_id for source in result.sources] == [1]
    llm.generate.assert_called_once()
    with sessions() as session:
        assert get_messages(session, result.conversation_id)[-1].content == text


def test_resolver_answer_cannot_replace_the_original_question(storage, conversational_clients):
    sessions, store, _ = storage
    embeddings, llm, _ = conversational_clients
    llm.generate.return_value = "A master's program. [1]"
    first = answer_in_conversation("What is NYU MSDS?", sessions, embeddings, store, llm)
    question = "Which courses can be waived, and what materials are required?"
    bad_rewrite = "There is no information about course waivers."
    llm.generate.side_effect = [bad_rewrite, "The sources do not describe waivers."]
    answer_in_conversation(question, sessions, embeddings, store, llm,
                           conversation_id=first.conversation_id)
    prompt = llm.generate.call_args.args[0]
    assert prompt[1]["content"].startswith(f"Question:\n{question}\n")
    assert f"Conversation interpretation (not evidence):\n{bad_rewrite}" in prompt[1]["content"]
    assert "original question defines what to answer" in prompt[0]["content"]
