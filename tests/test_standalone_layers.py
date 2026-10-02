"""Run public components in fresh processes with upper-layer imports blocked."""

import os
from pathlib import Path
import subprocess
import sys
from textwrap import dedent

import pytest

ROOT = Path(__file__).resolve().parents[1]

PRELUDE = """
import importlib.abc
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

class UpperLayerBlocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == prefix or fullname.startswith(prefix + '.') for prefix in BLOCKED):
            raise AssertionError('Unexpected upper-layer import: ' + fullname)

sys.meta_path.insert(0, UpperLayerBlocker())
"""

PROVIDER_SETUP = """
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient

sdk = Mock()
sdk.embeddings.create.side_effect = lambda **kwargs: SimpleNamespace(
    data=[SimpleNamespace(embedding=[1.0, 0.0]) for text in kwargs['input']]
)
sdk.responses.create.return_value = SimpleNamespace(output_text='Alpha closes at five. [1]')
embeddings = EmbeddingClient(sdk, model='offline-embedding')
llm = LLMClient(sdk, model='offline-answer')
"""

STORAGE_SETUP = """
from knowledgebase.schemas import Chunk
from knowledgebase.storage.operations import (
    create_file, delete_chunks, delete_file_record, get_file, save_chunks, update_file_status,
)
from knowledgebase.storage.runtime import open_storage
"""

CASES = {
    "contracts": (
        [
            "knowledgebase.providers",
            "knowledgebase.storage",
            "knowledgebase.rag",
            "knowledgebase.services",
            "pydantic_settings",
        ],
        """
        from knowledgebase.defaults import DEFAULT_TOP_K
        from knowledgebase.schemas import Chunk
        from knowledgebase.schemas.options import PlanningOptions, RetrievalOptions
        assert DEFAULT_TOP_K > 0
        assert RetrievalOptions().strategy == 'hybrid'
        assert PlanningOptions().max_rounds == 3
        assert Chunk(chunk_id='a', file_id='f', text='Alpha', index=0, start_offset=0, end_offset=5).text == 'Alpha'
        """,
    ),
    "providers": (
        ["knowledgebase.storage", "knowledgebase.rag", "knowledgebase.services"],
        PROVIDER_SETUP
        + """
assert embeddings.embed_query('Alpha hours?') == [1.0, 0.0]
assert llm.generate([{'role': 'user', 'content': 'Alpha hours?'}]) == 'Alpha closes at five. [1]'
assert sdk.responses.create.call_args.kwargs['model'] == 'offline-answer'
""",
    ),
    "parsing_chunking_reranking": (
        ["knowledgebase.storage", "knowledgebase.services", "docling", "torch"],
        PROVIDER_SETUP
        + r"""
from knowledgebase.rag.document_chunker import DocumentChunker
from knowledgebase.rag.parsing import DocumentParser
from knowledgebase.rag.reranking import Reranker
from knowledgebase.schemas import RelevanceScore, RerankCandidate

content = b'# Hours\n\nAlpha closes at five. Beta closes at six.\n'
parser = DocumentParser()
file = parser.parse(parser.prepare('hours.md', content), content)
for strategy in ('character', 'structural', 'parent_child', 'semantic'):
    batch, indexing = DocumentChunker(chunking_strategy=strategy, embeddings=embeddings).split(file)
    assert indexing['strategy'] == strategy
    assert batch.children
    assert all(chunk.text == file.text[chunk.start_offset:chunk.end_offset] for chunk in batch.children)

scorer = Mock(model='offline-reranker', model_revision='fixed', device='cpu', max_pair_tokens=1024, batch_size=4)
scorer.score.return_value = [RelevanceScore(chunk_id='a', score=1), RelevanceScore(chunk_id='b', score=2)]
candidates = [RerankCandidate(chunk_id=key, rank=i, rrf_score=1/(60+i), text=text)
              for i, (key, text) in enumerate([('a', 'Beta hours'), ('b', 'Alpha closes at five')], 1)]
ranked = Reranker(scorer).rerank('Alpha hours?', candidates, top_k=1)
assert [hit.chunk_id for hit in ranked.selected] == ['b']
""",
    ),
    "storage": (
        ["knowledgebase.providers", "knowledgebase.rag", "knowledgebase.services"],
        STORAGE_SETUP
        + """
chunk = Chunk(chunk_id='f:0', file_id='f', text='Alpha closes at five.', index=0,
              start_offset=0, end_offset=len('Alpha closes at five.'))
with open_storage(Path('data')) as (sessions, store):
    with sessions.begin() as session:
        create_file(session, 'f', 'hours.txt')
        save_chunks(session, [chunk])
        update_file_status(session, 'f', 'ready')
    store.upsert_chunks([chunk], [[1.0, 0.0]])
    assert store.search([1.0, 0.0], top_k=1)[0].chunk_id == 'f:0'
with open_storage(Path('data')) as (sessions, store):
    with sessions() as session:
        assert get_file(session, 'f').status == 'ready'
    store.delete_by_file_id('f')
    with sessions.begin() as session:
        delete_chunks(session, 'f')
        delete_file_record(session, 'f')
    assert store.search([1.0, 0.0], top_k=1) == []
""",
    ),
    "rag_engine": (
        ["knowledgebase.services"],
        PROVIDER_SETUP
        + STORAGE_SETUP
        + """
from knowledgebase.rag.client import RagClient
from knowledgebase.rag.retrieval import Retriever

with open_storage(Path('data')) as (sessions, store):
    chunk = Chunk(chunk_id='f:0', file_id='f', text='Alpha closes at five.', index=0,
                  start_offset=0, end_offset=len('Alpha closes at five.'))
    with sessions.begin() as session:
        create_file(session, 'f', 'hours.txt')
        save_chunks(session, [chunk])
        update_file_status(session, 'f', 'ready')
    store.upsert_chunks([chunk], embeddings.embed_documents([chunk.text]))
    retriever = Retriever(embeddings, store)
    with sessions() as session:
        evidence = retriever.retrieve('When does Alpha close?', session, file_ids=['f'])
        assert evidence.chunks and evidence.chunks[0].chunk.file_id == 'f'
    answer = RagClient(sessions, retriever, llm).answer('When does Alpha close?', file_ids=['f'])
    assert answer.answer == 'Alpha closes at five. [1]'
    assert answer.sources[0].file_id == 'f'
    assert answer.citation_check.valid_source_ids == [1]
""",
    ),
    "application_services": (
        [],
        PROVIDER_SETUP
        + STORAGE_SETUP
        + """
from knowledgebase.rag.client import RagClient
from knowledgebase.rag.retrieval import Retriever
from knowledgebase.services.chat import ChatService
from knowledgebase.services.files import FileService

with open_storage(Path('data')) as (sessions, store):
    files = FileService(sessions, store, embeddings=embeddings)
    file_id = files.ingest('hours.txt', b'Alpha closes at five.')
    rag = RagClient(sessions, Retriever(embeddings, store), llm)
    chat = ChatService(sessions, rag)
    answer = chat.answer('When does Alpha close?', file_ids=[file_id])
    assert answer.answer == 'Alpha closes at five. [1]'
    assert answer.sources[0].file_id == file_id
    assert len(chat.get_conversation(answer.conversation_id).messages) == 2
    files.delete(file_id)
    assert files.list_files() == []
""",
    ),
}


@pytest.mark.parametrize("case", CASES)
def test_component_runs_without_upper_layers(case, tmp_path):
    extra_blocked, program = CASES[case]
    blocked = [
        "knowledgebase.api",
        "knowledgebase.cli",
        "knowledgebase.bootstrap",
        "knowledgebase.config",
        *extra_blocked,
    ]
    code = f"BLOCKED = {blocked!r}\n" + dedent(PRELUDE) + dedent(program)
    code += "\nassert not any(name == p or name.startswith(p + '.') for p in BLOCKED for name in sys.modules)\n"
    # A fresh process avoids imports cached by pytest/conftest and has no local .env.
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("OPENAI_")
    }
    env["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
