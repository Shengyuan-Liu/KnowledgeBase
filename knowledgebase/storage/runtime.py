"""Open the shared local storage used by the API and CLI."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import chromadb
from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.storage.database import build_engine, build_session_factory, init_db
from knowledgebase.storage.vectordb import ChromaStore


@contextmanager
def open_storage(data_dir: Path) -> Iterator[tuple[sessionmaker[Session], ChromaStore]]:
    directory = data_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    engine = build_engine(f"sqlite:///{directory / 'knowledgebase.db'}")
    try:
        init_db(engine)
        collection = chromadb.PersistentClient(path=str(directory / "chroma")).get_or_create_collection(
            name="knowledgebase-chunks", embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
        )
        yield build_session_factory(engine), ChromaStore(collection)
    finally:
        engine.dispose()
