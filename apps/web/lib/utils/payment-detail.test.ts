import { describe, expect, it } from "vitest";
import type { LedgerTransaction, OutboxEvent } from "@/lib/api/types";
import {
  buildLedgerRows,
  buildPaymentTimelineItems,
  formatEventLabel,
} from "@/lib/utils/payment-detail";

describe("formatEventLabel", () => {
  it("converts dotted event names into title-cased labels", () => {
    expect(formatEventLabel("payment.settled")).toBe("Payment Settled");
    expect(formatEventLabel("hold.cleared")).toBe("Hold Cleared");
  });
});

describe("buildLedgerRows", () => {
  it("flattens ledger transactions into entry rows", () => {
    const transactions: LedgerTransaction[] = [
      {
        id: "txn_1",
        description: "authorization",
        created_at: "2026-04-11T00:00:00Z",
        entries: [
          {
            id: "entry_1",
            account_id: "acc_1",
            amount: 5000,
            currency: "usd",
            created_at: "2026-04-11T00:00:00Z",
          },
          {
            id: "entry_2",
            account_id: "acc_2",
            amount: -5000,
            currency: "usd",
            created_at: "2026-04-11T00:00:00Z",
          },
        ],
      },
    ];

    const rows = buildLedgerRows(transactions);
    expect(rows).toHaveLength(2);
    expect(rows[0]).toMatchObject({
      id: "entry_1",
      transaction_id: "txn_1",
      transaction_description: "authorization",
      amount: 5000,
    });
    expect(rows[1]).toMatchObject({
      id: "entry_2",
      transaction_id: "txn_1",
      amount: -5000,
    });
  });
});

describe("buildPaymentTimelineItems", () => {
  it("sorts events by created_at and maps outbox status variants", () => {
    const events: OutboxEvent[] = [
      {
        id: "event_2",
        event_type: "payment.settled",
        payload: {},
        status: "published",
        created_at: "2026-04-11T00:01:00Z",
        published_at: "2026-04-11T00:01:10Z",
      },
      {
        id: "event_1",
        event_type: "payment.authorized",
        payload: {},
        status: "pending",
        created_at: "2026-04-11T00:00:00Z",
        published_at: null,
      },
    ];

    const items = buildPaymentTimelineItems(events);
    expect(items).toHaveLength(2);
    expect(items[0]).toMatchObject({
      label: "Payment Authorized",
      variant: "warning",
    });
    expect(items[1]).toMatchObject({
      label: "Payment Settled",
      variant: "success",
    });
  });
});
