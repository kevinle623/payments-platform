# payments-platform

A payments platform monorepo implementing double-entry ledger accounting, processor abstraction, idempotency, and Stripe webhook handling -- with a Next.js frontend for end-to-end payment testing.

## Tech stack

| Layer | Stack |
|-------|-------|
| **API** | Python 3.13, FastAPI, SQLAlchemy (async), Alembic, asyncpg, Pydantic v2, Poetry |
| **Web** | Next.js 16 (App Router), TypeScript, Tailwind CSS v4, Bun, Stripe.js |
| **Infra** | PostgreSQL, Redis, RabbitMQ (Docker Compose) |
| **Payments** | Stripe (PaymentIntents with manual capture) |

## Project structure

```
payments-platform/
  apps/
    api/                  FastAPI backend
      app/
        payments/         payment processing (authorize, capture, refund, webhooks)
        ledger/           double-entry ledger (transactions, entries, accounts)
      shared/             cross-cutting: DB, processors, enums, exceptions, config
      alembic/            database migrations
      scripts/            seed scripts
      tests/              pytest test suite
      main.py             app entry point
    web/                  Next.js frontend
      src/
        app/              App Router pages
        components/       React components (CheckoutForm)
  docker-compose.yml      PostgreSQL, Redis, RabbitMQ
```

## Getting started

### Prerequisites

- Python 3.13+
- [Poetry](https://python-poetry.org/)
- [Bun](https://bun.sh/)
- Docker & Docker Compose
- A [Stripe](https://stripe.com/) test account

### 1. Start infrastructure

```bash
docker compose up -d
```

### 2. Set up the API

```bash
cd apps/api

# Copy env and fill in your Stripe keys
cp .env.example .env

# Install dependencies
poetry install

# Run migrations
poetry run alembic upgrade head

# Seed ledger accounts
poetry run python -m scripts.seed

# Start the server
poetry run uvicorn main:app --reload
```

The API runs at `http://localhost:8000`.

### 3. Set up the frontend

```bash
cd apps/web

# Install dependencies
bun install

# Add your Stripe publishable key
echo 'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE' > .env.local

# Start the dev server
bun dev
```

The frontend runs at `http://localhost:3000`.

### 4. Forward Stripe webhooks (for local testing)

```bash
stripe listen --forward-to localhost:8000/payments/webhooks/stripe
```

Copy the webhook signing secret (`whsec_...`) into `apps/api/.env` as `STRIPE_WEBHOOK_SECRET`.

## End-to-end payment flow

1. Open `http://localhost:3000`
2. Click **Authorize Payment** -- the frontend calls `POST /payments/authorize` and receives a `client_secret`
3. Stripe Elements renders a card form
4. Enter test card `4242 4242 4242 4242` (any future expiry, any CVC)
5. Click **Pay now** -- Stripe.js confirms the payment intent
6. Stripe fires a `payment_intent.succeeded` webhook to the API
7. The webhook handler settles the payment record and writes ledger settlement entries
8. Full double-entry lifecycle complete

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/payments/authorize` | Create a PaymentIntent and ledger authorization entries |
| `POST` | `/payments/capture` | Capture an authorized payment |
| `POST` | `/payments/refund` | Refund a captured payment |
| `POST` | `/payments/webhooks/stripe` | Stripe webhook receiver |
| `GET` | `/_live` | Liveness check |

## Architecture highlights

- **Double-entry ledger** -- every payment event (authorization, settlement) writes balanced debit/credit entries that sum to zero
- **Processor abstraction** -- `PaymentProcessor` Protocol with `StripeAdapter` implementation and a factory; adding a new processor means writing one adapter
- **Idempotency** -- duplicate authorize requests return the existing result without hitting Stripe again
- **Service/repository pattern** -- repositories return Pydantic DTOs (never ORM models), services own transaction boundaries
- **Atomic writes** -- payment record + ledger entries are written in a single DB transaction; commit or rollback together

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
