# payments-platform/apps/api

FastAPI backend implementing acquiring-side payment orchestration and issuer-side card simulation, backed by a double-entry ledger and a Celery + RabbitMQ async event pipeline.

## Tech stack

- Python 3.13, FastAPI, SQLAlchemy (async), asyncpg, Alembic, Pydantic v2, Poetry
- Stripe (payment processing)
- Celery + Celery Beat (scheduled tasks)
- aio-pika (async RabbitMQ client)

## Project structure

```
app/
  payments/             acquiring-side payment processing
    router.py           FastAPI routes
    service.py          business logic, transaction boundaries, outbox writes
    repository.py       data access -- returns Pydantic DTOs, never ORM models
    models.py           Payment ORM model
    schemas.py          request/response schemas + internal DTOs
  ledger/               double-entry ledger
    service.py          record_authorization(), record_settlement(), record_hold(), record_clear_hold()
    repository.py       accounts, transactions, entries
    models.py           Account, Transaction, Entry ORM models
  issuer/
    auth/               evaluate() -- idempotency, card lookup, controls, IssuerAuthorization record
    cards/              Cardholder + Card models, per-card ledger accounts, balance endpoint
    controls/           MCCBlock, VelocityRule, check_controls() rule engine
    settlement/         clear_hold() -- clears pending hold on payment settlement
  outbox/               OutboxEvent model, publish_event(), get_pending/mark_published/mark_failed
shared/
  processors/
    base.py             PaymentProcessor Protocol + normalized DTOs (PaymentIntent, PaymentStatus)
    factory.py          get_processor() based on PROCESSOR setting
    adapters/
      stripe.py         StripeAdapter
  db/
    base.py             SQLAlchemy DeclarativeBase
    adapters/
      postgresql.py     async engine, AsyncSessionLocal, get_db
  enums/
    currency.py         Currency StrEnum
    processor.py        SupportedProcessorType StrEnum
  settings.py           environment-based config (environ.get / environ[])
  exceptions.py         domain exceptions (PaymentDeclinedException, PaymentNotFoundError, etc.)
  exception_handlers.py FastAPI exception handlers
  logger.py             get_logger(__name__)
workers/
  exchanges.py          PAYMENTS_EXCHANGE, ISSUER_EXCHANGE -- single source of truth
  celery_app.py         Celery app, broker config, Beat schedules
  producers/
    payments/
      outbox_poller.py  Celery task: polls pending outbox rows, publishes to RabbitMQ payments exchange
  consumers/
    base.py             generic run_consumer/start (exchange, queue, routing_keys, handler)
    payments/
      fraud.py          payment.authorized -> risk score, flags high-value payments
      notifications.py  payment.* -> simulated notifications
      reporting.py      payment.* -> simulated analytics entries
    issuer/             future: card.issued, dispute.opened, hold.expired
  jobs/
    payments/
      reconciliation.py nightly Celery task: compares settled payments against Stripe
    issuer/             future: hold expiry, dispute aging
scripts/
  seed.py               seeds platform ledger accounts (expense, liability, cash)
alembic/                migrations
tests/
  payments/             payment service tests (authorize, idempotency, capture, refund, webhooks, card flow)
  ledger/               ledger service tests (authorization, settlement, hold, clear_hold, invariants)
  issuer/               issuer tests (auth engine, controls, settlement, lifecycle, ledger invariants)
main.py                 FastAPI app entry point
```

## Architecture patterns

- **Service/repository pattern** -- repositories handle DB I/O and return Pydantic DTOs; services own `session.commit()` / `session.rollback()`; routers handle HTTP only
- **No cross-module repository calls** -- services may call other services, never another module's repository
- **Processor abstraction** -- `PaymentProcessor` Protocol with `StripeAdapter`; swap processors via `PROCESSOR` env var
- **Double-entry ledger** -- every payment event writes balanced debit/credit entries; sum of all entries always equals zero
- **Outbox pattern** -- outbox event row written in the same DB transaction as ledger entries; Celery poller publishes to RabbitMQ separately, guaranteeing at-least-once delivery without dual-write risk
- **Issuer controls run before Stripe** -- mirrors real card network sequencing; if the issuer declines, Stripe is never called

## Issuer + acquiring flow

```
POST /payments/authorize
  1. Idempotency check
  2. issuer_auth_service.evaluate()       -- if card_id provided
       - card status check
       - check_controls() -- balance, MCC block, velocity limit
       - record IssuerAuthorization (APPROVED/DECLINED)
       - if APPROVED: record_hold() on card ledger accounts
  3. If DECLINED: raise PaymentDeclinedException (HTTP 402) -- Stripe never called
  4. processor.create_payment_intent()    -- Stripe PaymentIntent (manual capture)
  5. repository.create()                  -- payment record
  6. ledger_service.record_authorization() -- debit expense, credit liability
  7. outbox_service.publish_event()       -- payment.authorized row
  8. session.commit()                     -- single transaction covers all of the above

POST /payments/webhooks/stripe  (payment_intent.succeeded)
  1. repository.settle()                  -- payment -> SUCCEEDED
  2. ledger_service.record_settlement()   -- debit liability, credit cash
  3. issuer_settlement_service.clear_hold() -- debit pending_hold, credit available_balance
  4. outbox_service.publish_event()       -- payment.settled row
  5. session.commit()
```

## Async pipeline

```
DB outbox_events table
  <- written atomically with ledger entries in the payment transaction

Celery Beat (every 10s)
  -> fires poll_and_publish task

Celery Worker (outbox_poller)
  -> queries pending outbox rows
  -> publishes each to RabbitMQ "payments" topic exchange (routing_key = event_type)
  -> marks rows published/failed

RabbitMQ payments exchange
  -> payments.fraud queue       (bound to payment.authorized)
  -> payments.notifications     (bound to payment.authorized, .settled, .refunded)
  -> payments.reporting         (bound to payment.authorized, .settled, .refunded)

Consumers (long-running async processes)
  -> each reads from its own durable queue, processes one message at a time (prefetch=1)

Celery Beat (every 24h)
  -> fires run_reconciliation task
  -> queries settled payments, calls stripe.PaymentIntent.retrieve() for each
  -> logs mismatches
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

# Seed platform ledger accounts
poetry run python -m scripts.seed

# Start the API
poetry run uvicorn main:app --reload
```

Runs at `http://localhost:8000`.

## Running workers

```bash
# Celery worker (outbox poller + reconciliation)
poetry run celery -A workers.celery_app worker --loglevel=info

# Celery Beat scheduler
poetry run celery -A workers.celery_app beat --loglevel=info

# Consumers (each in a separate terminal)
poetry run python -m workers.consumers.payments.fraud
poetry run python -m workers.consumers.payments.notifications
poetry run python -m workers.consumers.payments.reporting
```

## Running tests

```bash
poetry run pytest
```

Requires a running PostgreSQL instance at `postgresql+asyncpg://postgres:postgres@localhost:5432/payments_test`. Each test function creates and drops all tables via `Base.metadata.create_all/drop_all`.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/payments/authorize` | Authorize -- runs issuer controls, creates Stripe PaymentIntent, writes ledger entries |
| POST | `/payments/capture` | Capture an authorized payment |
| POST | `/payments/refund` | Refund a captured payment |
| POST | `/payments/webhooks/stripe` | Stripe webhook receiver |
| POST | `/issuer/cardholders` | Create a cardholder |
| POST | `/issuer/cards` | Issue a card with credit limit |
| GET  | `/issuer/cards/{id}/balance` | Get available credit and pending holds for a card |
| POST | `/issuer/cards/{id}/controls/mcc-blocks` | Block an MCC category on a card |
| POST | `/issuer/cards/{id}/controls/velocity-rules` | Add a velocity spend limit to a card |
| GET  | `/_live` | Liveness check |

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `STRIPE_SECRET_KEY` | Yes | Stripe secret key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Yes | Webhook signing secret (`whsec_...`) |
| `DATABASE_URL` | No | PostgreSQL connection string |
| `REDIS_URL` | No | Redis connection string |
| `RABBITMQ_URL` | No | RabbitMQ connection string |
| `PROCESSOR` | No | Payment processor (default: `stripe`) |
| `EXPENSE_ACCOUNT_ID` | No | Platform ledger expense account UUID |
| `LIABILITY_ACCOUNT_ID` | No | Platform ledger liability account UUID |
| `CASH_ACCOUNT_ID` | No | Platform ledger cash account UUID |
