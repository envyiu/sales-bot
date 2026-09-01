# Sales Bot

Foundation monorepo for an AI sales chatbot. The development stack runs entirely with Docker Compose.

## Architecture

```text
Next.js :3000
    |
FastAPI :8000
    |
PostgreSQL + pgvector :5432
```

## Setup

Copy the example environment file, then start the three services:

```bash
cp .env.example .env
docker compose up --build
```

The database uses the `pgvector/pgvector:pg16` image and stores data in the named `postgres_data` volume.

## URLs

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health
- DB Health: http://localhost:8000/health/db

## Database migrations

Alembic is configured to use the same `DATABASE_URL` as the application. There are no application tables or migrations yet.

```bash
docker compose exec backend alembic current
```

## Stop

```bash
docker compose down
```

## Full reset

```bash
docker compose down -v
```

The `.env` file is ignored by Git. Do not commit real credentials or secrets.
