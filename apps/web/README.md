# payments-platform/apps/web

Dummy frontend for end-to-end Stripe payment testing. Calls the FastAPI backend to authorize a payment, then uses Stripe Elements to collect card details and confirm the payment intent.

Current status (April 4, 2026): this app is still checkout-only. Backend bill payments (`/payees`, `/bills`) and issuer observability APIs are available, and the next web initiative is the dashboard pages for payments, issuer, bills, fraud, reconciliation, and reporting.

## Tech stack

- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS v4
- Bun
- Stripe.js / React Stripe
- SWR

## Project structure

```
app/
  layout.tsx          Root layout (Geist font, global styles)
  page.tsx            Payment page (authorize + Stripe Elements)
  globals.css         Tailwind + CSS variables
components/
  checkout-form.tsx   Stripe PaymentElement form
hooks/
  use-authorize.ts    SWR mutation hook for payment authorization
lib/
  payments.ts         API service layer (authorize endpoint)
  stripe.ts           Stripe.js singleton
```

## Getting started

```bash
# Install dependencies
bun install

# Add your Stripe publishable key
echo 'NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY' > .env.local

# Start dev server
bun dev
```

Runs at `http://localhost:3000`. Requires the FastAPI backend running at `http://localhost:8000`.

## Environment variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key (`pk_test_...`) |
| `NEXT_PUBLIC_API_URL` | API base URL (default: `http://localhost:8000`) |

## Test flow

1. Click **Continue to Payment**
2. Enter test card `4242 4242 4242 4242` (any future expiry, any CVC)
3. Click **Pay $50.00**
4. Stripe fires a webhook to the backend, settling the payment and writing ledger entries
