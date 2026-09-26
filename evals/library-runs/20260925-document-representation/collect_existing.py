"""Collect unchanged service questions against a verified copy of the frozen index."""
from types import SimpleNamespace
from time import perf_counter
from evals import metrics
from evals.automatic import RecordedEmbeddings,RecordedResponses,identifier
from evals.evaluate import append_jsonl,write_json,retrieval_metrics
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient,StreamingLLMClient
from knowledgebase.services.chat import stream_answer_in_conversation

async def collect_existing(settings,directory,metadata,cases,sessions,store,chunks,sdk,async_sdk,calls):
    embeddings_api=RecordedEmbeddings(sdk,calls)
    embeddings=EmbeddingClient(SimpleNamespace(embeddings=embeddings_api),settings.embedding_model)
    response_api=RecordedResponses(async_sdk,calls)
    streaming=StreamingLLMClient(SimpleNamespace(responses=response_api),settings.answer_model,reasoning_effort=settings.answer_reasoning_effort)
    llm=LLMClient(sdk,settings.answer_model,reasoning_effort=settings.answer_reasoning_effort)
    assert not settings.rerank_enabled
    reranker=None
    batch = perf_counter()
    for case in cases:
        embeddings_api.stage, embeddings_api.case_id = "query_embedding", case["id"]
        response_api.case_id = case["id"]
        call_start = len(calls)
        row = {"case_id": case["id"], "question": case["question"], "status": "error",
               "events": [], "answer": "", "sources": [], "first_delta_seconds": None}
        start = perf_counter()
        try:
            stream = await stream_answer_in_conversation(case["question"], identifier(), sessions,
                embeddings, store, llm, streaming, top_k=settings.retrieval_top_k,
                evidence_max_tokens=settings.evidence_max_tokens, encoding_name=settings.chunk_tokenizer,
                retrieval_options=settings.retrieval_options, reranker_client=reranker)
            async for event in stream:
                elapsed = perf_counter() - start
                row["events"].append({"seconds": elapsed, **event.model_dump(mode="json")})
                if event.event == "sources":
                    row["sources"] = event.data["sources"]
                    row["retrieval_seconds"] = elapsed
                elif event.event == "answer_delta":
                    row["answer"] += event.data["delta"]
                    if event.data["delta"] and row["first_delta_seconds"] is None:
                        row["first_delta_seconds"] = elapsed
                elif event.event == "complete":
                    row.update(event.data)
                    row["status"] = "ok"
                elif event.event == "error":
                    row["error_type"] = "ServiceStreamError"
        except Exception as error:
            row["error_type"] = type(error).__name__
        row["total_seconds"] = perf_counter() - start
        observed = calls[call_start:]
        for call in observed:
            append_jsonl(directory / "calls.jsonl", call)
        row["embedding_seconds"] = sum(c["seconds"] for c in observed if c["stage"] == "query_embedding") if any(c["stage"] == "query_embedding" for c in observed) else None
        generated = next((c for c in observed if c["stage"] == "generation"), {})
        row["generation_seconds"] = generated.get("seconds")
        row["generation_first_delta_seconds"] = next((d["seconds"] for d in generated.get("deltas", []) if d["delta"]), None)
        if row["status"] == "ok":
            row["coverage"] = retrieval_metrics(case, row["sources"])
            row["ranking"] = metrics.ranking(case, row["retrieval"]["candidates"], chunks, settings.retrieval_top_k)
            for field in ("rerank_seconds", "packing_seconds", "scope_seconds"):
                row[field] = row["retrieval"][field]
        else:
            errors = [c.get("error_type") for c in observed if c.get("error_type")]
            if errors:
                row["error_type"] = errors[-1]
        append_jsonl(directory / "answers.jsonl", row)
        print(f"RAG {case['id']}: {row['status']}, {row['total_seconds']:.2f}s", flush=True)
    metadata["rag_wall_seconds"] = perf_counter() - batch
    write_json(directory / "run.json", metadata)
