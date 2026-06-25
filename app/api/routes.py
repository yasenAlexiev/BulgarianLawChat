from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import ChunkHit, HealthResponse, SearchRequest, SearchResponse
from app.config import get_settings
from app.db.session import get_db
from app.rag.embeddings import get_embedder
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
