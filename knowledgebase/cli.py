"""Index TXT/Markdown files and ask questions in an interactive terminal loop."""

import argparse
from collections.abc import Callable
from pathlib import Path

from openai import OpenAI

from knowledgebase.bootstrap import build_resources
from knowledgebase.config import Settings
from knowledgebase.schemas import ChatAnswer, ConversationAnswer
from knowledgebase.storage.runtime import open_storage


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
            print(
                f"\nCitation check — valid source IDs: {check.valid_source_ids}; invalid source IDs: {check.invalid_source_ids}"
            )
        print("\nRetrieved chunks:")
        if not result.sources:
            print("None.")
        for source in result.sources:
            print(f"\n[{source.source_id}] {source.file_name}")
            print(f"Chunk ID: {source.chunk_id}")
            print(source.text)


def cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files", nargs="*", type=Path, help="TXT/Markdown files to index before chatting"
    )
    parser.add_argument(
        "--data-dir", type=Path, help="Override the DATA_DIR local storage directory"
    )
    parser.add_argument("--model", default=None, help="Override the configured answer model")
    parser.add_argument("--top-k", type=int, help="Maximum retrieved chunks per question")
    parser.add_argument(
        "--rerank",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override RERANK_ENABLED",
    )
    parser.add_argument("--rerank-model", help="Override RERANK_MODEL")
    parser.add_argument(
        "--evidence-packing-strategy", choices=["parent_then_child", "parent_first"]
    )
    parser.add_argument(
        "--conversation-id", help="Resume a saved conversation in this data directory"
    )
    parser.add_argument(
        "--retrieval-mode",
        choices=["single", "planned"],
        help="Use one search or an bounded automatic query plan",
    )
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
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        ) as sdk:
            resources = build_resources(settings, sessions, store, sdk, data_dir=args.data_dir)
            for path in args.files:
                file_id = resources.files.ingest(path.name, path.read_bytes())
                print(f"Indexed {path.name} ({file_id})")
            conversation_id = args.conversation_id

            def ask(question: str) -> ConversationAnswer:
                nonlocal conversation_id
                result = resources.chat.answer(question, conversation_id=conversation_id)
                conversation_id = result.conversation_id
                return result

            run_chat_loop(ask)


if __name__ == "__main__":
    cli()
