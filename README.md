# SLA Monitor
Real-time uptime and latency monitoring platform.

## Stack
FastAPI · React · PostgreSQL · Redis · Celery · Docker

## .env example
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=

REDIS_HOST=localhost
REDIS_PORT=6379

APP_ENV=development
LOG_LEVEL=INFO

## Run locally
1. Copy `.env` and fill in values
2. `docker compose up --build`
3. Frontend: http://localhost:5173
4. API: http://localhost:8000