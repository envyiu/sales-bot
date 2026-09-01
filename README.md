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

## Database setup

Alembic manages the catalog schema. The initial migration enables the PostgreSQL `vector` extension and creates the `products`, `product_specs`, and `inventory` tables. The seed script inserts a small demo catalog.

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed_catalog
```

The seed command is idempotent and can be run again without duplicating products.

## URLs

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health
- DB Health: http://localhost:8000/health/db

## Catalog API

- `GET /api/products` — list active products with pagination, filters, search, and sorting.
- `GET /api/products/{slug}` — get an active product with its specification and inventory.

Examples:

```bash
curl 'http://localhost:8000/api/products?brand=Samsung&brand=Apple&limit=5'
curl 'http://localhost:8000/api/products?q=galaxy&sort=price_asc'
curl 'http://localhost:8000/api/products/samsung-galaxy-a56-5g'
```

## Database migrations

Alembic is configured to use the same `DATABASE_URL` as the application. The catalog migration creates the initial application tables.

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
