# payments-platform/apps/api

FastAPI backend implementing acquiring-side payment orchestration, issuer-side card simulation, and bill payments, backed by a double-entry ledger and a Celery + RabbitMQ async event pipeline.

Current status (April 5, 2026): bill payments implementation is live in code and covered by `tests/payees` and `tests/bills`; migration `637e756014ea_add_payees_and_bills_tables.py` is generated and applied; dashboard backend read APIs (`GET /payments`, `GET /payments/{id}`, `GET /issuer/cards`, `GET /issuer/cardholders`, `GET /issuer/cards/{id}/authorizations`) are implemented and tested; downstream `bill.*` consumer subscriptions for notifications/reporting are implemented.

## Immediate next priorities

1. Add integration tests for `bill.*` consumer handling and persistence.
2. Add dead-letter/retry topology for RabbitMQ consumer queues.
3. Support web dashboard pages for bills using current bill/payee APIs.
4. Start ACH adapter + bank-account domain work for bill payment routing.

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
  payees/               payee CRUD for bill payments
    router.py           payee endpoints (create/list/get)
    service.py          payee business logic
    repository.py       payee DB access
    models.py           Payee ORM model
    schemas.py          payee request/response DTOs
  bills/                bill scheduling + execution
    router.py           bill endpoints (create/list/get/update/execute)
    service.py          execute_bill(), frequency advancement, outbox writes
    repository.py       bill + bill_payment DB access
    models.py           Bill + BillPayment ORM models
    schemas.py          bill request/response DTOs
  ledger/               double-entry ledger
    service.py          record_authorization(), record_settlement(), record_hold(), record_clear_hold()
    repository.py       accounts, transactions, entries
    models.py           Account, Transaction, Entry ORM models
  fraud/                FraudSignal model + listing API
  notifications/        NotificationLog model + sender adapters
  reporting/            ReportingEvent model + summary API
  reconciliation/       ReconciliationRun + discrepancy models + listing API
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
  celery_app.py         Celery app, broker config, Beat schedules (outbox 10s, bills 5m, hold expiry 1h, reconciliation 24h), queue routes (outbox/jobs)
  producers/
    outbox_poller.py    Celery task: polls pending outbox rows, publishes to RabbitMQ (payments/issuer fanout by event prefix)
  consumers/
    base.py             generic run_consumer/start (exchange, queue, routing_keys, handler)
    payments/
      fraud.py          payment.authorized -> persists FraudSignal
      notifications.py  payment.* + bill.* + reconciliation.mismatch -> NotificationLog + sender delivery
      reporting.py      payment.* + bill.* -> persists ReportingEvent
    issuer/
      card_activity.py  card.issued, hold.created, hold.cleared activity logging
      risk.py           auth.approved, auth.declined risk logging
  jobs/
    bills/
      scheduler.py      every 5 minutes: finds due active bills, executes each
      executor.py       execution wrapper used by scheduler
    payments/
      reconciliation.py nightly Celery task: compares settled payments against Stripe
    issuer/
      hold_expiry.py    hourly stale hold expiry job with double-clear prevention
scripts/
  seed.py               seeds platform ledger accounts (expense, liability, cash)
alembic/                migrations
tests/
  payees/               payee service tests
  bills/                bill service + scheduler tests
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
Celery Beat (every 5m)
  -> fires run_bill_scheduler task
Celery Beat (every 1h)
  -> fires run_hold_expiry task

Celery Worker (queue: outbox)
  -> queries pending outbox rows
  -> publishes each to RabbitMQ "payments" or "issuer" topic exchange (routing_key = event_type)
  -> marks rows published/failed

Celery Worker (queue: jobs)
  -> runs bill scheduler, hold expiry, and reconciliation tasks

RabbitMQ payments exchange
  -> payments.fraud queue       (bound to payment.authorized)
  -> payments.notifications     (bound to payment.*, bill.*, reconciliation.mismatch)
  -> payments.reporting         (bound to payment.*, bill.*)

RabbitMQ issuer exchange
  -> issuer.card_activity queue (bound to card.issued, hold.created, hold.cleared)
  -> issuer.risk queue          (bound to auth.approved, auth.declined)

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
# Celery worker (outbox queue)
poetry run celery -A workers.celery_app worker --loglevel=info -Q outbox

# Celery worker (jobs queue: bills + hold expiry + reconciliation)
poetry run celery -A workers.celery_app worker --loglevel=info -Q jobs

# Celery Beat scheduler
poetry run celery -A workers.celery_app beat --loglevel=info

# Consumers (each in a separate terminal)
poetry run python -m workers.consumers.payments.fraud
poetry run python -m workers.consumers.payments.notifications
poetry run python -m workers.consumers.payments.reporting
poetry run python -m workers.consumers.issuer.card_activity
poetry run python -m workers.consumers.issuer.risk
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
| POST | `/payees` | Create a payee |
| GET  | `/payees` | List payees |
| GET  | `/payees/{id}` | Get payee detail |
| POST | `/bills` | Create/schedule a bill |
| GET  | `/bills` | List bills (optional status filter) |
| GET  | `/bills/{id}` | Get bill detail + execution history |
| POST | `/bills/{id}/execute` | Manually execute a bill |
| PATCH | `/bills/{id}` | Update bill (pause/resume/amount/frequency/date/card) |
| POST | `/issuer/cardholders` | Create a cardholder |
| GET  | `/issuer/cardholders/{cardholder_id}` | Get cardholder detail |
| POST | `/issuer/cards` | Issue a card with credit limit |
| GET  | `/issuer/cards/{id}` | Get card detail |
| GET  | `/issuer/cards/{id}/balance` | Get available credit and pending holds for a card |
| GET  | `/issuer/cards/{id}/controls/mcc-blocks` | List MCC blocks for a card |
| POST | `/issuer/cards/{id}/controls/mcc-blocks` | Block an MCC category on a card |
| DELETE | `/issuer/cards/{id}/controls/mcc-blocks/{mcc}` | Remove an MCC block |
| GET  | `/issuer/cards/{id}/controls/velocity-rules` | List velocity rules for a card |
| POST | `/issuer/cards/{id}/controls/velocity-rules` | Add a velocity spend limit to a card |
| DELETE | `/issuer/cards/{id}/controls/velocity-rules/{rule_id}` | Remove a velocity rule |
| GET  | `/fraud/signals` | List fraud signals |
| GET  | `/reporting/summary` | Reporting summary grouped by date/event/currency |
| GET  | `/reconciliation/runs` | List reconciliation runs |
| GET  | `/reconciliation/discrepancies` | List reconciliation discrepancies |
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
