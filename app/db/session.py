from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db.orm import Base, ChunkRow

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), autoflush=False, autocommit=False
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create pgvector extension, tables, and HNSW index."""
    settings = get_settings()
    engine = get_engine()

    ChunkRow.__table__.c.embedding.type.dim = settings.embedding_dimension  # type: ignore[attr-defined]

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        existing_dim = conn.execute(
            text(
                """
                SELECT NULLIF(
                    substring(format_type(a.atttypid, a.atttypmod) from 'vector\\((\\d+)\\)'),
                    ''
                )::int
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relname = 'legal_chunks'
                  AND a.attname = 'embedding'
                  AND NOT a.attisdropped
                  AND n.nspname = 'public'
                """
            )
        ).scalar()

        if existing_dim is not None and existing_dim != settings.embedding_dimension:
            conn.execute(text("DROP TABLE legal_chunks"))

        conn.commit()

    Base.metadata.create_all(bind=engine)
