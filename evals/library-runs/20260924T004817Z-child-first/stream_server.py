"""Isolated paired harness using the production streaming service and HTTP framing."""

from pathlib import Path
from typing import Literal

from knowledgebase.api.app import create_app
from knowledgebase.api.dependencies import Resources
from knowledgebase.api.streaming import ChatStreamingResponse
from knowledgebase.schemas import StreamChatRequest
from knowledgebase.services.chat import stream_answer_in_conversation
from knowledgebase.storage.operations import get_chunks, get_files, get_parents

app = create_app(frontend_dir=Path(__file__).parent / 'no-frontend')


@app.get('/benchmark/info')
def info(resources: Resources):
    settings = resources.settings
    with resources.sessions() as session:
        files = [{'file': f.model_dump(mode='json'),
                  'chunks': [c.model_dump() for c in get_chunks(session, f.file_id)],
                  'parents': [p.model_dump() for p in get_parents(session, f.file_id)]}
                 for f in get_files(session)]
    return {'snapshot': files, 'model': resources.reranker.model,
            'revision': resources.reranker.model_revision, 'device': resources.reranker.device,
            'batch_size': resources.reranker.batch_size, 'max_pair_tokens': resources.reranker.max_pair_tokens,
            'answer_model': settings.answer_model, 'embedding_model': settings.embedding_model,
            'top_k': settings.retrieval_top_k, 'evidence_max_tokens': settings.evidence_max_tokens,
            'retrieval_options': settings.retrieval_options.model_dump()}


@app.post('/benchmark/{strategy}')
async def compare(strategy: Literal['parent_first', 'parent_then_child'], body: StreamChatRequest, resources: Resources):
    settings = resources.settings
    events = await stream_answer_in_conversation(
        body.question, body.request_id, resources.sessions, resources.embeddings,
        resources.store, resources.llm, resources.streaming_llm,
        top_k=settings.retrieval_top_k, evidence_max_tokens=settings.evidence_max_tokens,
        encoding_name=settings.chunk_tokenizer,
        retrieval_options=settings.retrieval_options.model_copy(update={'packing_strategy': strategy}),
        reranker_client=resources.reranker,
    )
    return ChatStreamingResponse(events)
