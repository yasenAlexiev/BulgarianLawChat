from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import get_settings
from app.rag.generator import generate_answer, generate_answer_stream
from app.rag.query import clean_question, retrieval_queries
from app.rag.reranker import rerank_chunks
from app.rag.retriever import SearchResult, search_chunks_multi


@dataclass
class AnswerResult:
    question: str
    cleaned_query: str
    answer: str
    sources: list[SearchResult]


@dataclass
class StreamContext:
    """Context data for streaming response."""

    question: str
    cleaned_query: str
    sources: list[SearchResult]


def answer_question(
    session: Session,
    question: str,
    *,
    retrieval_top_k: int | None = None,
    context_top_k: int | None = None,
    rerank: bool | None = None,
) -> AnswerResult:
    settings = get_settings()
    cleaned = clean_question(question)
    retrieve_k = retrieval_top_k or settings.retrieval_top_k
    context_k = context_top_k or settings.context_top_k

    chunks = search_chunks_multi(
        session,
        retrieval_queries(cleaned),
        top_k=retrieve_k,
    )
    chunks = rerank_chunks(cleaned, chunks, enabled=rerank)
    context_chunks = chunks[:context_k]

    answer = generate_answer(cleaned, context_chunks)
    return AnswerResult(
        question=question,
        cleaned_query=cleaned,
        answer=answer,
        sources=context_chunks,
    )


def prepare_stream_context(
    session: Session,
    question: str,
    *,
    retrieval_top_k: int | None = None,
    context_top_k: int | None = None,
    rerank: bool | None = None,
) -> StreamContext:
    """Prepare context for streaming (retrieval + reranking) without generating answer."""
    settings = get_settings()
    cleaned = clean_question(question)
    retrieve_k = retrieval_top_k or settings.retrieval_top_k
    context_k = context_top_k or settings.context_top_k

    chunks = search_chunks_multi(
        session,
        retrieval_queries(cleaned),
        top_k=retrieve_k,
    )
    chunks = rerank_chunks(cleaned, chunks, enabled=rerank)
    context_chunks = chunks[:context_k]

    return StreamContext(
        question=question,
        cleaned_query=cleaned,
        sources=context_chunks,
    )


def stream_answer(context: StreamContext) -> Generator[str, None, None]:
    """Stream the answer tokens given a prepared context."""
    yield from generate_answer_stream(context.cleaned_query, context.sources)
