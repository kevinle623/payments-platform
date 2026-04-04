# payments-platform — Claude Code Context

## What this is
A payments platform monorepo with a FastAPI backend (`apps/api/`) and Next.js dummy frontend (`apps/web/`) for end-to-end Stripe payment testing. Implements double-entry ledger, processor abstraction, idempotency, and Stripe webhook handling.

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
- Repository deserializes ORM → Pydantic DTOs before returning to service
- Service owns transaction boundary (commit/rollback) -- repository only flushes
- Processor abstraction via Protocol in `shared/processors/base.py` with `StripeAdapter` in `shared/processors/adapters/stripe.py` and a factory in `shared/processors/factory.py`
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
        issuer/
          auth/                 -- evaluate(), IssuerAuthorization model, decision + decline reason
          cards/                -- Cardholder, Card models, per-card ledger accounts, balance endpoint
          controls/             -- MCCBlock, VelocityRule, check_controls() rule engine
          settlement/           -- clear_hold(), wired into handle_payment_succeeded()
        reconciliation/         -- stub, not yet built
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
        settings.py             -- environ.get() based config
        exceptions.py           -- domain exceptions
        exception_handlers.py   -- FastAPI exception handlers
        logger.py               -- get_logger(__name__)
      workers/
        celery_app.py           -- Celery app, broker config, Beat schedule (outbox every 10s, reconciliation every 24h)
        exchanges.py            -- PAYMENTS_EXCHANGE, ISSUER_EXCHANGE constants (single source of truth)
        producers/
          payments/
            outbox_poller.py    -- poll_and_publish Celery task: queries pending outbox rows, publishes to payments exchange
        consumers/
          base.py               -- generic run_consumer/start (exchange_name, queue_name, routing_keys, handler)
          payments/
            fraud.py            -- payment.authorized -> risk score, flags high-value payments
            notifications.py    -- payment.* -> simulated email/SMS notification
            reporting.py        -- payment.* -> simulated analytics entry
          issuer/               -- future: card.issued, dispute.opened, hold.expired consumers
        jobs/
          payments/
            reconciliation.py   -- nightly Celery task: queries settled payments, compares against Stripe, logs mismatches
          issuer/               -- future: hold expiry, dispute aging
      scripts/
        seed.py                 -- seeds ledger accounts into DB
      alembic/                  -- migrations
      tests/                    -- pytest tests
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
  docker-compose.yml            -- postgres, redis, rabbitmq
```

---

## Key design decisions
- `SupportedProcessorType` StrEnum in `shared/enums/processor.py` -- fails fast if invalid processor set
- Ledger account UUIDs hardcoded in `settings.py` as `EXPENSE_ACCOUNT_ID`, `LIABILITY_ACCOUNT_ID`, `CASH_ACCOUNT_ID` -- seeded via `scripts/seed.py`
- `stripe.PaymentIntent.create` uses `capture_method="manual"` and `automatic_payment_methods={"enabled": True, "allow_redirects": "never"}`
- Ledger service has no `session.commit()` -- caller owns the commit
- `_record_transaction` is private, `record_authorization` and `record_settlement` are the public API

---

## What's working
- `POST /payments/authorize` -- creates Stripe PaymentIntent, writes payment record + ledger authorization entries atomically, returns `client_secret`
- Idempotency -- duplicate requests return existing result without hitting Stripe
- Stripe webhook handler at `POST /payments/webhooks/stripe` -- validates signature, parses event, dispatches to service
- `handle_payment_succeeded` -- settles payment record + writes ledger settlement entries
- `handle_payment_refunded` -- refunds payment record
- `GET /_live` -- liveness endpoint
- Stripe CLI webhook forwarding working end to end
- DB seeded with expense, liability, cash ledger accounts
- CORS middleware allows requests from `localhost:3000`
- Next.js dummy frontend with Stripe Elements card form for end-to-end testing
- Payment service tests -- pytest with mocked processor, real test DB, covers authorize, idempotency, capture, refund, webhook handlers
- Ledger service tests -- all passing, session.commit() owned by caller as designed
- Logging across router, service, and ledger layers (INFO for state transitions, ERROR for imbalance, DEBUG for ledger writes)
- Bug fix -- `AuthorizeResponse.client_secret` defaulted to `None` so idempotency path doesn't blow up on DB hydration
- Issuer auth engine -- `evaluate()` in `app/issuer/auth/service.py`, wired into `payment_service.authorize()` before Stripe call, records `IssuerAuthorization` with decision + decline reason
- Issuer cards -- `Cardholder` and `Card` models, per-card `available_balance` and `pending_hold` ledger accounts auto-created on card issuance, balance endpoint at `GET /issuer/cards/{id}/balance`
- Issuer controls -- `MCCBlock` and `VelocityRule` models, `check_controls()` runs balance check + MCC block + velocity limit in order, plugged into `evaluate()`
- Issuer settlement -- `clear_hold()` in `app/issuer/settlement/service.py`, wired into `handle_payment_succeeded()`, clears pending hold atomically with acquiring settlement
- Issuer tests -- 24 tests covering all decline paths, idempotency, ledger invariants, full lifecycle (auth + settle nets to zero), card-integrated payment flow
- `card_id` optional on `AuthorizeRequest` -- triggers full issuer controls when provided, backwards compatible when omitted
- `PaymentDeclinedException` -- HTTP 402, raised when issuer declines before Stripe is called
- Outbox pattern -- `OutboxEvent` rows written atomically in the same DB transaction as payment/ledger writes; Celery Beat fires every 10s, worker queries pending rows and publishes to RabbitMQ `payments` topic exchange via aio-pika, marks rows published/failed; `(status, created_at)` composite index covers the poller query; engine created fresh per task invocation (not reused from postgresql.py) to avoid asyncio event loop mismatch across `asyncio.run()` calls
- RabbitMQ consumers -- three long-running async consumers (fraud, notifications, reporting) subscribe to the `payments` topic exchange via named durable queues; `prefetch_count=1` for one-at-a-time processing; `exchanges.py` is single source of truth for exchange names; producers under `workers/producers/`, consumers under `workers/consumers/`, jobs under `workers/jobs/`, all organized by domain
- Reconciliation job -- nightly Celery Beat task (`workers/jobs/payments/reconciliation.py`); queries settled payments in last 24h using composite `ix_payments_status_created_at` index; calls `stripe.PaymentIntent.retrieve()` for each; logs warnings on status mismatches; separate `jobs/` directory distinguishes scheduled jobs from message producers/consumers

---

## What's not yet built
- Docker Compose services for workers/consumers/jobs (deferred -- logic is currently logging stubs)
- Reconciliation discrepancy persistence (currently logs only -- no DB table yet)
- RabbitMQ consumer dead-lettering for failed messages
- Fraud signals persistence
- Real notification delivery (email/SMS)
- Reporting persistence and aggregation
- Issuer outbox events and issuer-side consumers/jobs
- Bill payments module
- Web UI dashboard (payment tracing, card management, issuer decisions, fraud signals)

---

## Iteration 2 -- real implementations (current focus)

The async pipeline is wired end-to-end but all consumers and the reconciliation job are logging stubs. The goal of iteration 2 is to make each one functionally real.

### Task 1 -- Fraud: persist risk signals
- Add `app/fraud/` module with `FraudSignal` model (`payment_id`, `risk_level`, `amount`, `currency`, `flagged_at`)
- Consumer writes a `FraudSignal` row instead of just logging
- Add `GET /fraud/signals` endpoint to query flagged payments
- Index on `(risk_level, flagged_at)` for dashboard queries
- Add `FraudSignalDTO` and tests

### Task 2 -- Notifications: real delivery
- Add `email` field to `Cardholder` model (migration required)
- Add `app/notifications/` module with `NotificationLog` model (`cardholder_id`, `event_type`, `channel`, `message`, `sent_at`)
- Integrate a delivery provider -- use SMTP (smtplib) or stub with a mock transport behind a `NotificationSender` Protocol so it's swappable
- Consumer looks up cardholder from `card_id` in payload, sends notification, writes log row
- Add tests covering log persistence and mock delivery

### Task 3 -- Reporting: persist events and aggregate
- Add `app/reporting/` module with `ReportingEvent` model (`event_type`, `payment_id`, `amount`, `currency`, `recorded_at`)
- Consumer writes a `ReportingEvent` row per payment lifecycle event
- Add `GET /reporting/summary` endpoint -- daily volume grouped by currency and event type
- Index on `(event_type, recorded_at)` for summary queries
- Add tests

### Task 4 -- Reconciliation: persist discrepancies
- Add `ReconciliationRun` model (`started_at`, `completed_at`, `checked`, `mismatches`) and `ReconciliationDiscrepancy` model (`payment_id`, `processor_payment_id`, `our_status`, `stripe_status`, `detected_at`) in `app/reconciliation/`
- Job writes a `ReconciliationRun` row and a `ReconciliationDiscrepancy` row per mismatch instead of just logging
- Wire discrepancies into the notifications consumer -- publish a `reconciliation.mismatch` outbox event so the notifications consumer can alert
- Add `GET /reconciliation/runs` and `GET /reconciliation/discrepancies` endpoints
- Add tests

### Task 5 -- Docker Compose: add worker services
- Add `outbox-poller`, `celery-beat`, `consumer-fraud`, `consumer-notifications`, `consumer-reporting` services to `docker-compose.yml`
- Add a shared `Dockerfile` for the API image
- All worker services share the same image, different `command`
- Wire `depends_on` to postgres and rabbitmq

---

## Iteration 2 -- issuer workers

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

Need a second outbox poller for the issuer exchange or extend the existing poller to fan out to multiple exchanges based on event type prefix (`payment.*` vs `card.*` / `auth.*` / `hold.*`).

### Task 8 -- Issuer jobs (`workers/jobs/issuer/`)
- `hold_expiry.py` -- Celery Beat job (runs hourly); finds `IssuerAuthorization` rows that are APPROVED and older than the hold expiry window (e.g. 7 days) with no corresponding settlement; calls `clear_hold()` and marks authorization as EXPIRED; prevents stale holds from permanently blocking available credit
- Future: `dispute_aging.py` -- escalate disputes that haven't been resolved within SLA

---

## Web UI dashboard -- next initiative

The current frontend is a minimal Stripe Elements checkout form. The goal is to extend it into a dev dashboard that visualizes the full payment lifecycle and lets you interact with the issuer track directly -- useful for E2E testing without hitting curl or the DB directly.

### Pages to build

**Payment flow (acquiring side)**
- `/ ` -- existing checkout page (keep as-is, entry point for triggering a payment)
- `/payments` -- paginated list of payments with id, amount, currency, status, created_at; click to drill in
- `/payments/[id]` -- payment detail: status timeline, ledger entries (debit/credit table), outbox events emitted, issuer auth decision if card was used, processor payment id link

**Issuer track**
- `/cards` -- list all cards with cardholder name, last four, credit limit, available credit, pending holds; button to issue a new card
- `/cards/[id]` -- card detail: balance breakdown, spend controls (MCC blocks + velocity rules) with add/remove UI, recent authorizations with approve/decline badge and decline reason
- `/cardholders` -- list cardholders, create new cardholder form

**Observability**
- `/fraud` -- list of fraud signals with risk level badge, payment id, amount, flagged_at (requires iteration 2 task 1)
- `/reconciliation` -- list of reconciliation runs with checked/mismatch counts; expand a run to see individual discrepancies (requires iteration 2 task 4)
- `/reporting` -- daily volume chart grouped by currency; event type breakdown (authorized vs settled vs refunded) (requires iteration 2 task 3)

### API endpoints to add (backend)
To support the dashboard, add read endpoints that don't exist yet:
- `GET /payments` -- paginated list with optional status filter
- `GET /payments/{id}` -- payment detail including ledger entries and outbox events
- `GET /issuer/cards` -- list all cards
- `GET /issuer/cardholders` -- list all cardholders
- `GET /issuer/cards/{id}/authorizations` -- auth history for a card
- `GET /fraud/signals` -- list fraud signals (iteration 2)
- `GET /reconciliation/runs` -- list reconciliation runs (iteration 2)
- `GET /reporting/summary` -- daily volume summary (iteration 2)

### Tech approach
- Next.js App Router pages with server components for data fetching
- Tailwind CSS for styling (already set up)
- No new dependencies needed beyond what's already in `apps/web/`
- Mock data where backend endpoints don't exist yet -- use a `USE_MOCK` flag per page so the UI can be built ahead of the API

### Build order
1. `/payments` list and `/payments/[id]` detail -- most useful for tracing the existing E2E flow
2. `/cards` and `/cards/[id]` -- issuer track interaction
3. `/cardholders` -- cardholder management
4. `/fraud`, `/reconciliation`, `/reporting` -- after iteration 2 backend tasks are done

---

## Bill payments -- next initiative

Goal: extend the platform to support scheduled and recurring bill payments (utilities, rent, subscriptions) on top of the existing payment and ledger infrastructure.

### Why this is a natural extension
- Existing `payments` module handles one-off authorized payments -- bill payments need scheduling, recurrence, and payee management
- The ledger already supports any debit/credit pattern -- bill payments just introduce a new posting policy
- Outbox + RabbitMQ pipeline can drive bill due-date reminders and execution events
- Issuer controls (velocity limits, MCC blocks) can apply to bill payments with no changes

### New domains to add
- `app/bills/` -- Bill model (payee, amount, due_date, recurrence_rule, status), BillPayment model (bill_id, payment_id, scheduled_for, executed_at)
- `app/payees/` -- Payee model (name, category, bank details or processor reference)

### Recurrence engine
- Store recurrence as a simple rule: `MONTHLY`, `WEEKLY`, `ANNUAL`, or a cron expression
- Celery Beat job under `workers/jobs/bills/scheduler.py` runs daily, finds bills due within the next N days, creates scheduled `BillPayment` rows
- A second job `workers/jobs/bills/executor.py` runs more frequently, finds due `BillPayment` rows, calls `payment_service.authorize()` then `capture()` -- reuses existing acquiring flow entirely

### Ledger impact
- Bill payments post to existing ledger accounts -- no new account types needed
- Add `bill_payment_id` as an optional reference on `LedgerTransaction` for traceability

### Events
- Add `bill.scheduled`, `bill.executed`, `bill.failed` to `OutboxEventType`
- Notifications consumer handles `bill.scheduled` (upcoming reminder) and `bill.failed` (alert)
- Reporting consumer handles all bill events for analytics

### New API endpoints
- `POST /bills` -- create a bill with payee, amount, recurrence
- `GET /bills` -- list bills with status
- `GET /bills/{id}/payments` -- history of executions
- `POST /payees` -- register a payee

### Build order
1. `app/payees/` -- Payee model and CRUD
2. `app/bills/` -- Bill + BillPayment models, service, repository
3. `workers/jobs/bills/scheduler.py` -- daily job to generate BillPayment rows
4. `workers/jobs/bills/executor.py` -- execution job calling existing authorize + capture
5. Outbox events for bill lifecycle
6. Notification + reporting consumer handlers for bill events
7. Tests covering recurrence scheduling, execution, and failure handling

---

## Future extension work (issuer-side simulation roadmap)
Goal: keep current Stripe acquiring flow, and add a second track that simulates issuer-side systems for learning.

### Why this matters
- Current project is strong for payment orchestration, webhooks, and ledgering
- Issuer-side work adds authorization decisioning, controls, limits, settlement/reconciliation, and dispute flows
- A realistic simulator can teach issuer architecture without needing direct card network access

### Core issuer domains to add
- Card program + cardholder/accounts domain
- Authorization engine (`auth request` -> approve/decline with reason codes)
- Holds lifecycle (`authorize`, `increment`, `partial capture`, `reversal`, `expiry`)
- Settlement and posting pipeline (pending -> posted entries)
- Spend controls (MCC blocks, merchant/category restrictions, velocity limits, per-user/team budgets)
- Risk/fraud checks and rule evaluation
- Disputes/chargebacks and adjustments

### Recommended architecture approach
- Keep `payments` module for acquiring (Stripe) as-is
- Add new `issuer` module(s) in API:
  - `issuer/cards`
  - `issuer/authorizations`
  - `issuer/controls`
  - `issuer/settlement`
  - `issuer/disputes`
- Reuse the same double-entry ledger, but introduce issuer-specific account mappings and posting policies
- Use outbox + RabbitMQ as the event backbone between auth, posting, risk, and notifications
- Build a fake network adapter that emits realistic card lifecycle events into the system

### Simulation strategy (no real network required)
- Implement a `MockNetworkAdapter` that sends ISO-like event payloads (auth, clearing, reversal, chargeback)
- Drive scenarios with deterministic fixtures:
  - insufficient funds/limit
  - MCC blocked
  - velocity exceeded
  - auth approved but clearing amount differs
  - late presentment and expired holds
- Keep Stripe path available for end-to-end acquiring demos while issuer simulator runs in parallel

### Milestones
1. Issuer account and card models with limits and available balance calculation
2. Real-time auth decision endpoint + rule engine + reason codes
3. Hold/settlement state machine with double-entry postings and invariants
4. Outbox events + consumer services for notifications/risk/reporting
5. Reconciliation and dispute simulation
6. Full integration test harness with scenario replay

### Quality bar for issuer track
- State machine tests for all lifecycle transitions
- Ledger invariants: every posting balanced and traceable to source event
- Idempotency on all inbound network events
- Replay-safe consumers and at-least-once event handling
- Auditability: immutable event log + correlation IDs across modules

---

## Running the apps
```bash
# API (from apps/api/)
cd apps/api && poetry run uvicorn main:app --reload

# Web (from apps/web/)
cd apps/web && bun dev

# Infrastructure
docker compose up -d

# Celery worker (from apps/api/)
cd apps/api && poetry run celery -A workers.celery_app worker --loglevel=info

# Celery Beat scheduler (from apps/api/)
cd apps/api && poetry run celery -A workers.celery_app beat --loglevel=info

# RabbitMQ consumers (each in its own terminal, from apps/api/)
cd apps/api && poetry run python -m workers.consumers.payments.fraud
cd apps/api && poetry run python -m workers.consumers.payments.notifications
cd apps/api && poetry run python -m workers.consumers.payments.reporting
```

---

## End to end test flow
1. Frontend calls `POST /payments/authorize` on the FastAPI backend → gets back `client_secret`
2. Frontend renders Stripe Elements card form using `client_secret`
3. User enters test card `4242 4242 4242 4242`
4. Stripe.js confirms the payment intent
5. Stripe fires `payment_intent.succeeded` webhook to FastAPI
6. Webhook handler settles payment record + writes ledger entries
7. Full double-entry lifecycle complete

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
1. Idempotency check (existing)
2. `issuer_auth_service.evaluate()` -- synchronous, blocking
3. If declined -- raise `PaymentDeclinedException`, never touch Stripe
4. Write issuer hold to ledger via `issuer_ledger_service.record_hold()`
5. Create Stripe PaymentIntent (existing)
6. Write acquiring payment record + ledger auth entries (existing)
7. `session.commit()` -- single transaction covers both sides

### Settlement (webhook side)
Inside `payment_service.handle_payment_succeeded()`, after acquiring ledger
settlement, call `issuer_settlement_service.clear_hold()` in the same transaction.

### Module structure
- `app/issuer/auth/`        -- evaluate(), rule engine, IssuerAuthorization model
- `app/issuer/controls/`    -- spend controls, MCC blocks, velocity limits
- `app/issuer/settlement/`  -- clear_hold()
- `app/issuer/network/`     -- MockNetworkAdapter (translates payment request to ISO-like auth request)

### Dependency rule
Payment service may call issuer service. Issuer service never calls payment
service. One-directional only.

### Outbox / RabbitMQ
Not used for auth or settlement -- those are synchronous direct service calls.
Reserved for async side effects: fraud scoring, notifications, reporting.

### Build order
1. `issuer/auth/` -- stub engine that always approves, wire end to end first
2. Plug into `payment_service.authorize()` before Stripe call
3. `issuer/controls/` -- MCC blocks, velocity limits, spend controls
4. `issuer/settlement/` -- clear_hold() from webhook handler
5. Outbox + RabbitMQ for async side effects last

---

## Coding style preferences
- Functional over classes -- only create classes when required (SQLAlchemy models, Pydantic schemas, Protocols)
- No em-dashes in comments or docstrings
- `isort` + `black` for formatting
- `get_logger(__name__)` from `shared/logger.py` for logging
- Clean separation: router handles HTTP, service handles business logic, repository handles DB I/O
- No cross-module repository calls -- only cross-module service calls
