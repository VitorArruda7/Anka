# Anka Investment Backend

FastAPI backend service for the Anka financial dashboard. Provides authentication, client management, asset allocations, movements, and export features.

## Requirements

- Python 3.11+
- PostgreSQL 15
- Redis 7

## Setup (local)

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Testing

```bash
pytest
```

## Docker

```bash
docker build -t anka-backend .
docker run --rm -it -p 8000:8000 --env-file .env anka-backend
```

Environment variables are loaded via `.env` (see `app/core/config.py`).
