"""Index TXT files and ask questions in an interactive terminal loop."""

import argparse
from collections.abc import Callable
from pathlib import Path

from openai import OpenAI

from knowledgebase.config import Settings
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient
from knowledgebase.schemas import ChatAnswer, ConversationAnswer
from knowledgebase.services.chat import answer_in_conversation
from knowledgebase.services.files import ingest_file
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
    parser.add_argument("files", nargs="*", type=Path, help="TXT files to index before chatting")
    parser.add_argument("--data-dir", type=Path, help="Override the DATA_DIR local storage directory")
    parser.add_argument("--model", default="gpt-4.1-nano", help="OpenAI answer model")
    parser.add_argument("--top-k", type=int, default=5, help="Maximum retrieved chunks per question")
    parser.add_argument("--conversation-id", help="Resume a saved conversation in this data directory")
    args = parser.parse_args()
    settings = Settings()
    args.data_dir = args.data_dir if args.data_dir is not None else settings.data_dir

    with open_storage(args.data_dir) as (sessions, store):
        with OpenAI(api_key=settings.openai_api_key) as sdk:
            embeddings = EmbeddingClient(sdk)
            llm = LLMClient(sdk, model=args.model)
            for path in args.files:
                file_id = ingest_file(
                    path.name, path.read_bytes(), sessions, embeddings, store
                )
                print(f"Indexed {path.name} ({file_id})")
            conversation_id = args.conversation_id

            def ask(question: str) -> ConversationAnswer:
                nonlocal conversation_id
                result = answer_in_conversation(
                    question, sessions, embeddings, store, llm,
                    conversation_id=conversation_id, top_k=args.top_k,
                )
                conversation_id = result.conversation_id
                return result

            run_chat_loop(ask)


if __name__ == "__main__":
    cli()
