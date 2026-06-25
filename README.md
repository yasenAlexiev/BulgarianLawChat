# Bulgarian Law Chat

RAG API за търсене и отговори върху български нормативни актове (FastAPI + PostgreSQL + pgvector).

## Setup

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -e .
docker compose up -d
copy .env.example .env
python -m app.rag.ingest data\chunks
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs
