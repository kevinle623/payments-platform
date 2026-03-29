"use client";

import { Elements } from "@stripe/react-stripe-js";
import CheckoutForm from "@/components/checkout-form";
import { useAuthorize } from "@/hooks/use-authorize";
import { stripePromise } from "@/lib/stripe";

export default function Home() {
  const { authorize, data, error, isLoading } = useAuthorize();
  const clientSecret = data?.client_secret;

  const handleAuthorize = () => {
    authorize({ amount: 5000, currency: "usd" });
  };

  return (
    <main className="flex flex-1 items-center justify-center p-6">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-xl font-semibold tracking-tight">Payment Test</h1>
          <p className="mt-1 text-sm text-muted">Stripe end-to-end checkout</p>
        </div>

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          {!clientSecret ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted">Total</span>
                <span className="font-mono font-medium">$50.00</span>
              </div>
              <div className="h-px bg-border" />
              {error && <p className="text-sm text-error">{error.message}</p>}
              <button
                onClick={handleAuthorize}
                disabled={isLoading}
                className="w-full cursor-pointer rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition-all hover:bg-accent-hover active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100"
              >
                {isLoading ? "Authorizing..." : "Continue to Payment"}
              </button>
            </div>
          ) : (
            <Elements
              stripe={stripePromise}
              options={{
                clientSecret,
                appearance: {
                  theme: "stripe",
                  variables: {
                    borderRadius: "8px",
                    fontFamily: "var(--font-geist-sans), system-ui, sans-serif",
                  },
                },
              }}
            >
              <CheckoutForm />
            </Elements>
          )}
        </div>
      </div>
    </main>
  );
}
