# apps/web

Next.js 16 dashboard + checkout frontend for the payments-platform backend.

## Status snapshot (April 11, 2026)

Dashboard implementation is complete:

- checkout on `/`
- payments, issuing, bills, and observability routes
- shared component system under `components/common`
- SWR hook layer under `lib/hooks`
- unit/component tests with Vitest

## Stack

- Next.js 16 App Router
- React 19 + TypeScript
- Tailwind CSS v4
- SWR
- Stripe Elements
- Vitest + Testing Library

## Architecture

Strict layering:

```text
lib/api/*   -> endpoint service functions
lib/hooks/* -> SWR query/mutation hooks
app/* + components/* -> UI routes and feature components
```

Rules:

- Components do not import SWR directly.
- Pages are thin wrappers and should not fetch directly.
- Dynamic route params use `useParams()` from `next/navigation`.
- Query/filter state is URL-driven via search params.

## Route coverage

- `/` overview + Stripe checkout
- `/payments` list
- `/payments/[id]` detail (overview/ledger/outbox/issuer tabs)
- `/cards` list + issue form
- `/cards/[id]` detail (card + balance + authorizations in parallel)
- `/cardholders` list + create form
- `/payees` list + create form
- `/bills` list + status filter
- `/bills/new` create flow
- `/bills/[id]` detail + execute + pause/resume
- `/fraud` list + risk filter
- `/reporting` date filters + charts + summary table
- `/reconciliation` run list + lazy discrepancy expansion
- custom `not-found` UI

## Project layout

```text
app/
  page.tsx
  payments/*, cards/*, cardholders/*, payees/*, bills/*, fraud/*, reporting/*, reconciliation/*
  not-found.tsx
components/
  common/          reusable UI primitives
  payments/        payments feature screens
  issuing/         cards/cardholders screens
  bills/           payees + bills screens
  observability/   fraud/reconciliation/reporting screens
  shell/           app shell/sidebar/topbar
lib/
  api/             typed API client modules
  hooks/           SWR hooks
  utils/           formatting/status/forms/reporting helpers
hooks/
  use-authorize.ts checkout authorize mutation hook
```

## Environment

`apps/web/.env.local`:

| Variable                             | Required | Description                                                 |
| ------------------------------------ | -------- | ----------------------------------------------------------- |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Yes      | Stripe publishable key (`pk_test_...`)                      |
| `NEXT_PUBLIC_API_BASE_URL`           | No       | API base URL override (defaults to `http://localhost:8000`) |
| `NEXT_PUBLIC_API_URL`                | No       | Legacy fallback for API base URL                            |

## Scripts

```bash
bun dev
bun run build
bun run start
bun run lint
bun run prettier --write
bun run test:unit
bun run test:unit:watch
```

## Local run

```bash
bun install
bun dev
```

Runs at `http://localhost:3000` and expects API at `http://localhost:8000` unless overridden.

## Validation checklist

```bash
bun run prettier --write
bunx tsc --noEmit
bun run test:unit
bun run build
```

## Manual E2E smoke

1. Start at `/`.
2. Authorize and submit test card `4242 4242 4242 4242`.
3. Confirm payment appears in `/payments` and detail page.
4. Create a payee and bill (`/payees`, `/bills/new`), execute bill from `/bills/[id]`.
5. Confirm fraud/reporting/reconciliation pages load and filter correctly.
