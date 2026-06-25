import json
from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import (
    AskRequest,
    AskResponse,
    ChunkHit,
    HealthResponse,
    SearchRequest,
    SearchResponse,
    SourceCitation,
)
from app.config import get_settings
from app.db.session import get_db
from app.rag.embeddings import get_embedder
from app.rag.pipeline import answer_question, prepare_stream_context, stream_answer
from app.rag.retriever import search_chunks

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}")

    return HealthResponse(
        status="ok",
        database=db_status,
        embedding_provider=settings.embedding_provider,
        embedding_model=get_embedder().model_name,
        llm_model=settings.llm_model,
    )


@router.post("/search", response_model=SearchResponse)
def search(
    body: SearchRequest,
    db: Session = Depends(get_db),
) -> SearchResponse:
    hits = search_chunks(db, body.query, top_k=body.top_k)
    return SearchResponse(
        query=body.query,
        results=[
            ChunkHit(
                chunk_id=hit.chunk_id,
                law=hit.law,
                article=hit.article,
                paragraph=hit.paragraph,
                text=hit.text,
                metadata=hit.metadata,
                score=hit.score,
            )
            for hit in hits
        ],
    )


@router.post("/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    db: Session = Depends(get_db),
) -> AskResponse:
    try:
        result = answer_question(
            db,
            body.question,
            retrieval_top_k=body.retrieval_top_k,
            context_top_k=body.context_top_k,
            rerank=body.rerank,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AskResponse(
        question=result.question,
        cleaned_query=result.cleaned_query,
        answer=result.answer,
        sources=[
            SourceCitation(
                chunk_id=source.chunk_id,
                law=source.law,
                article=source.article,
                paragraph=source.paragraph,
                text=source.text,
                metadata=source.metadata,
                score=source.score,
            )
            for source in result.sources
        ],
    )


@router.post("/ask/stream")
def ask_stream(
    body: AskRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream the answer using Server-Sent Events (SSE).

    Event types:
    - "metadata": Initial event with question, cleaned_query, and sources
    - "token": Each token chunk of the answer
    - "done": Final event indicating the stream is complete
    - "error": Error event if something goes wrong
    """
    try:
        context = prepare_stream_context(
            db,
            body.question,
            retrieval_top_k=body.retrieval_top_k,
            context_top_k=body.context_top_k,
            rerank=body.rerank,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    def generate_sse() -> Generator[str, None, None]:
        metadata = {
            "question": context.question,
            "cleaned_query": context.cleaned_query,
            "sources": [
                {
                    "chunk_id": source.chunk_id,
                    "law": source.law,
                    "article": source.article,
                    "paragraph": source.paragraph,
                    "text": source.text,
                    "metadata": source.metadata,
                    "score": source.score,
                }
                for source in context.sources
            ],
        }
        yield f"event: metadata\ndata: {json.dumps(metadata, ensure_ascii=False)}\n\n"

        try:
            for token in stream_answer(context):
                token_data = json.dumps({"token": token}, ensure_ascii=False)
                yield f"event: token\ndata: {token_data}\n\n"

            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            error_data = json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
