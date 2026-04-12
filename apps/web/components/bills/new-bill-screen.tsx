"use client";

import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { useToast } from "@/components/common/toast-provider";
import { useCreateBill } from "@/lib/hooks/use-bills";
import { useCards } from "@/lib/hooks/use-cards";
import { useCardholders } from "@/lib/hooks/use-cardholders";
import { usePayees } from "@/lib/hooks/use-payees";
import type { BillFrequency } from "@/lib/api/types";
import {
  normalizeCurrencyCode,
  parseMajorAmountToMinor,
} from "@/lib/utils/forms";

const FREQUENCIES: BillFrequency[] = [
  "one_time",
  "weekly",
  "biweekly",
  "monthly",
];

export function NewBillScreen() {
  const router = useRouter();
  const {
    data: payees,
    error: payeesError,
    isLoading: payeesLoading,
  } = usePayees({
    limit: 200,
    offset: 0,
  });
  const {
    data: cards,
    error: cardsError,
    isLoading: cardsLoading,
  } = useCards({
    limit: 200,
    offset: 0,
  });
  const {
    data: cardholders,
    error: cardholdersError,
    isLoading: cardholdersLoading,
  } = useCardholders({
    limit: 500,
    offset: 0,
  });
  const createBill = useCreateBill();
  const { pushToast } = useToast();

  const [payeeId, setPayeeId] = useState("");
  const [cardId, setCardId] = useState("");
  const [amountMajor, setAmountMajor] = useState("0.00");
  const [currency, setCurrency] = useState("usd");
  const [frequency, setFrequency] = useState<BillFrequency>("monthly");
  const [nextDueDate, setNextDueDate] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const cardholderById = useMemo(
    () => new Map(cardholders.map((cardholder) => [cardholder.id, cardholder])),
    [cardholders],
  );

  const canSubmit = useMemo(
    () =>
      Boolean(payeeId && amountMajor && currency && frequency && nextDueDate),
    [payeeId, amountMajor, currency, frequency, nextDueDate],
  );

  if (payeesError || cardsError || cardholdersError) {
    return (
      <ErrorState
        error={
          payeesError ??
          cardsError ??
          cardholdersError ??
          new Error("Unknown error")
        }
      />
    );
  }

  if (payeesLoading || cardsLoading || cardholdersLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-4 text-sm text-foreground-muted">
        Loading dependencies...
      </div>
    );
  }

  if (payees.length === 0) {
    return (
      <EmptyState
        title="No payees available"
        description="Create at least one payee before creating a bill."
        action={
          <Link
            href="/payees"
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground"
          >
            Go to payees
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-5">
      <Link
        href="/bills"
        className="inline-flex items-center gap-1.5 text-sm text-foreground-muted transition-colors hover:text-foreground"
      >
        <ChevronLeft className="h-4 w-4" />
        Back to bills
      </Link>

      <PageHeader
        title="New Bill"
        description="Create a recurring or one-time bill schedule"
      />

      <form
        onSubmit={async (event) => {
          event.preventDefault();
          const minorUnits = parseMajorAmountToMinor(amountMajor);
          if (minorUnits === null) {
            setFormError("Amount must be greater than 0.");
            pushToast({
              variant: "error",
              title: "Invalid amount",
              description: "Amount must be greater than 0.",
            });
            return;
          }
          try {
            const dueIso = new Date(
              `${nextDueDate}T00:00:00.000Z`,
            ).toISOString();
            const normalizedCurrency = normalizeCurrencyCode(currency);
            setFormError(null);

            const bill = await createBill.create({
              payee_id: payeeId,
              card_id: cardId || null,
              amount: minorUnits,
              currency: normalizedCurrency,
              frequency,
              next_due_date: dueIso,
            });

            pushToast({
              variant: "success",
              title: "Bill created",
              description: "Schedule created successfully.",
            });
            router.push(`/bills/${bill.id}`);
          } catch (submitError) {
            const message =
              submitError instanceof Error
                ? submitError.message
                : "Failed to create bill.";
            setFormError(message);
            pushToast({
              variant: "error",
              title: "Could not create bill",
              description: message,
            });
          }
        }}
        className="ui-form-card grid gap-4 md:grid-cols-2"
      >
        <label className="space-y-1 text-sm">
          <span className="ui-field-label">Payee</span>
          <select
            value={payeeId}
            onChange={(event) => setPayeeId(event.target.value)}
            required
            className="ui-select"
          >
            <option value="">Select payee</option>
            {payees.map((payee) => (
              <option key={payee.id} value={payee.id}>
                {payee.name}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-1 text-sm">
          <span className="ui-field-label">Linked card (optional)</span>
          <select
            value={cardId}
            onChange={(event) => setCardId(event.target.value)}
            className="ui-select"
          >
            <option value="">No linked card</option>
            {cards.map((card) => {
              const cardholder = cardholderById.get(card.cardholder_id);
              const prefix = cardholder
                ? `${cardholder.name} · `
                : `${card.cardholder_id.slice(0, 8)} · `;
              const label = card.last_four
                ? `${prefix}•••• ${card.last_four}`
                : `${prefix}${card.id.slice(0, 8)}`;
              return (
                <option key={card.id} value={card.id}>
                  {label}
                </option>
              );
            })}
          </select>
        </label>

        <label className="space-y-1 text-sm">
          <span className="ui-field-label">Amount (major units)</span>
          <input
            value={amountMajor}
            onChange={(event) => setAmountMajor(event.target.value)}
            type="number"
            step="0.01"
            min="0.01"
            required
            className="ui-input"
          />
        </label>

        <label className="space-y-1 text-sm">
          <span className="ui-field-label">Currency</span>
          <input
            value={currency}
            onChange={(event) => setCurrency(event.target.value)}
            required
            className="ui-input"
          />
        </label>

        <label className="space-y-1 text-sm">
          <span className="ui-field-label">Frequency</span>
          <select
            value={frequency}
            onChange={(event) =>
              setFrequency(event.target.value as BillFrequency)
            }
            className="ui-select"
          >
            {FREQUENCIES.map((entry) => (
              <option key={entry} value={entry}>
                {entry}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-1 text-sm">
          <span className="ui-field-label">Next due date</span>
          <input
            type="date"
            value={nextDueDate}
            onChange={(event) => setNextDueDate(event.target.value)}
            required
            className="ui-input"
          />
        </label>

        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={!canSubmit || createBill.isLoading}
            className="ui-button-primary"
          >
            {createBill.isLoading ? "Creating..." : "Create bill"}
          </button>
          {formError ? <p className="ui-inline-error">{formError}</p> : null}
        </div>
      </form>
    </div>
  );
}
