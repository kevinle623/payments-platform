import type { PaymentStatus } from "@/lib/api/types";

export const PAYMENT_STATUSES: PaymentStatus[] = [
  "pending",
  "succeeded",
  "failed",
  "refunded",
  "disputed",
];

export function parsePaymentStatus(
  value: string | null,
): PaymentStatus | undefined {
  if (!value) return undefined;
  if (PAYMENT_STATUSES.includes(value as PaymentStatus)) {
    return value as PaymentStatus;
  }
  return undefined;
}
