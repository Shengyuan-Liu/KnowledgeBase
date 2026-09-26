"""Open the shared local storage used by the API and CLI."""

from collections.abc import Iterator
from contextlib import contextmanager
import fcntl
from pathlib import Path

import chromadb
from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.services.files import recover_interrupted_files
from knowledgebase.storage.database import build_engine, build_session_factory, init_db
from knowledgebase.storage.vectordb import ChromaStore
from knowledgebase.storage.pdf_assets import PdfAssets


@contextmanager
def open_storage(data_dir: Path) -> Iterator[tuple[sessionmaker[Session], ChromaStore]]:
    directory = data_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    # Recovery must never mistake another live process's upload for a crash.
    with (directory / ".owner.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("This data directory is already in use. Stop its API or CLI process before reopening it.") from error
        engine = build_engine(f"sqlite:///{directory / 'knowledgebase.db'}")
        try:
            init_db(engine)
            collection = chromadb.PersistentClient(path=str(directory / "chroma")).get_or_create_collection(
                name="knowledgebase-chunks", embedding_function=None,
                configuration={"hnsw": {"space": "cosine"}},
            )
            sessions, store = build_session_factory(engine), ChromaStore(collection)
            recover_interrupted_files(sessions, store, assets=PdfAssets(directory))
            yield sessions, store
        finally:
            engine.dispose()
