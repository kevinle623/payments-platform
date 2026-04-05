# payments-platform -- Claude Code Context

## Claude behavior rules
- Never run commands locally -- no pytest, no alembic, no poetry, no migrations, no seed scripts
- The user handles all local execution including tests, migrations, and alembic
- When changes require a migration or test run, describe what to run but do not execute it

## What this is
A payments platform monorepo with a FastAPI backend (`apps/api/`) and Next.js dummy frontend (`apps/web/`) for end-to-end Stripe payment testing. Implements double-entry ledger, processor abstraction, idempotency, Stripe webhook handling, issuer auth/controls/settlement, outbox pattern, RabbitMQ async pipeline, fraud signals, notifications, reporting, reconciliation, issuer worker pipeline, and bill payments (payees + recurring/manual bill execution).

**Repo:** https://github.com/kevinle623/payments-platform

**Status snapshot (April 5, 2026):** Tasks 6 through 11 are implemented; bill payments, dashboard backend read APIs, and bill downstream consumer wiring are complete in code. Latest migration: `637e756014ea_add_payees_and_bills_tables.py`.

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
        payees/                 -- Payee model + CRUD (create/list/get)
        bills/                  -- Bill + BillPayment models, execute flow, scheduler/manual trigger, router
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
          auth/                 -- evaluate(), IssuerAuthorization model, decision (approved/declined/expired) + decline reason
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
        celery_app.py           -- Celery app, broker config, Beat schedule (outbox every 10s, bill scheduler every 5m, reconciliation every 24h, hold expiry every 1h), task routes (`outbox` and `jobs` queues)
        exchanges.py            -- PAYMENTS_EXCHANGE, ISSUER_EXCHANGE constants (single source of truth)
        producers/
          outbox_poller.py      -- poll_and_publish Celery task: queries pending outbox rows, fans out to payments or issuer exchange based on event type prefix
                                   card.* / auth.* / hold.* -> issuer exchange | payment.* / bill.* / reconciliation.* -> payments exchange
        consumers/
          base.py               -- generic run_consumer/start (exchange_name, queue_name, routing_keys, handler)
          payments/
            fraud.py            -- payment.authorized -> persists FraudSignal row
            notifications.py    -- payment.* + bill.* + reconciliation.mismatch -> delivers via sender, persists NotificationLog
            reporting.py        -- payment.* + bill.* -> persists ReportingEvent row
          issuer/
            card_activity.py    -- card.issued, hold.created, hold.cleared -> logs card lifecycle (future: card activity feed)
            risk.py             -- auth.approved, auth.declined -> scores issuer-side risk patterns (future: feed into fraud module)
        jobs/
          bills/
            scheduler.py        -- every 5 minutes, finds due active bills and dispatches execution
            executor.py         -- thin execution wrapper for scheduler testability
          payments/
            reconciliation.py   -- nightly Celery task: creates ReconciliationRun, checks settled payments vs Stripe, writes ReconciliationDiscrepancy rows, publishes reconciliation.mismatch outbox events
          issuer/
            hold_expiry.py      -- hourly Celery task: finds IssuerAuthorization rows APPROVED + older than 7 days, calls clear_hold() for genuinely stale holds, marks EXPIRED; skips already-settled payments to prevent double-clearing ledger
      scripts/
        seed.py                 -- seeds ledger accounts into DB
      alembic/                  -- migrations
      tests/                    -- pytest tests
        payees/                 -- payee CRUD service tests
        bills/                  -- bill service execution + scheduler tests
        fraud/                  -- FraudSignal service tests
        notifications/          -- NotificationLog + sender tests
        reporting/              -- ReportingEvent + summary tests
        reconciliation/         -- ReconciliationRun + discrepancy tests
        payments/               -- payment service tests
        ledger/                 -- ledger service tests
        issuer/                 -- issuer auth + settlement + hold expiry tests
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
  docker-compose.yml            -- full stack: postgres, redis, rabbitmq, api, celery-beat, outbox-poller, worker-jobs, all consumers (payments + issuer)
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
- Outbox poller fans out by event type prefix: `card.*` / `auth.*` / `hold.*` go to `issuer` exchange; everything else goes to `payments` exchange
- `IssuerAuthDecision` has three values: `approved`, `declined`, `expired` -- hold expiry job sets EXPIRED to prevent reprocessing
- Hold expiry double-clear prevention: job checks payment status before calling `clear_hold()`; if payment is already SUCCEEDED/REFUNDED, only marks auth EXPIRED (no ledger action)

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
- Outbox pattern -- `OutboxEvent` rows written atomically in same DB transaction; Celery Beat polls every 10s, fans out to payments or issuer RabbitMQ exchange
- `OutboxEventType` values: `payment.authorized`, `payment.settled`, `payment.refunded`, `bill.scheduled`, `bill.executed`, `bill.failed`, `reconciliation.mismatch`, `card.issued`, `auth.approved`, `auth.declined`, `hold.created`, `hold.cleared`
- Five long-running RabbitMQ consumers on durable queues with `prefetch_count=1`: fraud, notifications, reporting (payments exchange), card_activity, risk (issuer exchange)

### Completed iterations
- **Fraud** -- `FraudSignal` model persisted per `payment.authorized` event; `GET /fraud/signals` with `risk_level` filter + pagination; high-value threshold $100
- **Notifications** -- `NotificationLog` persisted for `payment.*`, `bill.*`, and `reconciliation.mismatch`; `NotificationSender` Protocol with `StubSender` (default), `SmtpSender` (smtplib), `TwilioSender` (stub); `get_sender()` factory driven by `NOTIFICATION_SENDER` env var
- **Reporting** -- `ReportingEvent` persisted for `payment.*` and `bill.*`; `GET /reporting/summary` returns daily volume grouped by date + event_type + currency with optional `since`/`until` filters
- **Reconciliation** -- `ReconciliationRun` + `ReconciliationDiscrepancy` models; nightly job; `GET /reconciliation/runs` + `GET /reconciliation/discrepancies?run_id=`
- **Issuer outbox events (Task 6)** -- `card.issued` published from cards service; `auth.approved`/`auth.declined` from auth service; `hold.created` from ledger service; `hold.cleared` from settlement service; all in same DB transaction
- **Issuer consumers (Task 7)** -- `card_activity.py` (card.issued, hold.created, hold.cleared) and `risk.py` (auth.approved, auth.declined) on issuer exchange; outbox poller fans out by event prefix
- **Issuer hold expiry (Task 8)** -- hourly Celery Beat job; `get_stale_approved()` query with composite index on `(decision, created_at)`; double-clear prevention via payment status check
- **Bill payments (Task 9)** -- `Payee`, `Bill`, `BillPayment` models; payee + bill routers; scheduled bill execution (Beat every 5 minutes) and manual trigger (`POST /bills/{id}/execute`); outbox events `bill.scheduled`/`bill.executed`/`bill.failed`; tests added in `tests/payees` and `tests/bills`
- **Dashboard backend APIs (Task 10)** -- added `GET /payments`, `GET /payments/{id}`, `GET /issuer/cards`, `GET /issuer/cardholders`, `GET /issuer/cards/{id}/authorizations`; payment detail aggregates ledger transactions + outbox events + issuer auth context
- **Bill downstream consumers + worker topology (Task 11)** -- notifications/reporting consumers subscribe to `bill.*`; bill event payload contract standardized; Celery task routing split into `outbox` and `jobs` queues; Docker Compose includes dedicated `worker-jobs`
- **Docker Compose** -- full stack containerized including `consumer-card-activity` and `consumer-issuer-risk`

---

## What's not yet built
- Web UI dashboard (NEXT -- see spec below)
- ACH processor adapter (next processor for bill-routing use cases)
- RabbitMQ consumer dead-lettering for failed messages
- Real Twilio SMS delivery (stub is in place, needs `pip install twilio` + credentials)
- Issuer dispute aging job

---

## Immediate next steps (ordered)
1. Add integration tests for `bill.*` consumer handling paths:
   - notifications consumer (`_handle_bill_event`)
   - reporting consumer (`_handle` persistence for bill events)
2. Add RabbitMQ dead-lettering/retry policy for payments consumers so poison messages do not block queues.
3. Build web dashboard bills pages (`/bills`, `/bills/[id]`) using existing bill/payee endpoints and manual execute trigger.
4. Build remaining web dashboard read pages for payments and issuer track using completed backend APIs.
5. Start ACH processor adapter initiative (`shared/processors/adapters/ach.py`) with bank-account domain model and async settlement lifecycle.

---

## Bill payments -- COMPLETED (Task 9)

Implemented with service/repository/router pattern and production wiring.

### Data model

**Payee** (`app/payees/`):
```
id, name, payee_type (utility/credit_card/mortgage/other),
account_number, routing_number, currency, created_at
```

**Bill** (`app/bills/`):
```
id, payee_id (FK), card_id (optional -- triggers issuer track when present),
amount, currency,
frequency (one_time/weekly/biweekly/monthly),
next_due_date, status (active/paused/completed/failed),
created_at, updated_at
```

**BillPayment** (execution record, also in `app/bills/`):
```
id, bill_id (FK), payment_id (FK -> payments.id),
status (pending/succeeded/failed),
executed_at
```

Relationship: `Payee <- Bill <- BillPayment -> Payment`

### Execution flow
1. Scheduler job (Celery Beat, every 5 minutes) finds bills where `next_due_date <= now AND status = active`
2. For each due bill, calls `bill_service.execute_bill()`
3. `execute_bill()` calls the existing `payment_service.authorize()` with the bill's amount/currency/card_id
4. On success: creates BillPayment record, advances `next_due_date` (or marks bill `completed` if `one_time`), publishes `bill.executed` outbox event
5. On failure: creates BillPayment record with failed status, publishes `bill.failed` outbox event; does NOT advance next_due_date (retry next cycle)

### Manual trigger
- `POST /bills/{id}/execute` -- on-demand execution, calls same `execute_bill()` service function
- Useful for dashboard retry and testing

### API endpoints
```
POST   /payees                    -- create payee
GET    /payees                    -- list payees
GET    /payees/{id}               -- get payee

POST   /bills                     -- create bill (schedules it)
GET    /bills                     -- list bills (filter by status)
GET    /bills/{id}                -- get bill + payment history
POST   /bills/{id}/execute        -- manual trigger
PATCH  /bills/{id}                -- update (pause/resume, change amount)
```

### Outbox events
- `bill.scheduled` -- published when a bill is created
- `bill.executed` -- published on successful execution
- `bill.failed` -- published on failed execution
- All route to `payments` exchange (same domain)
- Implemented in `OutboxEventType` in `app/outbox/models.py`

### Worker structure
```
workers/
  jobs/
    bills/
      scheduler.py   -- Celery Beat task (every 5 min): finds due bills, calls execute_bill()
      executor.py    -- execute_bill() logic extracted here for testability
```

Implemented in `celery_app.py` beat schedule:
```python
"schedule-bills": {
    "task": "workers.jobs.bills.scheduler.run_bill_scheduler",
    "schedule": 300.0,  # every 5 minutes
}
```

### Mandatory checklist
Completed for Payee, Bill, BillPayment:
1. Add imports to `alembic/env.py`
2. Add imports to `tests/conftest.py`
3. Generated migration: `637e756014ea_add_payees_and_bills_tables.py`
4. Run `poetry run alembic upgrade head`

### Tests implemented
- `tests/bills/test_service.py` -- bill creation, execute_bill happy path, execute_bill failure path, frequency advancement (one_time completes, monthly advances next_due_date), manual trigger idempotency
- `tests/bills/test_scheduler.py` -- get_due_bills repository query, skips paused/completed bills
- `tests/payees/test_service.py` -- CRUD
- Validation run: targeted suite passed (`10 passed`)

---

## Web UI dashboard -- NEXT

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

**Bills**
- `/bills` -- list bills with status, payee name, amount, frequency, next_due_date
- `/bills/[id]` -- bill detail: execution history, manual trigger button

**Observability**
- `/fraud` -- list of fraud signals with risk level badge, payment id, amount, flagged_at
- `/reconciliation` -- list of reconciliation runs with checked/mismatch counts; expand to see discrepancies
- `/reporting` -- daily volume chart grouped by currency; event type breakdown

### Backend endpoints status (completed)
- `GET /payments` -- paginated list with optional status filter
- `GET /payments/{id}` -- payment detail including ledger entries, outbox events, and issuer auth decision
- `GET /issuer/cards` -- list all cards
- `GET /issuer/cardholders` -- list all cardholders
- `GET /issuer/cards/{id}/authorizations` -- auth history for a card
- Validation run: `tests/payments/test_service.py` + `tests/issuer/test_cards_service.py` passed (`14 passed`)

---

## ACH processor adapter -- NEXT

The processor abstraction (`shared/processors/base.py`) is already set up for this. ACH is the industry standard for bill payments (bank-to-bank, 1-3 day settlement, NACHA return codes).

Implementation plan:
- `shared/processors/adapters/ach.py` -- `ACHAdapter` implementing the `PaymentProcessor` Protocol
- New `BankAccount` model for storing verified bank account details (sits alongside `Card` in issuer track)
- Bank account verification flow (micro-deposits)
- Different status lifecycle: `pending -> processing -> settled/failed` with async returns
- Bills can be routed to ACH via `PROCESSOR=ach` env var -- zero changes to bill service

---

## Celery jobs runner split -- implemented

Implemented behavior:
- `celery-beat` schedules `poll_and_publish`, `run_bill_scheduler`, `run_hold_expiry`, and `run_reconciliation`.
- Celery task routes split queues explicitly:
  - `workers.producers.outbox_poller.poll_and_publish -> outbox`
  - `workers.jobs.bills.scheduler.run_bill_scheduler -> jobs`
  - `workers.jobs.issuer.hold_expiry.run_hold_expiry -> jobs`
  - `workers.jobs.payments.reconciliation.run_reconciliation -> jobs`
- Docker Compose worker services:
  - `outbox-poller`: `celery -A workers.celery_app worker --loglevel=info -Q outbox`
  - `worker-jobs`: `celery -A workers.celery_app worker --loglevel=info -Q jobs`

---

## Bill-event downstream consumer pipeline -- implemented

Implemented behavior:
- `bill.scheduled`, `bill.executed`, and `bill.failed` payloads are standardized in bills service.
- Notifications consumer subscribes to `bill.*` routing keys and writes NotificationLog rows for bill lifecycle events.
- Reporting consumer subscribes to `bill.*` routing keys and records reporting events for bill lifecycle analytics.

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

# Celery worker -- outbox queue
cd apps/api && poetry run celery -A workers.celery_app worker --loglevel=info -Q outbox

# Celery worker -- jobs queue
cd apps/api && poetry run celery -A workers.celery_app worker --loglevel=info -Q jobs

# Celery Beat
cd apps/api && poetry run celery -A workers.celery_app beat --loglevel=info

# RabbitMQ consumers -- payments exchange
cd apps/api && poetry run python -m workers.consumers.payments.fraud
cd apps/api && poetry run python -m workers.consumers.payments.notifications
cd apps/api && poetry run python -m workers.consumers.payments.reporting

# RabbitMQ consumers -- issuer exchange
cd apps/api && poetry run python -m workers.consumers.issuer.card_activity
cd apps/api && poetry run python -m workers.consumers.issuer.risk
```

### Full stack via Docker Compose
```bash
export STRIPE_SECRET_KEY=sk_test_...
export STRIPE_WEBHOOK_SECRET=whsec_...

docker compose up --build
```

Services: postgres, redis, rabbitmq, api, celery-beat, outbox-poller, worker-jobs, consumer-fraud, consumer-notifications, consumer-reporting, consumer-card-activity, consumer-issuer-risk.

---

## End to end test flow
1. Frontend calls `POST /payments/authorize` -> gets back `client_secret`
2. Frontend renders Stripe Elements card form using `client_secret`
3. User enters test card `4242 4242 4242 4242`
4. Stripe.js confirms the payment intent
5. Stripe fires `payment_intent.succeeded` webhook to FastAPI
6. Webhook handler settles payment record + writes ledger entries + clears issuer hold + publishes `hold.cleared` outbox event
7. Outbox poller fans out: `payment.*` events to payments exchange, `hold.*` / `auth.*` / `card.*` to issuer exchange
8. payments exchange: fraud consumer persists FraudSignal; notifications consumer persists NotificationLog; reporting consumer persists ReportingEvent
9. issuer exchange: card_activity consumer logs hold lifecycle; risk consumer logs auth decisions
10. Full double-entry lifecycle complete, all observability tables populated

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
