# apps/api

FastAPI backend for payments-platform, including:
- acquiring payment orchestration
- issuer simulation (cards + controls + auth decisions)
- bill scheduling/execution
- outbox + RabbitMQ consumer pipeline
- observability projections (fraud, notifications, reporting, reconciliation)

## Status snapshot (April 11, 2026)

Core backend implementation is complete and wired end-to-end with workers.

## Stack

- Python 3.13
- FastAPI
- SQLAlchemy async + asyncpg
- Alembic
- Celery + Celery Beat
- aio-pika
- Poetry

## API modules

```text
app/
  payments/        authorize/capture/refund/webhooks + list/detail
  payees/          payee CRUD
  bills/           bill CRUD + execute + execution history
  issuer/
    cards/         cardholders/cards/balance/authorizations
    controls/      mcc-block and velocity controls
    auth/          issuer authorization records
    settlement/    hold clearing on settlement
  ledger/          double-entry accounting service
  outbox/          transactional event staging
  fraud/           fraud signal projection + list endpoint
  notifications/   notification log projection + sender abstraction
  reporting/       reporting event projection + summary endpoint
  reconciliation/  run/discrepancy projection + endpoints
```

## Worker topology

```text
workers/
  celery_app.py
  producers/outbox_poller.py
  jobs/
    bills/scheduler.py
    payments/ach_settlement.py
    payments/reconciliation.py
    issuer/hold_expiry.py
  consumers/payments/{fraud,notifications,reporting}.py
  consumers/issuer/{card_activity,risk}.py
```

Celery Beat schedules:
- outbox poller: every 10s
- bill scheduler: every 5m
- ACH settlement: every 2m
- hold expiry: every 1h
- reconciliation: every 24h

## Endpoint inventory

### Payments

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/payments` | list (status, limit, offset) |
| `GET` | `/payments/{payment_id}` | detail with payment + ledger transactions + outbox events + issuer auth |
| `POST` | `/payments/authorize` | creates intent + ledger authorization + outbox event |
| `POST` | `/payments/capture` | capture authorized payment |
| `POST` | `/payments/refund` | refund payment |
| `POST` | `/payments/webhooks/stripe` | webhook ingest |

### Payees + bills

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/payees` | create payee |
| `GET` | `/payees` | list payees |
| `GET` | `/payees/{payee_id}` | payee detail |
| `POST` | `/bills` | create bill |
| `GET` | `/bills` | list bills (status, limit, offset) |
| `GET` | `/bills/{bill_id}` | bill detail + bill payments |
| `PATCH` | `/bills/{bill_id}` | update bill |
| `POST` | `/bills/{bill_id}/execute` | manual execution |

### Issuer

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/issuer/cardholders` | create cardholder |
| `GET` | `/issuer/cardholders` | list cardholders |
| `GET` | `/issuer/cardholders/{cardholder_id}` | cardholder detail |
| `POST` | `/issuer/cards` | create card |
| `GET` | `/issuer/cards` | list cards |
| `GET` | `/issuer/cards/{card_id}` | card detail |
| `GET` | `/issuer/cards/{card_id}/balance` | available credit + pending holds |
| `GET` | `/issuer/cards/{card_id}/authorizations` | issuer auth history |
| `GET` | `/issuer/cards/{card_id}/controls/mcc-blocks` | list MCC blocks |
| `POST` | `/issuer/cards/{card_id}/controls/mcc-blocks` | add MCC block |
| `DELETE` | `/issuer/cards/{card_id}/controls/mcc-blocks/{mcc}` | remove MCC block |
| `GET` | `/issuer/cards/{card_id}/controls/velocity-rules` | list velocity rules |
| `POST` | `/issuer/cards/{card_id}/controls/velocity-rules` | add velocity rule |
| `DELETE` | `/issuer/cards/{card_id}/controls/velocity-rules/{rule_id}` | remove velocity rule |

### Observability

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/fraud/signals` | risk-level filtered list |
| `GET` | `/reporting/summary` | grouped by date/event_type/currency |
| `GET` | `/reconciliation/runs` | run history |
| `GET` | `/reconciliation/discrepancies` | discrepancies (optional `run_id`) |
| `GET` | `/_live` | health |

## Local setup

```bash
poetry install
cp .env.example .env
poetry run alembic upgrade head
poetry run python -m scripts.seed
poetry run uvicorn main:app --reload
```

## Running workers (manual mode)

```bash
# queue: outbox
poetry run celery -A workers.celery_app worker --loglevel=info -Q outbox

# queue: jobs
poetry run celery -A workers.celery_app worker --loglevel=info -Q jobs

# beat
poetry run celery -A workers.celery_app beat --loglevel=info

# consumers
poetry run python -m workers.consumers.payments.fraud
poetry run python -m workers.consumers.payments.notifications
poetry run python -m workers.consumers.payments.reporting
poetry run python -m workers.consumers.issuer.card_activity
poetry run python -m workers.consumers.issuer.risk
```

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | No | Postgres DSN |
| `REDIS_URL` | No | Redis URL |
| `RABBITMQ_URL` | No | RabbitMQ URL |
| `PROCESSOR` | No | checkout/card payment processor (`stripe` default) |
| `BILL_PROCESSOR` | No | bill execution processor (`ach` default) |
| `STRIPE_SECRET_KEY` | Required for Stripe | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Required for Stripe webhooks | Stripe webhook signing secret |
| `EXPENSE_ACCOUNT_ID` | No | platform ledger UUID |
| `LIABILITY_ACCOUNT_ID` | No | platform ledger UUID |
| `CASH_ACCOUNT_ID` | No | platform ledger UUID |
| `NOTIFICATION_SENDER` | No | `stub` / `smtp` / `twilio` |
| `SMTP_*`, `TWILIO_*` | Conditional | sender adapter config |

## Tests

```bash
poetry run pytest
```
