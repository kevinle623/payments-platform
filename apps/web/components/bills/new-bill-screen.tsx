"use client";

import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { useCreateBill } from "@/lib/hooks/use-bills";
import { useCards } from "@/lib/hooks/use-cards";
import { usePayees } from "@/lib/hooks/use-payees";
import type { BillFrequency } from "@/lib/api/types";

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
  const createBill = useCreateBill();

  const [payeeId, setPayeeId] = useState("");
  const [cardId, setCardId] = useState("");
  const [amountMajor, setAmountMajor] = useState("0.00");
  const [currency, setCurrency] = useState("usd");
  const [frequency, setFrequency] = useState<BillFrequency>("monthly");
  const [nextDueDate, setNextDueDate] = useState("");

  const canSubmit = useMemo(
    () =>
      Boolean(payeeId && amountMajor && currency && frequency && nextDueDate),
    [payeeId, amountMajor, currency, frequency, nextDueDate],
  );

  if (payeesError || cardsError) {
    return (
      <ErrorState
        error={payeesError ?? cardsError ?? new Error("Unknown error")}
      />
    );
  }

  if (payeesLoading || cardsLoading) {
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
          const parsedAmount = Number.parseFloat(amountMajor);
          const minorUnits = Math.round(parsedAmount * 100);
          const dueIso = new Date(`${nextDueDate}T00:00:00.000Z`).toISOString();

          const bill = await createBill.create({
            payee_id: payeeId,
            card_id: cardId || null,
            amount: minorUnits,
            currency,
            frequency,
            next_due_date: dueIso,
          });

          router.push(`/bills/${bill.id}`);
        }}
        className="grid gap-4 rounded-xl border border-border bg-card p-4 md:grid-cols-2"
      >
        <label className="space-y-1 text-sm">
          <span className="text-foreground-muted">Payee</span>
          <select
            value={payeeId}
            onChange={(event) => setPayeeId(event.target.value)}
            required
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-foreground"
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
          <span className="text-foreground-muted">Linked card (optional)</span>
          <select
            value={cardId}
            onChange={(event) => setCardId(event.target.value)}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-foreground"
          >
            <option value="">No linked card</option>
            {cards.map((card) => (
              <option key={card.id} value={card.id}>
                {card.last_four ? `•••• ${card.last_four}` : card.id}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-1 text-sm">
          <span className="text-foreground-muted">Amount (major units)</span>
          <input
            value={amountMajor}
            onChange={(event) => setAmountMajor(event.target.value)}
            type="number"
            step="0.01"
            min="0"
            required
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-foreground"
          />
        </label>

        <label className="space-y-1 text-sm">
          <span className="text-foreground-muted">Currency</span>
          <input
            value={currency}
            onChange={(event) => setCurrency(event.target.value)}
            required
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-foreground"
          />
        </label>

        <label className="space-y-1 text-sm">
          <span className="text-foreground-muted">Frequency</span>
          <select
            value={frequency}
            onChange={(event) =>
              setFrequency(event.target.value as BillFrequency)
            }
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-foreground"
          >
            {FREQUENCIES.map((entry) => (
              <option key={entry} value={entry}>
                {entry}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-1 text-sm">
          <span className="text-foreground-muted">Next due date</span>
          <input
            type="date"
            value={nextDueDate}
            onChange={(event) => setNextDueDate(event.target.value)}
            required
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-foreground"
          />
        </label>

        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={!canSubmit || createBill.isLoading}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {createBill.isLoading ? "Creating..." : "Create bill"}
          </button>
        </div>
      </form>
    </div>
  );
}
