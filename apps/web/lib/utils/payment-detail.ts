import type { LedgerTransaction, OutboxEvent } from "@/lib/api/types";
import { getStatusMeta, type StatusVariant } from "@/lib/utils/status";

export interface LedgerRow {
  id: string;
  transaction_id: string;
  transaction_description: string;
  account_id: string;
  amount: number;
  currency: string;
  created_at: string;
}

export interface PaymentTimelineItem {
  label: string;
  timestamp: string;
  variant: StatusVariant;
}

export function formatEventLabel(eventType: string): string {
  return eventType
    .split(".")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function buildLedgerRows(
  transactions: LedgerTransaction[],
): LedgerRow[] {
  return transactions.flatMap((transaction) =>
    transaction.entries.map((entry) => ({
      id: entry.id,
      transaction_id: transaction.id,
      transaction_description: transaction.description,
      account_id: entry.account_id,
      amount: entry.amount,
      currency: entry.currency,
      created_at: entry.created_at,
    })),
  );
}

export function buildPaymentTimelineItems(
  events: OutboxEvent[],
): PaymentTimelineItem[] {
  return [...events]
    .sort(
      (a, b) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    )
    .map((event) => ({
      label: formatEventLabel(event.event_type),
      timestamp: event.created_at,
      variant: getStatusMeta("outbox", event.status).variant,
    }));
}
