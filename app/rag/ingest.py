from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import LegalChunk
from app.db.orm import ChunkRow
from app.db.session import get_session_factory, init_db
from app.rag.embeddings import get_embedder, reset_embedder

DEFAULT_CHUNKS_DIR = Path(__file__).resolve().parents[2] / "data" / "chunks"
BATCH_SIZE = 64


def load_chunks(path: Path) -> list[LegalChunk]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [LegalChunk(**row) for row in payload["chunks"]]


def load_chunks_from_dir(directory: Path) -> list[LegalChunk]:
    chunks: list[LegalChunk] = []
    for path in sorted(directory.glob("*.json")):
        chunks.extend(load_chunks(path))
    return chunks


def dedupe_values_by_chunk_id(values: list[dict]) -> list[dict]:
    """PostgreSQL upsert rejects duplicate primary keys within one INSERT."""
    unique: dict[str, dict] = {}
    for row in values:
        unique[row["chunk_id"]] = row
    return list(unique.values())


def upsert_chunk_rows(
    session: Session,
    values: list[dict],
) -> int:
    if not values:
        return 0

    values = dedupe_values_by_chunk_id(values)
    table = ChunkRow.__table__
    stmt = insert(table).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[table.c.chunk_id],
        set_={
            "law": stmt.excluded.law,
            "article": stmt.excluded.article,
            "paragraph": stmt.excluded.paragraph,
            "text": stmt.excluded.text,
            "metadata": stmt.excluded.metadata,
            "embedding": stmt.excluded.embedding,
            "embedding_model": stmt.excluded.embedding_model,
        },
    )
    session.execute(stmt)
    session.commit()
    return len(values)


def ingest_chunks(
    chunks: list[LegalChunk],
    *,
    batch_size: int = BATCH_SIZE,
) -> int:
    embedder = get_embedder()
    session = get_session_factory()()
    total = 0

    try:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            vectors = embedder.embed_documents([chunk.text for chunk in batch])
            values = [
                {
                    "chunk_id": chunk.chunk_id,
                    "law": chunk.law,
                    "article": chunk.article,
                    "paragraph": chunk.paragraph,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                    "embedding": vector,
                    "embedding_model": embedder.model_name,
                }
                for chunk, vector in zip(batch, vectors, strict=True)
            ]
            total += upsert_chunk_rows(session, values)
            print(f"Ingested {total}/{len(chunks)} chunks")
    finally:
        session.close()

    return total


def ingest_path(path: Path) -> int:
    if path.is_dir():
        chunks = load_chunks_from_dir(path)
    else:
        chunks = load_chunks(path)
    return ingest_chunks(chunks)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in {"-h", "--help"}:
        print(
            "Usage: python -m app.rag.ingest [chunks.json|chunks_dir]\n"
            "Embeds legal chunks and upserts them into PostgreSQL + pgvector.\n"
            "Default input: data/chunks/"
        )
        return

    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CHUNKS_DIR
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    init_db()
    reset_embedder()
    count = ingest_path(input_path)
    print(f"Done. Upserted {count} chunks.")


if __name__ == "__main__":
    main()
