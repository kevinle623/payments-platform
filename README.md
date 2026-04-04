# payments-platform

A payments platform monorepo implementing acquiring-side payment orchestration and issuer-side card simulation. Built with FastAPI, Stripe, a double-entry ledger, and a full async event pipeline via Celery and RabbitMQ.

## Tech stack

| Layer | Stack |
|-------|-------|
| API | Python 3.13, FastAPI, SQLAlchemy (async), Alembic, asyncpg, Pydantic v2, Poetry |
| Web | Next.js 16 (App Router), TypeScript, Tailwind CSS v4, Bun, Stripe.js |
| Infra | PostgreSQL, Redis, RabbitMQ, Docker Compose |
| Payments | Stripe PaymentIntents (manual capture) |
| Workers | Celery + Celery Beat, aio-pika |

## What this is

Two tracks running together:

**Acquiring track** -- integrates with Stripe to authorize, capture, and refund payments. Every payment event is backed by double-entry ledger entries so debits always equal credits.

**Issuer track** -- simulates the card network side. When a payment is authorized with a `card_id`, the issuer engine runs spend controls (balance check, MCC block, velocity limits) and decides to approve or decline before Stripe is ever called. On settlement, issuer holds are cleared atomically.

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
    - `payments.fraud` -- scores risk on `payment.authorized`
    - `payments.notifications` -- sends simulated notifications on all payment events
    - `payments.reporting` -- logs analytics entries on all payment events

### Reconciliation
13. Celery Beat fires nightly -- reconciliation job queries settled payments and compares against Stripe, logging any status mismatches

## Project structure

```
payments-platform/
  apps/
    api/                      FastAPI backend (see apps/api/README.md)
      app/
        payments/             payment processing (authorize, capture, refund, webhooks)
        ledger/               double-entry ledger (accounts, transactions, entries)
        issuer/
          auth/               evaluate() -- controls engine, IssuerAuthorization
          cards/              Cardholder + Card models, per-card ledger accounts
          controls/           MCCBlock, VelocityRule, check_controls()
          settlement/         clear_hold() -- clears issuer hold on settlement
        outbox/               OutboxEvent model, publish_event(), repository
      shared/                 DB, processors, enums, exceptions, settings, logger
      workers/
        exchanges.py          PAYMENTS_EXCHANGE, ISSUER_EXCHANGE constants
        producers/payments/   outbox_poller -- reads DB, publishes to RabbitMQ
        consumers/payments/   fraud, notifications, reporting consumers
        jobs/payments/        reconciliation -- nightly Stripe comparison
      alembic/                migrations
      scripts/                seed scripts
      tests/                  pytest suite
    web/                      Next.js dummy frontend for E2E testing
  docker-compose.yml          Postgres, Redis, RabbitMQ
  Makefile                    common dev commands
```

## Getting started

### Prerequisites

- Python 3.13+, Poetry
- Bun
- Docker and Docker Compose
- Stripe test account + Stripe CLI

### 1. Start infrastructure

```bash
make infra
```

### 2. Set up the API

```bash
cd apps/api
cp .env.example .env   # fill in STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET
poetry install
make migrate
make seed
```

### 3. Set up the frontend

```bash
cd apps/web
bun install
echo 'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY' > .env.local
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000' >> .env.local
```

### 4. Start API and frontend

```bash
make dev
```

Or individually:

```bash
make api   # FastAPI on :8000
make web   # Next.js on :3000
```

### 5. Forward Stripe webhooks

```bash
stripe listen --forward-to localhost:8000/payments/webhooks/stripe
```

Copy the printed `whsec_...` into `apps/api/.env` as `STRIPE_WEBHOOK_SECRET` and restart the API.

### 6. Start async workers (optional)

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

## Make targets

| Target | Description |
|--------|-------------|
| `make infra` | Start Postgres, Redis, RabbitMQ |
| `make infra-down` | Stop infrastructure |
| `make infra-reset` | Stop infrastructure and destroy volumes |
| `make dev` | Start infra + API + web concurrently |
| `make api` | Start FastAPI dev server |
| `make web` | Start Next.js dev server |
| `make migrate` | Run Alembic migrations |
| `make migration` | Create a new migration (prompts for name) |
| `make downgrade` | Rollback one migration |
| `make seed` | Seed ledger accounts |
| `make test` | Run all tests |
| `make test-api` | Run pytest only |
| `make lint` | Fix lint and format |
| `make check` | Read-only lint + typecheck + tests (CI) |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/payments/authorize` | Authorize payment -- runs issuer controls if card_id provided, creates Stripe PaymentIntent, writes ledger entries |
| POST | `/payments/capture` | Capture an authorized payment |
| POST | `/payments/refund` | Refund a captured payment |
| POST | `/payments/webhooks/stripe` | Stripe webhook receiver (succeeds, refunds) |
| POST | `/issuer/cardholders` | Create a cardholder |
| POST | `/issuer/cards` | Issue a card with credit limit |
| GET  | `/issuer/cards/{id}/balance` | Get available credit and pending holds |
| POST | `/issuer/cards/{id}/controls/mcc-blocks` | Block an MCC category |
| POST | `/issuer/cards/{id}/controls/velocity-rules` | Add a velocity spend limit |
| GET  | `/_live` | Liveness check |

## Environment variables

### API (`apps/api/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `STRIPE_SECRET_KEY` | Yes | Stripe secret key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret (`whsec_...`) |
| `DATABASE_URL` | No | PostgreSQL connection string |
| `REDIS_URL` | No | Redis connection string |
| `RABBITMQ_URL` | No | RabbitMQ connection string |
| `PROCESSOR` | No | Payment processor (default: `stripe`) |
| `EXPENSE_ACCOUNT_ID` | No | Platform ledger expense account UUID |
| `LIABILITY_ACCOUNT_ID` | No | Platform ledger liability account UUID |
| `CASH_ACCOUNT_ID` | No | Platform ledger cash account UUID |

### Web (`apps/web/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Yes | Stripe publishable key (`pk_test_...`) |
| `NEXT_PUBLIC_API_URL` | No | API base URL (default: `http://localhost:8000`) |
