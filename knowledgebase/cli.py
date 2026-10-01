"""Index TXT/Markdown files and ask questions in an interactive terminal loop."""

import argparse
from collections.abc import Callable
from pathlib import Path

from openai import OpenAI

from knowledgebase.config import Settings
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.schemas import ChatAnswer, ConversationAnswer
from knowledgebase.services.chat import answer_in_conversation
from knowledgebase.services.files import FileService
from knowledgebase.storage.runtime import open_storage
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.rag.pdf_runtime import LocalPdfParser


def run_chat_loop(ask: Callable[[str], ChatAnswer]) -> None:
    """Read questions and display answers with retrieved excerpts."""
    print("KnowledgeBase — ask a question, or type exit / quit to leave.")
    while True:
        try:
            question = input("\nQuestion> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return
        if question.strip().lower() in {"exit", "quit"}:
            print("Goodbye.")
            return
        if not question.strip():
            continue

        result = ask(question)
        if isinstance(result, ConversationAnswer):
            print(f"\nConversation: {result.conversation_id}")
            if result.retrieval_question != question:
                print(f"Retrieval question: {result.retrieval_question}")
        print(f"\nAnswer:\n{result.answer}")
        check = result.citation_check
        if check.no_citations:
            print("\nCitation check: no numbered citations found.")
        else:
            print(f"\nCitation check — valid source IDs: {check.valid_source_ids}; invalid source IDs: {check.invalid_source_ids}")
        print("\nRetrieved chunks:")
        if not result.sources:
            print("None.")
        for source in result.sources:
            print(f"\n[{source.source_id}] {source.file_name}")
            print(f"Chunk ID: {source.chunk_id}")
            print(source.text)


def cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path, help="TXT/Markdown files to index before chatting")
    parser.add_argument("--data-dir", type=Path, help="Override the DATA_DIR local storage directory")
    parser.add_argument("--model", default=None, help="Override the configured answer model")
    parser.add_argument("--top-k", type=int, help="Maximum retrieved chunks per question")
    parser.add_argument("--rerank", action=argparse.BooleanOptionalAction, default=None, help="Override RERANK_ENABLED")
    parser.add_argument("--rerank-model", help="Override RERANK_MODEL")
    parser.add_argument("--evidence-packing-strategy", choices=["parent_then_child", "parent_first"])
    parser.add_argument("--conversation-id", help="Resume a saved conversation in this data directory")
    parser.add_argument("--retrieval-mode", choices=["single", "planned"], help="Use one search or an bounded automatic query plan")
    args = parser.parse_args()
    overrides = {}
    if args.retrieval_mode is not None:
        overrides["retrieval_mode"] = args.retrieval_mode
    if args.model is not None:
        overrides["answer_model"] = args.model
    if args.top_k is not None:
        overrides["retrieval_top_k"] = args.top_k
    if args.rerank is not None:
        overrides["rerank_enabled"] = args.rerank
    if args.rerank_model is not None:
        overrides["rerank_model"] = args.rerank_model
    if args.evidence_packing_strategy is not None:
        overrides["evidence_packing_strategy"] = args.evidence_packing_strategy
    settings = Settings(**overrides)
    args.data_dir = args.data_dir if args.data_dir is not None else settings.data_dir

    with open_storage(args.data_dir) as (sessions, store):
        with OpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds, max_retries=settings.openai_max_retries,
        ) as sdk:
            embeddings = EmbeddingClient(sdk, model=settings.embedding_model)
            llm = LLMClient(sdk, model=settings.answer_model, reasoning_effort=settings.answer_reasoning_effort)
            reranker = RerankerClient(
                settings.rerank_model, device=settings.rerank_device,
                batch_size=settings.rerank_batch_size, max_pair_tokens=settings.rerank_max_pair_tokens,
            ) if settings.rerank_enabled else None
            resolver = LLMClient(sdk, model=settings.resolver_model) if settings.resolver_model else None
            pdf_parser = LocalPdfParser(settings.pdf_model_dir)
            planner = PlannerClient(sdk, settings.planner_model or settings.answer_model,
                                    settings.planning, settings.chunk_tokenizer)
            files = FileService.from_settings(settings, sessions, embeddings, store,
                                              assets=PdfAssets(args.data_dir), pdf_parser=pdf_parser)
            for path in args.files:
                file_id = files.ingest(path.name, path.read_bytes())
                print(f"Indexed {path.name} ({file_id})")
            conversation_id = args.conversation_id

            def ask(question: str) -> ConversationAnswer:
                nonlocal conversation_id
                result = answer_in_conversation(
                    question, sessions, embeddings, store, llm,
                    conversation_id=conversation_id, top_k=settings.retrieval_top_k,
                    history_limit=settings.history_limit, resolver_client=resolver,
                    evidence_max_tokens=settings.evidence_max_tokens, encoding_name=settings.chunk_tokenizer,
                    retrieval_options=settings.retrieval_options, reranker_client=reranker,
                    **({"planner_client": planner, "planning_options": settings.planning}
                       if settings.retrieval_mode == "planned" else {}),
                )
                conversation_id = result.conversation_id
                return result

            run_chat_loop(ask)


if __name__ == "__main__":
    cli()
