from __future__ import annotations

from app.config import get_settings
from app.rag.retriever import SearchResult


_reranker = None
_reranker_model: str | None = None


def reset_reranker() -> None:
    global _reranker, _reranker_model
    _reranker = None
    _reranker_model = None


def _get_reranker():
    global _reranker, _reranker_model
    settings = get_settings()
    if _reranker is None or _reranker_model != settings.rerank_model:
        from sentence_transformers import CrossEncoder

        _reranker = CrossEncoder(settings.rerank_model)
        _reranker_model = settings.rerank_model
    return _reranker


def rerank_chunks(
    question: str,
    chunks: list[SearchResult],
    *,
    enabled: bool | None = None,
) -> list[SearchResult]:
    if not chunks:
        return []

    settings = get_settings()
    use_rerank = settings.rerank_enabled if enabled is None else enabled
    if not use_rerank:
        return chunks

    model = _get_reranker()
    pairs = [(question, chunk.text) for chunk in chunks]
    scores = model.predict(pairs)

    ranked = sorted(
        zip(chunks, scores, strict=True),
        key=lambda item: float(item[1]),
        reverse=True,
    )
    return [
        SearchResult(
            chunk_id=chunk.chunk_id,
            law=chunk.law,
            article=chunk.article,
            paragraph=chunk.paragraph,
            text=chunk.text,
            metadata=chunk.metadata,
            score=round(float(score), 4),
        )
        for chunk, score in ranked
    ]
