from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.orm import ChunkRow
from app.rag.embeddings import get_embedder


@dataclass
class SearchResult:
    chunk_id: str
    law: str
    article: str
    paragraph: str | None
    text: str
    metadata: dict
    score: float


def search_chunks(
    session: Session,
    query: str,
    *,
    top_k: int = 5,
) -> list[SearchResult]:
    embedder = get_embedder()
    query_vector = embedder.embed_query(query)

    distance = ChunkRow.embedding.cosine_distance(query_vector)
    stmt = (
        select(ChunkRow, distance.label("distance"))
        .order_by(distance)
        .limit(top_k)
    )
    rows = session.execute(stmt).all()

    results: list[SearchResult] = []
    for row, dist in rows:
        results.append(
            SearchResult(
                chunk_id=row.chunk_id,
                law=row.law,
                article=row.article,
                paragraph=row.paragraph,
                text=row.text,
                metadata=row.metadata_ or {},
                score=round(1.0 - float(dist), 4),
            )
        )
    return results
