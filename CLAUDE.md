# payments-platform -- Claude Code Context

## Claude behavior rules
- Never run commands locally -- no pytest, no alembic, no poetry, no migrations, no seed scripts
- The user handles all local execution including tests, migrations, and alembic
- When changes require a migration or test run, describe what to run but do not execute it

## What this is
A payments platform monorepo with a FastAPI backend (`apps/api/`) and Next.js dummy frontend (`apps/web/`) for end-to-end Stripe payment testing. Implements double-entry ledger, processor abstraction, idempotency, Stripe webhook handling, issuer auth/controls/settlement, outbox pattern, RabbitMQ async pipeline, fraud signals, notifications, reporting, and reconciliation.

**Repo:** https://github.com/kevinle623/payments-platform

---

## Tech stack
- **API:** Python 3.13, FastAPI, SQLAlchemy (async), Alembic, asyncpg, Pydantic v2, Poetry
- **Web:** Next.js 16 (App Router), TypeScript, Tailwind CSS v4, Bun, Stripe.js + React Stripe
- **Infra:** PostgreSQL, Redis, RabbitMQ (all via Docker Compose)
- Stripe for payment processing

---

## Architecture patterns
- Functional style -- no classes except SQLAlchemy models and Pydantic schemas
- Service/repository pattern with clean DTO boundaries
- ORM models stay internal to repository layer -- never exposed outside
- Repository deserializes ORM -> Pydantic DTOs before returning to service
- Service owns transaction boundary (commit/rollback) -- repository only flushes
- Processor abstraction via Protocol in `shared/processors/base.py` with `StripeAdapter` in `shared/processors/adapters/stripe.py` and a factory in `shared/processors/factory.py`
- Notification sender abstraction via Protocol in `app/notifications/sender/base.py` with `StubSender`, `SmtpSender`, `TwilioSender` in `app/notifications/sender/adapters/` and a factory in `app/notifications/sender/factory.py`
- All domain exceptions in `shared/exceptions.py`, registered as FastAPI exception handlers in `shared/exception_handlers.py`
- `_` prefix on repository functions that return raw ORM objects or are internal only
- Public repository functions always return Pydantic DTOs
- Service maps from internal `PaymentRecord` DTO to response DTOs before returning

---

## Current module structure
```
payments-platform/              (monorepo root)
  apps/
    api/                        (FastAPI backend)
      app/
        ledger/                 -- double-entry ledger (models, schemas, repository, service, router)
        payments/               -- payment processing (models, schemas, repository, service, router)
        fraud/                  -- FraudSignal model, GET /fraud/signals, consumer persists risk signals
        notifications/          -- NotificationLog model, NotificationSender Protocol + adapters (stub/smtp/twilio)
          sender/
            base.py             -- NotificationSender Protocol
            factory.py          -- get_sender() driven by NOTIFICATION_SENDER env var
            adapters/
              stub.py           -- logs only (default)
              smtp.py           -- smtplib + asyncio.to_thread
              twilio.py         -- stub, ready to wire up
        reporting/              -- ReportingEvent model, GET /reporting/summary (daily volume by event_type + currency)
        reconciliation/         -- ReconciliationRun + ReconciliationDiscrepancy models, GET /reconciliation/runs + /discrepancies
        issuer/
          auth/                 -- evaluate(), IssuerAuthorization model, decision + decline reason
          cards/                -- Cardholder, Card models, per-card ledger accounts, balance endpoint
          controls/             -- MCCBlock, VelocityRule, check_controls() rule engine
          settlement/           -- clear_hold(), wired into handle_payment_succeeded()
        outbox/                 -- OutboxEvent model, publish_event(), repository (get_pending, mark_published, mark_failed)
        events/                 -- stub, not yet built
      shared/
        db/
          adapters/
            postgresql.py       -- async engine, session, get_db
          base.py               -- DeclarativeBase
        processors/
          adapters/
            stripe.py           -- StripeAdapter
            braintree.py        -- stub
          base.py               -- PaymentProcessor Protocol, normalized DTOs
          factory.py            -- get_processor() based on PROCESSOR setting
        enums/
          currency.py           -- Currency StrEnum
          processor.py          -- SupportedProcessorType StrEnum
          notification_sender.py -- SupportedNotificationSender StrEnum (stub/smtp/twilio)
        settings.py             -- environ.get() based config (includes SMTP + Twilio + NOTIFICATION_SENDER)
        exceptions.py           -- domain exceptions
        exception_handlers.py   -- FastAPI exception handlers
        logger.py               -- get_logger(__name__)
      workers/
        celery_app.py           -- Celery app, broker config, Beat schedule (outbox every 10s, reconciliation every 24h)
        exchanges.py            -- PAYMENTS_EXCHANGE, ISSUER_EXCHANGE constants (single source of truth)
        producers/
          outbox_poller.py      -- poll_and_publish Celery task: queries pending outbox rows, fans out to payments or issuer exchange based on event type prefix
        consumers/
          base.py               -- generic run_consumer/start (exchange_name, queue_name, routing_keys, handler)
          payments/
            fraud.py            -- payment.authorized -> persists FraudSignal row
            notifications.py    -- payment.* + reconciliation.mismatch -> delivers via sender, persists NotificationLog
            reporting.py        -- payment.* -> persists ReportingEvent row
          issuer/
            card_activity.py    -- card.issued, hold.created, hold.cleared -> logs card lifecycle (future: card activity feed)
            risk.py             -- auth.approved, auth.declined -> scores issuer-side risk patterns (future: feed into fraud module)
        jobs/
          payments/
            reconciliation.py   -- nightly Celery task: creates ReconciliationRun, checks settled payments vs Stripe, writes ReconciliationDiscrepancy rows, publishes reconciliation.mismatch outbox events
          issuer/               -- future: hold expiry, dispute aging
      scripts/
        seed.py                 -- seeds ledger accounts into DB
      alembic/                  -- migrations
      tests/                    -- pytest tests
        fraud/                  -- FraudSignal service tests
        notifications/          -- NotificationLog + sender tests
        reporting/              -- ReportingEvent + summary tests
        reconciliation/         -- ReconciliationRun + discrepancy tests
        payments/               -- payment service tests
        ledger/                 -- ledger service tests
        issuer/                 -- issuer auth + settlement tests
      Dockerfile                -- shared image for api + all worker services
      main.py                   -- FastAPI app entry point
      pyproject.toml            -- Poetry dependencies
    web/                        (Next.js dummy frontend)
      src/
        app/
          layout.tsx            -- root layout
          page.tsx              -- payment page with authorize + Stripe Elements
          globals.css           -- Tailwind CSS
        components/
          CheckoutForm.tsx      -- Stripe PaymentElement form
      package.json              -- Bun/npm dependencies
  docker-compose.yml            -- full stack: postgres, redis, rabbitmq, api, celery-beat, outbox-poller, all consumers
```

---

## Key design decisions
- `SupportedProcessorType` StrEnum in `shared/enums/processor.py` -- fails fast if invalid processor set
- `SupportedNotificationSender` StrEnum in `shared/enums/notification_sender.py` -- same pattern for notification delivery
- Ledger account UUIDs hardcoded in `settings.py` as `EXPENSE_ACCOUNT_ID`, `LIABILITY_ACCOUNT_ID`, `CASH_ACCOUNT_ID` -- seeded via `scripts/seed.py`
- `stripe.PaymentIntent.create` uses `capture_method="manual"` and `automatic_payment_methods={"enabled": True, "allow_redirects": "never"}`
- Ledger service has no `session.commit()` -- caller owns the commit
- `_record_transaction` is private, `record_authorization` and `record_settlement` are the public API
- Workers (consumers + jobs) create a fresh SQLAlchemy engine per invocation via `create_async_engine(DATABASE_URL)` -- never reuse the FastAPI engine to avoid asyncio event loop mismatch
- `card_id` included in `payment.authorized` outbox payload when issuer track is used -- lets the notifications consumer resolve the cardholder email

---

## What's working

### Acquiring (Stripe)
- `POST /payments/authorize` -- creates Stripe PaymentIntent, writes payment record + ledger authorization entries atomically, returns `client_secret`
- Idempotency -- duplicate requests return existing result without hitting Stripe
- Stripe webhook handler at `POST /payments/webhooks/stripe` -- validates signature, parses event, dispatches to service
- `handle_payment_succeeded` -- settles payment record + writes ledger settlement entries
- `handle_payment_refunded` -- refunds payment record
- `GET /_live` -- liveness endpoint

### Issuer track
- Issuer auth engine -- `evaluate()` in `app/issuer/auth/service.py`, wired into `payment_service.authorize()` before Stripe call
- Issuer controls -- `MCCBlock` and `VelocityRule` models, `check_controls()` runs balance check + MCC block + velocity limit
- Issuer settlement -- `clear_hold()` wired into `handle_payment_succeeded()`
- `card_id` optional on `AuthorizeRequest` -- triggers full issuer controls when provided
- `PaymentDeclinedException` -- HTTP 402, raised when issuer declines before Stripe is called

### Async pipeline
- Outbox pattern -- `OutboxEvent` rows written atomically in same DB transaction; Celery Beat polls every 10s, publishes to RabbitMQ `payments` topic exchange
- `OutboxEventType` values: `payment.authorized`, `payment.settled`, `payment.refunded`, `reconciliation.mismatch`
- Three long-running RabbitMQ consumers (fraud, notifications, reporting) on durable queues with `prefetch_count=1`

### Iteration 2 -- real implementations (COMPLETE)
- **Fraud** -- `FraudSignal` model persisted per `payment.authorized` event; `GET /fraud/signals` with `risk_level` filter + pagination; high-value threshold $100
- **Notifications** -- `NotificationLog` persisted per payment lifecycle event; `NotificationSender` Protocol with `StubSender` (default), `SmtpSender` (smtplib), `TwilioSender` (stub); `get_sender()` factory driven by `NOTIFICATION_SENDER` env var; consumer resolves cardholder email from `card_id` in payload; `reconciliation.mismatch` handled as system alert
- **Reporting** -- `ReportingEvent` persisted per payment lifecycle event; `GET /reporting/summary` returns daily volume grouped by date + event_type + currency with optional `since`/`until` filters
- **Reconciliation** -- `ReconciliationRun` + `ReconciliationDiscrepancy` models; nightly job creates run, checks settled payments vs Stripe, writes discrepancy rows, publishes `reconciliation.mismatch` outbox events; `GET /reconciliation/runs` + `GET /reconciliation/discrepancies?run_id=`
- **Docker Compose** -- full stack containerized: `api`, `celery-beat`, `outbox-poller`, `consumer-fraud`, `consumer-notifications`, `consumer-reporting`; shared `Dockerfile` in `apps/api/`; healthchecks on postgres, redis, rabbitmq; `x-api-env` YAML anchor for DRY env vars

---

## What's not yet built
- Issuer outbox events (Task 6) -- `card.issued`, `auth.approved`, `auth.declined`, `hold.created`, `hold.cleared`
- Issuer consumers (Task 7) -- `card_activity.py`, `risk.py`
- Issuer jobs (Task 8) -- `hold_expiry.py`
- Docker Compose services for issuer workers (after Tasks 6-8)
- RabbitMQ consumer dead-lettering for failed messages
- Web UI dashboard (payment tracing, card management, issuer decisions, fraud signals)
- Bill payments module
- Real Twilio SMS delivery (stub is in place, needs `pip install twilio` + credentials)

---

## Iteration 2 -- issuer workers (NEXT)

The issuer track currently has no outbox events and no async side effects. This extends the worker infrastructure to cover issuer-side lifecycle events using the same producer/consumer/jobs pattern.

### Task 6 -- Issuer outbox events
- Add issuer event types to `OutboxEventType`: `card.issued`, `auth.approved`, `auth.declined`, `hold.created`, `hold.cleared`
- Publish `card.issued` in `issuer/cards/service.py` after card creation
- Publish `auth.approved` / `auth.declined` in `issuer/auth/service.py` after evaluate()
- Publish `hold.created` in `ledger/service.py` after record_hold()
- Publish `hold.cleared` in `issuer/settlement/service.py` after clear_hold()
- All written in the same DB transaction as the triggering operation -- same outbox pattern

### Task 7 -- Issuer consumers (`workers/consumers/issuer/`)
Add `ISSUER_EXCHANGE = "issuer"` (already in `exchanges.py`) and a dedicated issuer outbox poller that publishes to it. Then add consumers:

- `card_activity.py` -- subscribes to `card.issued`, `hold.created`, `hold.cleared`; logs card lifecycle (future: write to card activity feed)
- `risk.py` -- subscribes to `auth.approved`, `auth.declined`; scores issuer-side risk patterns (velocity of declines, unusual MCC patterns); future: feed into fraud module

Extend the existing outbox poller to fan out to multiple exchanges based on event type prefix (`payment.*` -> payments exchange, `card.*` / `auth.*` / `hold.*` -> issuer exchange).

### Task 8 -- Issuer jobs (`workers/jobs/issuer/`)
- `hold_expiry.py` -- Celery Beat job (runs hourly); finds `IssuerAuthorization` rows that are APPROVED and older than the hold expiry window (e.g. 7 days) with no corresponding settlement; calls `clear_hold()` and marks authorization as EXPIRED; prevents stale holds from permanently blocking available credit
- Future: `dispute_aging.py` -- escalate disputes that haven't been resolved within SLA

---

## Web UI dashboard -- next initiative

The current frontend is a minimal Stripe Elements checkout form. The goal is to extend it into a dev dashboard that visualizes the full payment lifecycle and lets you interact with the issuer track directly.

### Pages to build

**Payment flow (acquiring side)**
- `/` -- existing checkout page (keep as-is)
- `/payments` -- paginated list of payments with id, amount, currency, status, created_at
- `/payments/[id]` -- payment detail: status timeline, ledger entries, outbox events, issuer auth decision

**Issuer track**
- `/cards` -- list all cards with cardholder name, last four, credit limit, available credit, pending holds
- `/cards/[id]` -- card detail: balance breakdown, spend controls, recent authorizations
- `/cardholders` -- list cardholders, create new cardholder form

**Observability**
- `/fraud` -- list of fraud signals with risk level badge, payment id, amount, flagged_at
- `/reconciliation` -- list of reconciliation runs with checked/mismatch counts; expand to see discrepancies
- `/reporting` -- daily volume chart grouped by currency; event type breakdown

### Backend endpoints still needed
- `GET /payments` -- paginated list with optional status filter
- `GET /payments/{id}` -- payment detail including ledger entries and outbox events
- `GET /issuer/cards` -- list all cards
- `GET /issuer/cardholders` -- list all cardholders
- `GET /issuer/cards/{id}/authorizations` -- auth history for a card

---

## Bill payments -- next initiative

- `app/bills/` -- Bill + BillPayment models, scheduler job, executor job
- `app/payees/` -- Payee model and CRUD
- Reuses existing authorize + capture flow entirely
- Outbox events: `bill.scheduled`, `bill.executed`, `bill.failed`

---

## Running the apps

### Local development (no Docker)
```bash
# Infrastructure only
docker compose up -d postgres redis rabbitmq

# API
cd apps/api && poetry run uvicorn main:app --reload

# Web
cd apps/web && bun dev

# Celery worker
cd apps/api && poetry run celery -A workers.celery_app worker --loglevel=info

# Celery Beat
cd apps/api && poetry run celery -A workers.celery_app beat --loglevel=info

# RabbitMQ consumers (each in its own terminal)
cd apps/api && poetry run python -m workers.consumers.payments.fraud
cd apps/api && poetry run python -m workers.consumers.payments.notifications
cd apps/api && poetry run python -m workers.consumers.payments.reporting
```

### Full stack via Docker Compose
```bash
# Stripe keys must be set in the environment
export STRIPE_SECRET_KEY=sk_test_...
export STRIPE_WEBHOOK_SECRET=whsec_...

docker compose up --build
```

This starts: postgres, redis, rabbitmq, api, celery-beat, outbox-poller, consumer-fraud, consumer-notifications, consumer-reporting.

---

## End to end test flow
1. Frontend calls `POST /payments/authorize` -> gets back `client_secret`
2. Frontend renders Stripe Elements card form using `client_secret`
3. User enters test card `4242 4242 4242 4242`
4. Stripe.js confirms the payment intent
5. Stripe fires `payment_intent.succeeded` webhook to FastAPI
6. Webhook handler settles payment record + writes ledger entries + clears issuer hold
7. Outbox poller publishes `payment.authorized` and `payment.settled` events to RabbitMQ
8. Fraud consumer persists FraudSignal; notifications consumer persists NotificationLog; reporting consumer persists ReportingEvent
9. Full double-entry lifecycle complete, all observability tables populated

---

## Environment variables

**API (`apps/api/.env`):**
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/payments
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
PROCESSOR=stripe
EXPENSE_ACCOUNT_ID=00000000-0000-0000-0000-000000000001
LIABILITY_ACCOUNT_ID=00000000-0000-0000-0000-000000000002
CASH_ACCOUNT_ID=00000000-0000-0000-0000-000000000003

# Notification delivery -- defaults to stub (log only)
NOTIFICATION_SENDER=stub   # stub | smtp | twilio

# SMTP (required when NOTIFICATION_SENDER=smtp)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@payments-platform.local

# Twilio (required when NOTIFICATION_SENDER=twilio)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
```

**Web (`apps/web/.env.local`):**
```
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

---

## Issuer track -- architecture decisions

The issuer auth engine runs synchronously inside `payment_service.authorize()`,
before the Stripe PaymentIntent is created. This mirrors real-world card network
sequencing -- the issuer must approve before the acquirer proceeds.

### Call order in authorize()
1. Idempotency check
2. `issuer_auth_service.evaluate()` -- synchronous, blocking
3. If declined -- raise `PaymentDeclinedException`, never touch Stripe
4. Write issuer hold to ledger via `issuer_ledger_service.record_hold()`
5. Create Stripe PaymentIntent
6. Write acquiring payment record + ledger auth entries
7. `session.commit()` -- single transaction covers both sides

### Settlement (webhook side)
Inside `payment_service.handle_payment_succeeded()`, after acquiring ledger
settlement, call `issuer_settlement_service.clear_hold()` in the same transaction.

### Dependency rule
Payment service may call issuer service. Issuer service never calls payment
service. One-directional only.

---

## Coding style preferences
- Functional over classes -- only create classes when required (SQLAlchemy models, Pydantic schemas, Protocols)
- No em-dashes in comments or docstrings
- `isort` + `black` for formatting
- `get_logger(__name__)` from `shared/logger.py` for logging
- Clean separation: router handles HTTP, service handles business logic, repository handles DB I/O
- No cross-module repository calls -- only cross-module service calls

---

## Mandatory checklist when adding a new SQLAlchemy model

**ALWAYS do all three of these every time a new model is created -- no exceptions:**

1. **`alembic/env.py`** -- add an import for the new model module so `alembic revision --autogenerate` picks it up:
   ```python
   import app.mymodule.models  # noqa: F401
   ```
   Without this, autogenerate produces an empty migration even though the model exists.

2. **`tests/conftest.py`** -- add the same import so `Base.metadata.create_all()` creates the table in the test DB:
   ```python
   import app.mymodule.models  # noqa: F401
   ```
   Without this, tests that touch the new table will fail with "relation does not exist".

3. **Migration workflow** -- never hand-write migration files. Always:
   ```bash
   cd apps/api && poetry run alembic revision --autogenerate -m "describe the change"
   # review the generated file, then:
   poetry run alembic upgrade head
   ```
