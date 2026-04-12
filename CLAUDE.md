# payments-platform -- Claude Context

## Collaboration rules

- Do not run local commands unless explicitly authorized by the user.
- Do not run install/dev/test/migration commands by default; ask user to run them.
- Do not commit or push unless explicitly requested.
- Prefer small, verifiable edits.

## Repository snapshot (April 11, 2026)

This monorepo is implemented end-to-end:
- API domains are complete.
- Worker topology is complete (outbox poller, job workers, RabbitMQ consumers).
- Dashboard routes are complete in `apps/web`.

## Monorepo layout

```text
payments-platform/
  apps/
    api/    FastAPI + workers + tests
    web/    Next.js dashboard + checkout
  docker-compose.yml
```

## Web architecture (`apps/web`)

- No `src/` directory. Root-level `app/`, `components/`, `lib/`, `hooks/`.
- Path alias: `@/* -> ./*`.
- File names use kebab-case.
- Data flow layering is strict:
  - `lib/api/*` -> `lib/hooks/*` -> `app/*` + `components/*`.
- Components should not import SWR directly.
- Pages should not call `fetch` directly.
- Dynamic route params use `useParams()` from `next/navigation`.
- Pages using `useSearchParams()` should be wrapped in Suspense boundaries.

## API architecture (`apps/api`)

- Service/repository pattern.
- Repositories handle DB I/O and return DTOs.
- Services own transaction boundaries.
- Double-entry ledger for financial state transitions.
- Outbox pattern for async side effects.
- Celery + RabbitMQ for scheduled jobs and consumer projections.
- Processor abstraction:
  - `PROCESSOR` for card/checkout flow.
  - `BILL_PROCESSOR` for bill execution flow (defaults ACH).

## Worker topology

- Beat schedule:
  - outbox polling: 10s
  - bill scheduler: 5m
  - ACH settlement: 2m
  - hold expiry: 1h
  - reconciliation: 24h
- Consumers:
  - payments exchange: fraud, notifications, reporting
  - issuer exchange: card_activity, risk
- Dead-letter support exists via `payments.dlx` / `issuer.dlx`.

## Endpoint inventory

### Payments
- `GET /payments`
- `GET /payments/{payment_id}`
- `POST /payments/authorize`
- `POST /payments/capture`
- `POST /payments/refund`
- `POST /payments/webhooks/stripe`

### Payees + bills
- `POST /payees`
- `GET /payees`
- `GET /payees/{payee_id}`
- `POST /bills`
- `GET /bills`
- `GET /bills/{bill_id}`
- `PATCH /bills/{bill_id}`
- `POST /bills/{bill_id}/execute`

### Issuer
- `POST /issuer/cardholders`
- `GET /issuer/cardholders`
- `GET /issuer/cardholders/{cardholder_id}`
- `POST /issuer/cards`
- `GET /issuer/cards`
- `GET /issuer/cards/{card_id}`
- `GET /issuer/cards/{card_id}/balance`
- `GET /issuer/cards/{card_id}/authorizations`
- `GET /issuer/cards/{card_id}/controls/mcc-blocks`
- `POST /issuer/cards/{card_id}/controls/mcc-blocks`
- `DELETE /issuer/cards/{card_id}/controls/mcc-blocks/{mcc}`
- `GET /issuer/cards/{card_id}/controls/velocity-rules`
- `POST /issuer/cards/{card_id}/controls/velocity-rules`
- `DELETE /issuer/cards/{card_id}/controls/velocity-rules/{rule_id}`

### Observability
- `GET /fraud/signals`
- `GET /reporting/summary`
- `GET /reconciliation/runs`
- `GET /reconciliation/discrepancies`
- `GET /_live`

## Response shape notes (important)

- Most list endpoints used by dashboard return bare arrays, not wrapped pagination objects.
- Pagination is query-param driven (`limit`, `offset`) where supported.
- `GET /payments/{id}` returns wrapped detail:
  - `payment`
  - `ledger_transactions`
  - `outbox_events`
  - `issuer_authorization`
- `GET /bills/{id}` returns:
  - `bill`
  - `payments`

When wiring a new endpoint, verify actual `router.py` + `schemas.py` before coding against assumptions.

## Full E2E flow summary

### Card checkout path
1. `POST /payments/authorize` creates payment + ledger authorization + outbox event.
2. Stripe Elements confirms payment with returned `client_secret`.
3. Stripe webhook settles payment, writes settlement ledger entries, clears issuer hold when relevant.
4. Outbox poller publishes events to RabbitMQ.
5. Consumers persist fraud, notifications, and reporting projections.
6. Dashboard pages (`/payments`, `/fraud`, `/reporting`, `/reconciliation`) reflect state.

### Bill path
1. Create payee + bill (`/payees`, `/bills`).
2. Bill executes via scheduler or manual `/bills/{id}/execute`.
3. Bill execution creates `BillPayment` and emits `bill.*` outbox events.
4. Notifications/reporting consumers persist downstream records.
5. Dashboard pages (`/bills*`, `/reporting`) reflect lifecycle.

## Useful validation commands (user-run)

### Web
```bash
cd apps/web
bun run prettier --write
bunx tsc --noEmit
bun run test:unit
bun run build
```

### API
```bash
cd apps/api
poetry run pytest
```
