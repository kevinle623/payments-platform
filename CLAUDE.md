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
        reconciliation/         -- stub, not yet built
        outbox/                 -- stub, not yet built
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

---

## What's not yet built
- Outbox pattern -- write ledger + outbox event atomically, Celery worker polls and publishes to RabbitMQ
- RabbitMQ event consumers (fraud, notifications, reporting)
- Reconciliation job -- Celery Beat nightly job comparing ledger against Stripe records
- Payment service tests -- pytest with mocked processor adapter and real test DB
- Ledger tests need updating -- `session.commit()` was removed from ledger service, tests need `await session.commit()` added directly

---

## Running the apps
```bash
# API (from apps/api/)
cd apps/api && poetry run uvicorn main:app --reload

# Web (from apps/web/)
cd apps/web && bun dev

# Infrastructure
docker compose up -d
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

## Coding style preferences
- Functional over classes -- only create classes when required (SQLAlchemy models, Pydantic schemas, Protocols)
- No em-dashes in comments or docstrings
- `isort` + `black` for formatting
- `get_logger(__name__)` from `shared/logger.py` for logging
- Clean separation: router handles HTTP, service handles business logic, repository handles DB I/O
- No cross-module repository calls -- only cross-module service calls