# Sales Bot Agent Guide

## Scope

This repository is a Docker-first monorepo for a smartphone storefront and AI sales advisor:

- `frontend/`: Next.js 16, React 19, TypeScript, App Router.
- `backend/`: FastAPI, SQLAlchemy async, PostgreSQL/pgvector, Alembic.
- `docker-compose.yml`: the supported development environment.

Keep changes within the assigned task. Do not add infrastructure, AI features, schemas, or dependencies speculatively.

## Development workflow

- Use Docker Compose; do not require host Python, Node.js, or PostgreSQL.
- Copy `.env.example` to `.env` for local work. Never commit `.env`, API keys, passwords, or provider payloads containing secrets.
- Start the stack with `docker compose up --build -d`.
- Preserve unrelated user changes in a dirty worktree.
- Work on the requested task branch. Do not merge into `main` unless explicitly instructed.

## Backend conventions

- Keep the flow `route -> service -> SQLAlchemy -> PostgreSQL`.
- Routes parse HTTP input and map service errors; services must not raise `HTTPException`.
- Use SQLAlchemy 2.x async APIs and request-scoped `AsyncSession` instances.
- Use eager loading or explicit joins; never rely on async relationship lazy loading or introduce N+1 queries.
- Use SQLAlchemy expressions/bound parameters for user input. Never construct SQL from raw strings.
- Keep database invariants as real PostgreSQL constraints, not Python-only validation.
- Return explicit Pydantic v2 schemas rather than raw ORM objects.

## Database and migrations

- Application metadata comes from `app.db.base.Base`; ensure new models are imported in `app.models`.
- Create a new Alembic revision for schema changes. Do not rewrite an approved migration unless the task explicitly says the migration is still under review.
- Downgrades must drop dependent objects before their parents and preserve unrelated schema/data.
- Seed scripts must be idempotent, transactional, and must not overwrite unrelated records.
- Do not use SQLite fallbacks.

## Chat and model invariants

- Persist complete LangChain messages with `message_to_dict()` and rehydrate with `messages_from_dict()`.
- Keep each successful user/tool/assistant protocol sequence ordered and atomic; do not persist partial chat turns.
- Tool dispatch must use an explicit whitelist and Pydantic argument validation. Never use `eval`, arbitrary `getattr`, or dynamic imports from model output.
- Store-specific products, prices, specifications, and stock must come from database-backed tools. Current-stock questions must call `check_inventory`.
- Preserve provider metadata and thought signatures on `AIMessage`; do not convert tool-call messages to plain text.
- Keep tool-aware history trimming so a `ToolMessage` is never orphaned from its preceding AI tool call.
- Preserve model priority and RPM policy in `app.agent.model_router`. Gemini tool history must not be sent to incompatible Gemma models.
- Never log prompts, full chat contents, credentials, or hidden provider reasoning.

## Frontend conventions

- Prefer Server Components. Add `"use client"` only to isolated interactive components.
- Browser code must call same-origin Next.js routes such as `/api/chat`; never expose `BACKEND_API_URL`, Docker hostnames, or `GOOGLE_API_KEY` in client bundles.
- Keep API calls and response types in `frontend/lib/`; do not scatter untyped `fetch()` calls across components.
- Do not use `any` or `dangerouslySetInnerHTML` for backend content.
- Reuse shared formatting and image fallback components.
- Preserve filters and pagination in URL query parameters and let the backend remain the source of truth.
- Keep chat requests single-flight, reuse the stored conversation ID, and surface non-2xx responses as controlled UI errors.

## Required verification

Run checks proportional to the change. Before handing off a cross-stack task, run at least:

```bash
docker compose up --build -d
docker compose ps
docker compose exec backend python -m unittest discover -s tests -v
docker compose exec backend alembic current
docker compose exec backend alembic check
docker compose exec backend python -m compileall app scripts tests
docker compose run --rm frontend npm run build
```

For database changes, also test migration upgrade/downgrade roundtrips and database constraints. For API/UI changes, verify real HTTP responses and the affected end-to-end flow. Report any test that could not be run rather than claiming it passed.

## Handoff

- Run `git diff --check` before committing.
- Use the task's requested commit message and push only the requested branch.
- Report the full commit SHA, verification results, important design decisions, and remaining limitations.
