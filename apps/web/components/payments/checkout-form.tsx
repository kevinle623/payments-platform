"use client";

import { useState } from "react";
import {
  PaymentElement,
  useStripe,
  useElements,
} from "@stripe/react-stripe-js";

export default function CheckoutForm() {
  const stripe = useStripe();
  const elements = useElements();
  const [status, setStatus] = useState<
    "idle" | "processing" | "succeeded" | "failed"
  >("idle");
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stripe || !elements) return;

    setStatus("processing");
    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: window.location.href },
      redirect: "if_required",
    });

    if (error) {
      setStatus("failed");
      setMessage(error.message ?? "Payment failed");
    } else {
      setStatus("succeeded");
      setMessage("Payment confirmed. Webhook will settle the ledger.");
    }
  };

  const isDisabled =
    !stripe || status === "processing" || status === "succeeded";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <PaymentElement />
      {message && (
        <p
          className={`text-sm ${
            status === "succeeded" ? "text-success" : "text-danger"
          }`}
        >
          {message}
        </p>
      )}
      <button
        type="submit"
        disabled={isDisabled}
        className="w-full cursor-pointer rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-all hover:bg-primary-hover active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100"
      >
        {status === "processing"
          ? "Processing..."
          : status === "succeeded"
            ? "Done"
            : "Pay $50.00"}
      </button>
    </form>
  );
}
