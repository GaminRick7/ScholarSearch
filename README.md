# ScholarSearch

Discover the right papers faster: hybrid BM25 + BERT search with an interactive citation graph for research influence patterns.

AI-powered research paper discovery engine with hybrid search (BM25 + BERT embeddings), citation network visualization, and a modern Next.js frontend. Backend is built with FastAPI, PostgreSQL, Redis caching, and ChromaDB for vector search. Fully containerized with Docker Compose.

## Features
- **Hybrid search**: custom BM25 (implemented from scratch) keyword relevance + BERT semantic similarity (Sentence Transformers all-MiniLM-L6-v2)
- **Redis-backed caching** with cache warming and cache management endpoints
- **ChromaDB vector store** integration for semantic retrieval
- **PostgreSQL** relational schema for papers, authors, venues, citations
- **Interactive citation network visualization** using graph data structures (O(1) vertex lookup, efficient traversal) rendered with D3/React
- **Production-friendly**: health checks, service-level status, and observability hooks

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, Pydantic, Uvicorn
- **Search/AI**: Custom BM25 implementation, Sentence Transformers, ChromaDB
- **Data**: PostgreSQL, Redis
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind, Radix UI, D3
- **Infra**: Docker, Docker Compose

## Repository Layout
- `src/app` — FastAPI application (APIs, services, models)
- `visual-search-engine` — Next.js + TypeScript frontend
- `docker-compose.yml` — Postgres, Redis, ChromaDB services
- `requirements.txt` — Python backend dependencies

## Quickstart (Docker Compose)
Prerequisites: Docker and Docker Compose installed.

```bash
# From repo root
docker compose up -d

# Services exposed
# - FastAPI:     http://localhost:8000
# - PostgreSQL:  localhost:5432 (scholarnet / scholarnet / scholarnet)
# - Redis:       localhost:6379
# - ChromaDB:    http://localhost:8001
```

Then, run the frontend:
```bash
cd visual-search-engine
pnpm install   # or npm install / yarn
pnpm dev       # or npm run dev
# Frontend: http://localhost:3000
```

## Local Development (without Docker)
Prerequisites: Python 3.11+, Node 18+/20+, PostgreSQL 15+, Redis 7+, ChromaDB server.

1) Python environment and deps
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2) Environment variables (adjust as needed)
Create `.env` from `env.example` at repo root.

Key variables the backend reads (defaults shown):
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
DATABASE_URL=postgresql+psycopg2://scholarnet:scholarnet@localhost:5432/scholarnet
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

3) Start backend (FastAPI)
```bash
python -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

4) Start frontend (Next.js)
```bash
cd visual-search-engine
pnpm install && pnpm dev
```

## Data Ingestion and Embedding
- Create/update papers via REST (see endpoints below). The BM25 index auto-builds and updates on changes.
- Add vectors to ChromaDB for semantic search:
```bash
# Triggers embedding of all non-stub, unembedded papers
POST http://localhost:8000/api/v1/papers/vectors/
```

## Key API Endpoints
Base URL: `http://localhost:8000`

### Health and status
- `GET /` — API info and feature flags
- `GET /health` — Aggregated service health (DB, Redis, Chroma)

### Search
- `POST /api/v1/search`
  - Request body:
    ```json
    {
      "query": "transformers",
      "page": 1,
      "size": 20,
      "bert_weight": 2.0,
      "citation_weight": 0.5
    }
    ```
  - Returns hybrid-ranked results combining BM25 and BERT (with optional citation boost)

### Suggestions
- `GET /api/v1/suggest/{text}` — Semantic suggestions using ChromaDB

### Papers
- `GET /api/v1/papers` — Paginated list
- `GET /api/v1/papers/{paper_id}` — Paper details (authors, references)
- `POST /api/v1/papers` — Bulk create papers (see `PaperTemplate` in backend)
- `PUT /api/v1/papers/{paper_id}` — Update paper (also updates BM25 index)
- `DELETE /api/v1/papers/{paper_id}`