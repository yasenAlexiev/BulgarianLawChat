from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.db.session import init_db
from app.rag.embeddings import reset_embedder


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_settings().init_db_on_startup:
        reset_embedder()
        init_db()
    yield


app = FastAPI(
    title="Bulgarian Law Chat",
    description="RAG API over Bulgarian legal texts with pgvector retrieval.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "Bulgarian Law Chat",
        "docs": "/docs",
        "search": "/api/v1/search",
        "ask": "/api/v1/ask",
    }
