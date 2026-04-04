# payments-platform

A payments platform monorepo implementing acquiring-side payment orchestration, issuer-side card simulation, and a full async observability pipeline. Built with FastAPI, Stripe, a double-entry ledger, RabbitMQ, and Celery.

## Tech stack

| Layer | Stack |
|-------|-------|
| API | Python 3.13, FastAPI, SQLAlchemy (async), Alembic, asyncpg, Pydantic v2, Poetry |
| Web | Next.js 16 (App Router), TypeScript, Tailwind CSS v4, Bun, Stripe.js |
| Infra | PostgreSQL, Redis, RabbitMQ, Docker Compose |
| Payments | Stripe PaymentIntents (manual capture) |
| Workers | Celery + Celery Beat, aio-pika |

## What this is

Three tracks running together:

**Acquiring track** -- integrates with Stripe to authorize, capture, and refund payments. Every payment event is backed by double-entry ledger entries so debits always equal credits.

**Issuer track** -- simulates the card network side. When a payment is authorized with a `card_id`, the issuer engine runs spend controls (balance check, MCC block, velocity limits) and decides to approve or decline before Stripe is ever called. On settlement, issuer holds are cleared atomically.

**Observability pipeline** -- every payment lifecycle event is published to RabbitMQ via the outbox pattern. Three consumers run independently and persist fraud signals, notification logs, and reporting events. A nightly reconciliation job checks settled payments against Stripe and records any discrepancies.

## End-to-end flow

### Authorization
1. Frontend calls `POST /payments/authorize` with amount, currency, and optional `card_id`
2. If `card_id` provided: issuer evaluates controls (balance, MCC block, velocity) -- declines with HTTP 402 if any check fails
3. Stripe PaymentIntent created (manual capture mode)
4. Payment record + ledger authorization entries written atomically
5. Outbox event (`payment.authorized`) written in the same transaction
6. `client_secret` returned to frontend

### Payment confirmation
7. Frontend renders Stripe Elements using `client_secret`
8. User enters card details and submits -- Stripe.js confirms the intent
9. Stripe fires `payment_intent.succeeded` webhook to `POST /payments/webhooks/stripe`
10. Webhook handler: settles payment record + writes ledger settlement entries + clears issuer hold + writes outbox event (`payment.settled`) -- all in one transaction

### Async side effects
11. Celery Beat fires every 10 seconds -- outbox poller queries pending rows, publishes to RabbitMQ `payments` topic exchange
12. Three consumers process events independently from their own durable queues:
    - `payments.fraud` -- scores risk on `payment.authorized`, persists `FraudSignal` row
    - `payments.notifications` -- resolves cardholder email if `card_id` present, delivers via `NotificationSender`, persists `NotificationLog` row
    - `payments.reporting` -- persists `ReportingEvent` row for daily volume aggregation

### Reconciliation
13. Celery Beat fires nightly -- reconciliation job creates a `ReconciliationRun`, checks each settled payment against Stripe, writes `ReconciliationDiscrepancy` rows for mismatches, publishes `reconciliation.mismatch` outbox event per mismatch so the notifications consumer can alert

## Project structure

```
payments-platform/
  apps/
    api/                      FastAPI backend
      app/
        payments/             payment processing (authorize, capture, refund, webhooks)
        ledger/               double-entry ledger (accounts, transactions, entries)
        fraud/                FraudSignal model + GET /fraud/signals
        notifications/        NotificationLog model + NotificationSender Protocol/adapters
        reporting/            ReportingEvent model + GET /reporting/summary
        reconciliation/       ReconciliationRun + Discrepancy models + GET endpoints
        issuer/
          auth/               evaluate() -- controls engine, IssuerAuthorization
          cards/              Cardholder + Card models, per-card ledger accounts
          controls/           MCCBlock, VelocityRule, check_controls()
          settlement/         clear_hold() -- clears issuer hold on settlement
        outbox/               OutboxEvent model, publish_event(), repository
      shared/                 DB, processors, notification senders, enums, exceptions, settings, logger
      workers/
        exchanges.py          PAYMENTS_EXCHANGE, ISSUER_EXCHANGE constants
        producers/payments/   outbox_poller -- reads DB, publishes to RabbitMQ
        consumers/payments/   fraud, notifications, reporting consumers
        jobs/payments/        reconciliation -- nightly Stripe comparison
      alembic/                migrations
      scripts/                seed scripts
      tests/                  pytest suite (fraud, notifications, reporting, reconciliation, payments, ledger, issuer)
      Dockerfile              shared image for api + all worker services
    web/                      Next.js dummy frontend for E2E testing
  docker-compose.yml          full stack: postgres, redis, rabbitmq, api, workers, consumers
```

## Getting started

### Option A -- Full stack via Docker Compose (recommended)

```bash
# Set your Stripe test keys
export STRIPE_SECRET_KEY=sk_test_...
export STRIPE_WEBHOOK_SECRET=whsec_...

docker compose up --build
```

This starts everything: postgres, redis, rabbitmq, api (port 8000), celery-beat, outbox-poller, consumer-fraud, consumer-notifications, consumer-reporting.

### Option B -- Local development

#### Prerequisites
- Python 3.13+, Poetry
- Bun
- Docker and Docker Compose
- Stripe test account + Stripe CLI

#### 1. Start infrastructure

```bash
docker compose up -d postgres redis rabbitmq
```

#### 2. Set up the API

```bash
cd apps/api
cp .env.example .env   # fill in STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET
poetry install
poetry run alembic upgrade head
poetry run python scripts/seed.py
```

#### 3. Set up the frontend

```bash
cd apps/web
bun install
echo 'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...' > .env.local
```

#### 4. Start API and frontend

```bash
# API on :8000
cd apps/api && poetry run uvicorn main:app --reload

# Frontend on :3000
cd apps/web && bun dev
```

#### 5. Forward Stripe webhooks

```bash
stripe listen --forward-to localhost:8000/payments/webhooks/stripe
```

Copy the printed `whsec_...` into `apps/api/.env` as `STRIPE_WEBHOOK_SECRET` and restart the API.

#### 6. Start async workers

```bash
# from apps/api/

# Celery worker (runs outbox poller + reconciliation tasks)
poetry run celery -A workers.celery_app worker --loglevel=info

# Celery Beat scheduler
poetry run celery -A workers.celery_app beat --loglevel=info

# RabbitMQ consumers (each in a separate terminal)
poetry run python -m workers.consumers.payments.fraud
poetry run python -m workers.consumers.payments.notifications
poetry run python -m workers.consumers.payments.reporting
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/payments/authorize` | Authorize payment -- runs issuer controls if card_id provided, creates Stripe PaymentIntent, writes ledger entries |
| POST | `/payments/capture` | Capture an authorized payment |
| POST | `/payments/refund` | Refund a captured payment |
| POST | `/payments/webhooks/stripe` | Stripe webhook receiver |
| GET  | `/fraud/signals` | List fraud signals with optional `risk_level` filter |
| GET  | `/reporting/summary` | Daily volume grouped by event_type and currency |
| GET  | `/reconciliation/runs` | List reconciliation job runs |
| GET  | `/reconciliation/discrepancies` | List discrepancies with optional `run_id` filter |
| POST | `/issuer/cardholders` | Create a cardholder |
| POST | `/issuer/cards` | Issue a card with credit limit |
| GET  | `/issuer/cards/{id}/balance` | Get available credit and pending holds |
| POST | `/issuer/cards/{id}/controls/mcc-blocks` | Block an MCC category |
| POST | `/issuer/cards/{id}/controls/velocity-rules` | Add a velocity spend limit |
| GET  | `/_live` | Liveness check |

## Environment variables

### API (`apps/api/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STRIPE_SECRET_KEY` | Yes | -- | Stripe secret key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Yes | -- | Stripe webhook signing secret (`whsec_...`) |
| `DATABASE_URL` | No | postgres localhost | PostgreSQL connection string |
| `REDIS_URL` | No | redis localhost | Redis connection string |
| `RABBITMQ_URL` | No | rabbitmq localhost | RabbitMQ connection string |
| `PROCESSOR` | No | `stripe` | Payment processor |
| `EXPENSE_ACCOUNT_ID` | No | preset UUID | Platform ledger expense account |
| `LIABILITY_ACCOUNT_ID` | No | preset UUID | Platform ledger liability account |
| `CASH_ACCOUNT_ID` | No | preset UUID | Platform ledger cash account |
| `NOTIFICATION_SENDER` | No | `stub` | `stub` / `smtp` / `twilio` |
| `SMTP_HOST` | No | -- | Required when `NOTIFICATION_SENDER=smtp` |
| `SMTP_PORT` | No | `587` | SMTP port |
| `SMTP_USER` | No | -- | SMTP username |
| `SMTP_PASSWORD` | No | -- | SMTP password |
| `SMTP_FROM` | No | `noreply@...` | From address |
| `TWILIO_ACCOUNT_SID` | No | -- | Required when `NOTIFICATION_SENDER=twilio` |
| `TWILIO_AUTH_TOKEN` | No | -- | Twilio auth token |
| `TWILIO_FROM_NUMBER` | No | -- | Twilio from number |

### Web (`apps/web/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Yes | Stripe publishable key (`pk_test_...`) |

## Running tests

```bash
cd apps/api && poetry run pytest
```
