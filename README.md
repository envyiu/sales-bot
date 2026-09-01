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

The database uses the `pgvector/pgvector:pg16` image and stores data in the named `postgres_data` volume. Set `GOOGLE_API_KEY` in `.env` before using the chat endpoint; the key is consumed by the backend only.

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

## Storefront

The Next.js storefront fetches the catalog from FastAPI on the server using `BACKEND_API_URL`. The Docker-only hostname is never exposed as a browser-side public environment variable.

- `GET /` — storefront home and catalog CTA.
- `GET /products` — searchable, filterable, sortable catalog with pagination.
- `GET /products/{slug}` — product detail with specifications and stock.

## Catalog API

- `GET /api/products` — list active products with pagination, filters, search, and sorting.
- `GET /api/products/{slug}` — get an active product with its specification and inventory.

Examples:

```bash
curl 'http://localhost:8000/api/products?brand=Samsung&brand=Apple&limit=5'
curl 'http://localhost:8000/api/products?q=galaxy&sort=price_asc'
curl 'http://localhost:8000/api/products/samsung-galaxy-a56-5g'
```

## Chat API

`POST /api/chat` sends a message through LangChain and the configured Gemini model. A missing `conversation_id` starts a conversation; reuse the returned ID for follow-up messages.

```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Tôi cần tư vấn điện thoại cho việc chụp ảnh."}'
```

Chat history is stored in `conversations` and `messages`. LangChain message payloads are stored as JSONB so tool-call metadata can be rehydrated. The advisor can call `search_products`, `get_product_detail`, and `check_inventory`; tool executions are recorded in `tool_calls`.

Recommendations are ranked from catalog scores in the database. Current inventory questions use `check_inventory` at request time. Tool telemetry is committed as execution events, while chat messages are committed only as a complete successful turn; a failed first turn can therefore leave an empty conversation with telemetry. Streaming, RAG, and a frontend chat widget are not enabled yet.

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
