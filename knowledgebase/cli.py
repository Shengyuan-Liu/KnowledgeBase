"""Index TXT files and ask questions in an interactive terminal loop."""

import argparse
from collections.abc import Callable
from pathlib import Path

import chromadb
from openai import OpenAI

from knowledgebase.config import Settings
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient
from knowledgebase.schemas import ChatAnswer, ConversationAnswer
from knowledgebase.services.chat import answer_in_conversation
from knowledgebase.services.files import ingest_file
from knowledgebase.storage.database import build_engine, build_session_factory, init_db
from knowledgebase.storage.vectordb import ChromaStore


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
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Local storage directory")
    parser.add_argument("--model", default="gpt-4.1-nano", help="OpenAI answer model")
    parser.add_argument("--top-k", type=int, default=5, help="Maximum retrieved chunks per question")
    parser.add_argument("--conversation-id", help="Resume a saved conversation in this data directory")
    args = parser.parse_args()
    settings = Settings()

    args.data_dir.mkdir(parents=True, exist_ok=True)
    database_path = args.data_dir.resolve() / "knowledgebase.db"
    engine = build_engine(f"sqlite:///{database_path}")
    try:
        init_db(engine)
        sessions = build_session_factory(engine)
        chroma = chromadb.PersistentClient(path=str(args.data_dir / "chroma"))
        collection = chroma.get_or_create_collection(
            name="knowledgebase-chunks",
            embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
        )
        store = ChromaStore(collection)
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
    finally:
        engine.dispose()


if __name__ == "__main__":
    cli()
