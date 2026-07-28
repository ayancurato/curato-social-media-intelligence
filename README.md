# Curato AI — Social Media Intelligence System

Enterprise-grade multi-agent AI platform for intelligent social media content generation.

## Architecture

```
├── backend/          # FastAPI + Python (Agents, Orchestrator, API)
├── frontend/         # Next.js + TypeScript (Dashboard UI)
└── docker-compose.yml  # Local development infrastructure
```

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker Desktop (for PostgreSQL + Redis)

### 1. Start Infrastructure
```bash
docker-compose up -d postgres redis
```

### 2. Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. Celery Worker
```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 5. Open Dashboard
Navigate to `http://localhost:3000`

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

## Deployment

- **Frontend**: Vercel
- **Backend**: Railway (FastAPI + Celery + PostgreSQL + Redis)
