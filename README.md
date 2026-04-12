# payments-platform

Monorepo for a full payments simulation stack:
- acquiring (authorize/capture/refund + Stripe webhooks)
- issuer (cardholders/cards, controls, auth decisions, hold lifecycle)
- bills (payees, recurring/manual bill execution)
- observability (fraud, notifications, reporting, reconciliation)
- web dashboard (Next.js 16 + SWR) covering all of the above

## Status snapshot (April 11, 2026)

Core implementation is complete across API, workers, and dashboard UI.

- Backend domains are implemented and wired.
- Async outbox + RabbitMQ consumers are running with DLQ support.
- ACH bill processor + settlement job are implemented.
- Dashboard routes are implemented for payments, issuing, bills, and observability.

## Tech stack

| Layer | Stack |
| --- | --- |
| API | Python 3.13, FastAPI, SQLAlchemy (async), Alembic, Pydantic v2, Poetry |
| Web | Next.js 16 App Router, TypeScript, Tailwind v4, SWR, Bun |
| Infra | PostgreSQL, Redis, RabbitMQ, Docker Compose |
| Workers | Celery + Celery Beat, aio-pika |
| Processors | Stripe (card checkout) + ACH adapter (bill execution path) |

## Full end-to-end flow (highlight)

### Flow A: card checkout (`/` -> `/payments` -> observability)
1. Web calls `POST /payments/authorize` with amount/currency (and optional `card_id`).
2. If `card_id` is provided, issuer controls run first (balance, MCC block, velocity).
3. Payment + ledger authorization entries + outbox event are committed atomically.
4. Web gets `client_secret` and confirms using Stripe PaymentElement.
5. Stripe webhook `POST /payments/webhooks/stripe` settles payment.
6. Settlement writes ledger entries, clears issuer hold (when applicable), and enqueues outbox events.
7. Outbox poller publishes events to RabbitMQ.
8. Consumers persist fraud, notifications, and reporting projections.
9. Dashboard reflects results via:
   - `/payments` and `/payments/[id]`
   - `/fraud`
   - `/reporting`
   - `/reconciliation`

### Flow B: bill execution (`/payees` + `/bills`)
1. Create payee via `POST /payees`.
2. Create bill via `POST /bills` (optionally linked to a card).
3. Bill executes by:
   - scheduler job (every 5 minutes), or
   - manual trigger `POST /bills/{id}/execute`.
4. Execution runs through payment authorization path and creates `BillPayment`.
5. `bill.executed` / `bill.failed` outbox events are published.
6. Notifications + reporting consumers persist downstream records.
7. Dashboard surfaces lifecycle on:
   - `/bills`, `/bills/new`, `/bills/[id]`
   - `/reporting`

## Monorepo structure

```text
payments-platform/
  apps/
    api/               FastAPI app + workers + tests + alembic
    web/               Next.js dashboard + checkout
  docker-compose.yml   Postgres, Redis, RabbitMQ, API, workers, consumers
  CLAUDE.md            repo context + endpoint inventory for coding sessions
```

## Quick start

### 1) Start backend stack

From repo root:

```bash
export STRIPE_SECRET_KEY=sk_test_...
export STRIPE_WEBHOOK_SECRET=whsec_...
docker compose up --build
```

This starts:
- `api` on `http://localhost:8000`
- `postgres` on `localhost:5432`
- `redis` on `localhost:6379`
- `rabbitmq` on `localhost:5672` (`15672` mgmt UI)
- Celery beat + workers + RabbitMQ consumers

### 2) Run API migrations + seed (first run)

```bash
cd apps/api
poetry install
poetry run alembic upgrade head
poetry run python -m scripts.seed
```

### 3) Run web app

```bash
cd apps/web
bun install
echo 'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...' > .env.local
bun dev
```

Web runs at `http://localhost:3000`.

### 4) Forward Stripe webhooks

```bash
stripe listen --forward-to localhost:8000/payments/webhooks/stripe
```

## Route map (web)

- `/` overview + checkout
- `/payments`, `/payments/[id]`
- `/cards`, `/cards/[id]`
- `/cardholders`
- `/payees`
- `/bills`, `/bills/new`, `/bills/[id]`
- `/fraud`
- `/reporting`
- `/reconciliation`

## API endpoint groups

- Payments: `/payments/*`
- Issuer: `/issuer/*`
- Bills: `/bills/*`
- Payees: `/payees/*`
- Observability:
  - `/fraud/signals`
  - `/reporting/summary`
  - `/reconciliation/runs`
  - `/reconciliation/discrepancies`
- Health: `/_live`

For full endpoint details and response-shape notes, see:
- [`apps/api/README.md`](./apps/api/README.md)
- [`CLAUDE.md`](./CLAUDE.md)

## Validation commands

### Web (`apps/web`)

```bash
bun run prettier --write
bunx tsc --noEmit
bun run test:unit
bun run build
```

### API (`apps/api`)

```bash
poetry run pytest
```
