# payments-platform

A FastAPI + Next.js payments platform that integrates Stripe PaymentIntents, records double-entry ledger entries, handles webhooks, and ships with a demo frontend for end-to-end testing—built with Dockerized Postgres/Redis and a Celery + RabbitMQ outbox pipeline for reliable async event fan-out.

## Tech stack

| Layer | Stack |
|-------|-------|
| API | Python 3.13, FastAPI, SQLAlchemy (async), Alembic, asyncpg, Pydantic v2, Poetry |
| Web | Next.js 16 (App Router), TypeScript, Tailwind CSS v4, Bun, Stripe.js |
| Infra | PostgreSQL, Redis, RabbitMQ, Docker Compose |
| Payments | Stripe PaymentIntents (manual capture) |

## Architecture overview

- API: Functional services and repositories; repositories return Pydantic DTOs, services own transaction boundaries and commits; processor abstraction via `PaymentProcessor` Protocol with `StripeAdapter`; FastAPI exception handlers map domain errors.
- Payments: `POST /payments/authorize` creates a PaymentIntent and writes ledger authorization entries; webhooks (`payment_intent.succeeded`, refunds) drive settlement and ledger updates; idempotency on authorize to reuse an existing intent.
- Ledger: Double-entry model with accounts, transactions, and entries; every event writes balanced debit and credit rows.
- Frontend: Next.js App Router demo page using Stripe Elements; calls API for authorization then confirms client-side with Stripe.js.
- Outbox (planned): During the same DB transaction as ledger writes, an outbox row is stored. A Celery worker publishes outbox events to RabbitMQ with retries and marks them sent.
- Consumers (planned): RabbitMQ consumers perform side effects off the critical path, such as notifications, fraud checks, and reporting.
- Reconciliation (planned): Nightly job compares ledger state with Stripe (and other processors if added) to flag drift.
- Observability: Logging via shared logger; liveness endpoint at `/_live`.

## Project structure

```
payments-platform/
  apps/
    api/                  FastAPI backend
      app/
        payments/         payment processing (authorize, capture, refund, webhooks)
        ledger/           double-entry ledger (transactions, entries, accounts)
      shared/             DB, processors, enums, exceptions, config
      alembic/            migrations
      scripts/            seed scripts
      tests/              pytest suite (ledger present, payments planned)
      main.py             app entry point
    web/                  Next.js frontend
      src/app             App Router pages
      src/components      Checkout form with Stripe Elements
  docker-compose.yml      Postgres, Redis, RabbitMQ
```

## Data flow (implemented)

1. Frontend calls `POST /payments/authorize`, API creates PaymentIntent (manual capture) and ledger authorization entries, returns `client_secret`.
2. Stripe Elements confirms the intent; Stripe finalizes authorization or success.
3. Stripe webhook hits `/payments/webhooks/stripe`; API verifies signature and dispatches to payment service.
4. Service settles payment record and writes ledger settlement entries in a single transaction.
5. Idempotent authorize reuses an existing intent instead of creating a new one.

## Asynchronous processing (planned)

- Outbox table written in the same transaction as ledger changes.
- Celery worker polls outbox, publishes to RabbitMQ with at-least-once semantics, marks rows as sent.
- Dedicated consumers handle notifications, fraud checks, reporting, and any downstream integrations without blocking the checkout path.

## Reconciliation (planned)

- Scheduled job compares internal ledger balances and payment records against Stripe data.
- Flags discrepancies and can emit reconciliation events through the same outbox and consumer pipeline.

## Getting started

### Prerequisites

- Python 3.13+
- Poetry
- Bun
- Docker and Docker Compose
- Stripe test account

### 1. Start infrastructure

```bash
make infra
```

### 2. Set up the API

```bash
cd apps/api
cp .env.example .env   # fill in STRIPE_SECRET_KEY etc.
poetry install
make migrate
make seed
```

API runs at `http://localhost:8000`.

### 3. Set up the frontend

```bash
cd apps/web
bun install
echo 'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY' > .env.local
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000' >> .env.local
```

Frontend runs at `http://localhost:3000`.

### 4. Start everything

```bash
make dev   # starts infra + api + web concurrently
```

Or start each individually:

```bash
make api   # FastAPI on :8000
make web   # Next.js on :3000
```

### 5. Forward Stripe webhooks

```bash
stripe listen --forward-to localhost:8000/payments/webhooks/stripe
```

Copy the printed `whsec_...` into `apps/api/.env` as `STRIPE_WEBHOOK_SECRET` and restart the API if it changes.

## Make targets

Run `make help` to see all targets. Common ones:

| Target | Description |
|--------|-------------|
| `make infra` | Start Postgres, Redis, RabbitMQ |
| `make infra-down` | Stop infrastructure |
| `make infra-reset` | Stop infrastructure and destroy volumes |
| `make infra-logs` | Tail infrastructure logs |
| `make dev` | Start infra + api + web concurrently |
| `make api` | Start FastAPI dev server |
| `make web` | Start Next.js dev server |
| `make migrate` | Run Alembic migrations |
| `make downgrade` | Rollback one migration |
| `make migration` | Create a new migration (prompts for name) |
| `make seed` | Seed ledger accounts |
| `make lint` | Fix lint and format issues (api + web) |
| `make typecheck` | Run mypy (api) and tsc (web) |
| `make test` | Run all tests |
| `make test-api` | Run pytest only |
| `make test-web` | Run web tests only |
| `make test-watch` | Run web tests in watch mode |
| `make check` | Read-only lint + typecheck + all tests (CI) |
| `make clean` | Remove `__pycache__`, `.mypy_cache`, `.ruff_cache`, `*.pyc` |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/payments/authorize` | Create PaymentIntent and ledger authorization entries |
| POST | `/payments/capture` | Capture an authorized payment |
| POST | `/payments/refund` | Refund a captured payment |
| POST | `/payments/webhooks/stripe` | Stripe webhook receiver |
| GET  | `/_live` | Liveness check |

## Environment variables

### API (`apps/api/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `STRIPE_SECRET_KEY` | Yes | Stripe secret key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret (`whsec_...`) |
| `DATABASE_URL` | No | PostgreSQL connection string (default: `postgresql+asyncpg://postgres:postgres@localhost:5432/payments`) |
| `REDIS_URL` | No | Redis connection string (default: `redis://localhost:6379/0`) |
| `RABBITMQ_URL` | No | RabbitMQ connection string (default: `amqp://guest:guest@localhost:5672/`) |
| `PROCESSOR` | No | Payment processor to use (default: `stripe`) |
| `EXPENSE_ACCOUNT_ID` | No | Ledger expense account UUID |
| `LIABILITY_ACCOUNT_ID` | No | Ledger liability account UUID |
| `CASH_ACCOUNT_ID` | No | Ledger cash account UUID |

### Web (`apps/web/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Yes | Stripe publishable key (`pk_test_...`) |
| `NEXT_PUBLIC_API_URL` | No | API base URL for the frontend (default: `http://localhost:8000`) |
