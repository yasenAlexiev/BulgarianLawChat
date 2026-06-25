from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class ChunkHit(BaseModel):
    chunk_id: str
    law: str
    article: str
    paragraph: str | None
    text: str
    metadata: dict
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[ChunkHit]


class HealthResponse(BaseModel):
    status: str
    database: str
    embedding_provider: str
    embedding_model: str
