import { describe, expect, it } from "vitest";
import type { ReportingSummaryRow } from "@/lib/api/types";
import {
  buildReportingCurrencySeries,
  buildReportingEventTotals,
} from "@/lib/utils/reporting";

const ROWS: ReportingSummaryRow[] = [
  {
    date: "2026-04-10",
    event_type: "payment.authorized",
    currency: "usd",
    total_amount: 1500,
    count: 3,
  },
  {
    date: "2026-04-10",
    event_type: "payment.refunded",
    currency: "usd",
    total_amount: -200,
    count: 1,
  },
  {
    date: "2026-04-11",
    event_type: "payment.authorized",
    currency: "usd",
    total_amount: 2500,
    count: 5,
  },
  {
    date: "2026-04-11",
    event_type: "bill.executed",
    currency: "eur",
    total_amount: 900,
    count: 2,
  },
];

describe("buildReportingCurrencySeries", () => {
  it("groups rows by currency and date with sorted daily points", () => {
    const result = buildReportingCurrencySeries(ROWS);

    expect(result).toHaveLength(2);
    expect(result[0].currency).toBe("eur");
    expect(result[0].totalAmount).toBe(900);
    expect(result[0].totalCount).toBe(2);

    expect(result[1].currency).toBe("usd");
    expect(result[1].points).toEqual([
      { date: "2026-04-10", totalAmount: 1300, count: 4 },
      { date: "2026-04-11", totalAmount: 2500, count: 5 },
    ]);
    expect(result[1].totalAmount).toBe(3800);
    expect(result[1].totalCount).toBe(9);
  });
});

describe("buildReportingEventTotals", () => {
  it("groups by currency + event type and sorts by total amount desc", () => {
    const result = buildReportingEventTotals(ROWS);

    expect(result).toEqual([
      {
        currency: "eur",
        eventType: "bill.executed",
        totalAmount: 900,
        count: 2,
      },
      {
        currency: "usd",
        eventType: "payment.authorized",
        totalAmount: 4000,
        count: 8,
      },
      {
        currency: "usd",
        eventType: "payment.refunded",
        totalAmount: -200,
        count: 1,
      },
    ]);
  });
});
