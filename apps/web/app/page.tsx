"use client";

import { Elements } from "@stripe/react-stripe-js";
import CheckoutForm from "@/components/payments/checkout-form";
import { useAuthorize } from "@/hooks/use-authorize";
import { stripePromise } from "@/lib/stripe";

export default function Home() {
  const { authorize, data, error, isLoading } = useAuthorize();
  const clientSecret = data?.client_secret;

  const handleAuthorize = () => {
    authorize({ amount: 5000, currency: "usd" });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Overview
        </h1>
        <p className="mt-1 text-sm text-foreground-muted">
          Test the end-to-end Stripe checkout flow.
        </p>
      </div>

      <div className="max-w-sm rounded-xl border border-border bg-card p-6 shadow-lg">
        <div className="mb-5">
          <p className="text-sm text-foreground-muted">Test checkout</p>
          <p className="mt-1 text-xs text-foreground-subtle">
            Authorizes a $50.00 payment via Stripe.
          </p>
        </div>

        {!clientSecret ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-foreground-muted">Total</span>
              <span className="font-mono font-medium text-foreground">
                $50.00
              </span>
            </div>
            <div className="h-px bg-border" />
            {error && <p className="text-sm text-danger">{error.message}</p>}
            <button
              onClick={handleAuthorize}
              disabled={isLoading}
              className="w-full cursor-pointer rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-all hover:bg-primary-hover active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100"
            >
              {isLoading ? "Authorizing..." : "Continue to Payment"}
            </button>
          </div>
        ) : (
          <Elements
            stripe={stripePromise}
            options={{
              clientSecret,
              fonts: [
                {
                  cssSrc:
                    "https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap",
                },
              ],
              appearance: {
                theme: "night",
                variables: {
                  borderRadius: "8px",
                  colorBackground: "#0f0f12",
                  colorText: "#fafafa",
                  colorPrimary: "#6366f1",
                  fontFamily: "Geist, system-ui, -apple-system, sans-serif",
                },
              },
            }}
          >
            <CheckoutForm />
          </Elements>
        )}
      </div>
    </div>
  );
}
