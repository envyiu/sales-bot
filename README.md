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

The backend routes requests through this priority-ordered Gemini model fallback chain:

```text
gemini-3.5-flash-lite (15 RPM)
gemini-3.1-flash-lite (15 RPM)
gemma-4-31b-it (30 RPM)
gemma-4-26b-a4b-it (30 RPM)
```

The limiter and provider cooldown state are in memory for the single Docker backend process. If the backend is later scaled across workers or containers, move that state to shared storage such as Redis.

For tool-call turns, the router reads `AIMessage.response_metadata["model_name"]` and keeps the complete tool protocol within one model family. Gemini tool histories use only the two Gemini models; Gemma tool histories can use the two Gemma models because cross-Gemma history was verified with the current provider integration. This prevents the known Gemini-tool-history to Gemma `400 INVALID_ARGUMENT` response.

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

`POST /api/chat` sends a message through LangChain and the model fallback router. The response includes the model that actually answered. A missing `conversation_id` starts a conversation; reuse the returned ID for follow-up messages.

```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Tôi cần tư vấn điện thoại cho việc chụp ảnh."}'
```

Chat history is stored in `conversations` and `messages`. LangChain message payloads are stored as JSONB so tool-call metadata can be rehydrated. The advisor can call `search_products`, `get_product_detail`, `check_inventory`, and `retrieve_product_knowledge`; tool executions are recorded in `tool_calls`.

Recommendations are ranked from catalog scores in the database. Current inventory questions use `check_inventory` at request time. Semantic experience questions can use the scoped product knowledge corpus; structured catalog data remains authoritative for price, stock, and exact specifications. Tool telemetry is committed as execution events, while chat messages are committed only as a complete successful turn; a failed first turn can therefore leave an empty conversation with telemetry.

## Knowledge RAG

Knowledge files live in `backend/data/knowledge/`, one Markdown file per product slug. The ingestion script resolves slugs against the catalog, splits topic sections, and stores Gemini Embedding 2 vectors in `product_documents` using 768 dimensions.

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed_catalog
docker compose exec backend python -m scripts.ingest_knowledge
```

The `retrieve_product_knowledge` tool is scoped to recommendation candidates when appropriate. It provides semantic evidence for gaming, camera, video, battery experience, thermals, strengths, weaknesses, and suitable users; it is not authoritative for live price, stock, or exact specifications.

The storefront includes a floating chat widget. Browser requests go to the same-origin Next.js `/api/chat` proxy, while the backend URL and Google API key remain server-side. The browser stores only `conversation_id` in localStorage; the transcript currently resets after a full page reload because no public history endpoint exists yet.

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

## Authentication and sessions

The storefront provides `/register`, `/login`, and `/account`. Authentication uses
email and password with Argon2id hashes; passwords are never stored. FastAPI creates
opaque 256-bit session tokens and stores only their SHA-256 hashes in
`auth_sessions`. The trusted Next.js BFF keeps the raw token in the
`sales_bot_session` HttpOnly, SameSite=Lax cookie. Sessions last 24 hours by
default (`AUTH_SESSION_TTL_SECONDS=86400`); set `AUTH_COOKIE_SECURE=true` when
serving the frontend over HTTPS.

The backend auth endpoints are `POST /api/auth/register`, `POST /api/auth/login`,
`POST /api/auth/logout`, and `GET /api/auth/me`. Browser code calls the same-origin
Next.js BFF routes only. Registration and login are limited per client IP in the
single frontend process (5 and 10 requests per minute); scaled deployments should
move this limiter to shared storage such as Redis.

Chat remains available anonymously. A new authenticated chat conversation stores
its `user_id`; only that user can load it. Existing anonymous conversations remain
unclaimed, and an old anonymous conversation is never automatically attached to an
account. Auth/session and conversation authorization actions emit structured JSON
security events, including login failures, session invalidation, logout, rate
limits, and denied conversation access. Failed-login email values are represented
by a SHA-256 pseudonymous fingerprint for correlation, not anonymization.
