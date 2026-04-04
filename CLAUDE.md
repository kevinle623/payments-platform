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
        celery_app.py           -- Celery app, broker config, Beat schedule (poll every 10s)
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
- RabbitMQ consumers -- three long-running async consumers (fraud, notifications, reporting) subscribe to the `payments` topic exchange via named durable queues; `prefetch_count=1` for one-at-a-time processing; `exchanges.py` is single source of truth for exchange names; producers under `workers/producers/`, consumers under `workers/consumers/`, both organized by domain for extensibility

---

## What's not yet built
- Reconciliation job -- Celery Beat nightly job comparing ledger against Stripe records
- Docker Compose services for workers/consumers (deferred until reconciliation is done and logic is non-trivial)

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
