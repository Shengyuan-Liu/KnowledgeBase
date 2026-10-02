"""Exercise independent requests through the same service and provider components."""

from unittest.mock import Mock

import anyio
import pytest

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.retrieval import Retriever
from knowledgebase.services.chat import ChatService
from knowledgebase.services.files import FileService
from knowledgebase.rag.client import RagClient


@pytest.mark.anyio
async def test_overlapping_streams_keep_evidence_answers_and_histories_separate(
    storage, embeddings
):
    sessions, store, _ = storage
    files = FileService(sessions, store, embeddings=embeddings)
    first = files.ingest("alpha.txt", b"Alpha closes at five.")
    second = files.ingest("beta.txt", b"Beta closes at six.")
    started = []
    both_started = anyio.Event()

    class Streamer:
        async def stream(self, messages):
            name = "Alpha" if "alpha.txt" in messages[0]["content"] else "Beta"
            started.append(name)
            if len(started) == 2:
                both_started.set()
            yield name
            await both_started.wait()
            yield " answer. [1]"

    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "Third answer. [1]"
    rag = RagClient(sessions, Retriever(embeddings, store), llm, Streamer())
    chat = ChatService(sessions, rag)
    answers = {}

    async def ask(name, file_id):
        stream = await chat.stream(f"{name} hours?", name, file_ids=[file_id])
        answers[name] = [event async for event in stream]

    with anyio.fail_after(5):
        async with anyio.create_task_group() as tasks:
            tasks.start_soon(ask, "Alpha", first)
            tasks.start_soon(ask, "Beta", second)
    conversations = set()
    for name, file_id in (("Alpha", first), ("Beta", second)):
        events = answers[name]
        assert all(event.request_id == name for event in events)
        assert events[-1].event == "complete"
        saved = events[-1].data
        assert saved["answer"] == f"{name} answer. [1]"
        assert {source["file_id"] for source in saved["sources"]} == {file_id}
        history = chat.get_conversation(saved["conversation_id"])
        assert [message.content for message in history.messages] == [
            f"{name} hours?",
            saved["answer"],
        ]
        conversations.add(saved["conversation_id"])
    assert len(conversations) == 2
    third = chat.answer("Third question", file_ids=[first])
    assert third.answer == "Third answer. [1]"
    assert third.conversation_id not in conversations
    assert {source.file_id for source in third.sources} == {first}


def test_request_deadline_and_cancellation_do_not_modify_shared_clients(storage):
    sessions, store, _ = storage
    embeddings = EmbeddingClient(Mock(), "offline")
    llm = LLMClient(Mock(), "offline")
    retriever = Retriever(embeddings, store)
    rag = RagClient(sessions, retriever, llm, planner=Mock(), retrieval_mode="planned")
    first, second = rag.request_control(), rag.request_control()
    bounded = retriever.bounded(first.before_answer)
    first.cancelled.set()
    with pytest.raises(TimeoutError, match="cancelled"):
        bounded.embeddings._remaining()
    assert second.before_answer() > 0
    assert retriever.embeddings is embeddings
    assert embeddings._remaining is None
    assert llm._limits is None
