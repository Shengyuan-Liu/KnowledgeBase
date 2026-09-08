from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.storage.models import Base


def build_engine(database_url: str) -> Engine:
    """Create an engine and enable foreign keys on each new SQLite connection."""
    engine = create_engine(database_url)

    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _connection_record):
            # SQLite requires this PRAGMA to run outside a transaction.
            previous_autocommit = connection.autocommit
            connection.autocommit = True
            try:
                connection.execute("PRAGMA foreign_keys=ON").close()
            finally:
                connection.autocommit = previous_autocommit

    return engine


def init_db(engine: Engine) -> None:
    """Create missing tables without dropping data or migrating existing tables."""
    Base.metadata.create_all(engine)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a factory for independent sessions bound to the engine.

    Callers own session cleanup and transaction boundaries. Use the factory's
    begin() context manager to commit on success and roll back on failure.
    """
    return sessionmaker(bind=engine)
