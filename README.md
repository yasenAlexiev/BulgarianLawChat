# Bulgarian Law Chat

RAG API за търсене и отговори върху български нормативни актове (FastAPI + PostgreSQL + pgvector) с React чат frontend.

## Setup

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -e .
docker compose up -d
copy .env.example .env
python -m app.integration.corpus_pipeline --ingest
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Корпус: от raw текст до векторна база

Нормативните актове минават през четири JSON етапа преди да влязат в pgvector:

```
data/raw/*.txt
    │  parser
    ▼
data/processed/*.json
    │  normalizer
    ▼
data/normalized/*.json
    │  chunker
    ▼
data/chunks/*.json
    │  ingest (embeddings)
    ▼
PostgreSQL + pgvector
```

### Какво прави всяка стъпка

| Етап | Папка | Модул | Описание |
|------|-------|-------|----------|
| 1. Parse | `data/raw/` → `data/processed/` | `app.integration.parser` | Чете `.txt` от lex.bg и извлича структура: заглавие, членове, алинеи |
| 2. Normalize | `data/processed/` → `data/normalized/` | `app.integration.normalizer` | Преобразува дървовидния JSON в плоски документи (1 ред = член или алинея), почиства текста |
| 3. Chunk | `data/normalized/` → `data/chunks/` | `app.rag.chunker` | Групира за RAG: 1 chunk = 1 член; ако членът е твърде дълъг → по 1 chunk на алинея |
| 4. Ingest | `data/chunks/` → DB | `app.rag.ingest` | Генерира embeddings и ги записва в PostgreSQL (pgvector) |

Файловете запазват едно и също име във всяка папка, напр. `кодекс-на-труда.txt` → `кодекс-на-труда.json`.

### Всичко наведнъж

Обработва **всички** `.txt` файлове в `data/raw/` и (с `--ingest`) ги зарежда в базата:

```powershell
python -m app.integration.corpus_pipeline --ingest
```

Само JSON етапите, без ingest в базата:

```powershell
python -m app.integration.corpus_pipeline
```

Един конкретен закон:

```powershell
python -m app.integration.corpus_pipeline data\raw\кодекс-на-труда.txt --ingest
```

### Стъпка по стъпка (един файл)

```powershell
python -m app.integration.parser data\raw\кодекс-на-труда.txt data\processed\кодекс-на-труда.json
python -m app.integration.normalizer data\processed\кодекс-на-труда.json data\normalized\кодекс-на-труда.json
python -m app.rag.chunker data\normalized\кодекс-на-труда.json data\chunks\кодекс-на-труда.json
python -m app.rag.ingest data\chunks
```

### Добавяне на нов закон

1. Сложи `.txt` файла в `data/raw/` (копие от lex.bg, UTF-8).
2. Пусни `python -m app.integration.corpus_pipeline --ingest`.
3. Рестартирай API сървъра (ако вече работи).

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Чатът е на http://localhost:5173 — Vite проксира `/api` към backend на порт 8000.

За production build задайте `VITE_API_URL` (напр. `https://api.example.com/api/v1`).
