from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_settings().init_db_on_startup:
        init_db()
    yield


app = FastAPI(
    title="Bulgarian Law Chat",
    description="RAG API over Bulgarian legal texts with pgvector retrieval.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "Bulgarian Law Chat",
        "docs": "/docs",
        "search": "/api/v1/search",
    }
