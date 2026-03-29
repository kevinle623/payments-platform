# payments-platform/apps/api

FastAPI backend implementing payment processing with double-entry ledger accounting, processor abstraction, idempotency, and Stripe webhook handling.

## Tech stack

- Python 3.13
- FastAPI
- SQLAlchemy (async) + asyncpg
- Alembic (migrations)
- Pydantic v2
- Poetry
- Stripe

## Project structure

```
app/
  payments/           Payment processing (authorize, capture, refund, webhooks)
    router.py         FastAPI routes
    service.py        Business logic + transaction boundaries
    repository.py     Data access (returns Pydantic DTOs, never ORM models)
    models.py         SQLAlchemy ORM models
    schemas.py        Pydantic request/response schemas
  ledger/             Double-entry ledger
    router.py         FastAPI routes
    service.py        Authorization + settlement entry recording
    repository.py     Transaction + entry data access
    models.py         Account, Transaction, Entry ORM models
    schemas.py        Pydantic DTOs
shared/
  processors/
    base.py           PaymentProcessor Protocol + normalized DTOs
    factory.py        get_processor() factory
    adapters/
      stripe.py       StripeAdapter implementation
  db/
    base.py           SQLAlchemy DeclarativeBase
    adapters/
      postgresql.py   Async engine, session, get_db
  enums/
    currency.py       Currency StrEnum
    processor.py      SupportedProcessorType StrEnum
  settings.py         Environment-based config
  exceptions.py       Domain exceptions
  exception_handlers.py  FastAPI exception handlers
  logger.py           Logging setup
scripts/
  seed.py             Seeds ledger accounts into DB
alembic/              Database migrations
main.py               FastAPI app entry point
```

## Getting started

```bash
# Install dependencies
poetry install

# Copy env and fill in Stripe keys
cp .env.example .env

# Start infrastructure (from monorepo root)
docker compose up -d

# Run migrations
poetry run alembic upgrade head

# Seed ledger accounts
poetry run python -m scripts.seed

# Start the server
poetry run uvicorn main:app --reload
```

Runs at `http://localhost:8000`.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/payments/authorize` | Create PaymentIntent + ledger authorization entries |
| `POST` | `/payments/capture` | Capture an authorized payment |
| `POST` | `/payments/refund` | Refund a captured payment |
| `POST` | `/payments/webhooks/stripe` | Stripe webhook receiver |
| `GET` | `/_live` | Liveness check |

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `STRIPE_SECRET_KEY` | Yes | Stripe secret key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Yes | Webhook signing secret (`whsec_...`) |
| `DATABASE_URL` | No | PostgreSQL connection string |
| `REDIS_URL` | No | Redis connection string |
| `RABBITMQ_URL` | No | RabbitMQ connection string |
| `PROCESSOR` | No | Payment processor (default: `stripe`) |
| `EXPENSE_ACCOUNT_ID` | No | Ledger expense account UUID |
| `LIABILITY_ACCOUNT_ID` | No | Ledger liability account UUID |
| `CASH_ACCOUNT_ID` | No | Ledger cash account UUID |

## Architecture

- **Service/repository pattern** -- repositories return Pydantic DTOs, services own transaction boundaries
- **Processor abstraction** -- `PaymentProcessor` Protocol with adapter implementations and a factory
- **Double-entry ledger** -- every payment event writes balanced debit/credit entries that sum to zero
- **Idempotency** -- duplicate authorize requests return the existing result without hitting Stripe
- **Atomic writes** -- payment record + ledger entries committed or rolled back together

## Webhook testing

```bash
stripe listen --forward-to localhost:8000/payments/webhooks/stripe
```

Copy the `whsec_...` signing secret into `.env` as `STRIPE_WEBHOOK_SECRET`.
