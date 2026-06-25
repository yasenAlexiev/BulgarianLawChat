# Bulgarian Law Chat

RAG API за търсене и отговори върху български нормативни актове (FastAPI + PostgreSQL + pgvector) с React чат frontend.

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

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Чатът е на http://localhost:5173 — Vite проксира `/api` към backend на порт 8000.

За production build задайте `VITE_API_URL` (напр. `https://api.example.com/api/v1`).
