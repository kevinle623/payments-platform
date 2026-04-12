// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReportingCharts } from "@/components/observability/reporting-charts";
import type { ReportingSummaryRow } from "@/lib/api/types";

describe("ReportingCharts", () => {
  it("renders per-currency chart sections and top event labels", () => {
    const rows: ReportingSummaryRow[] = [
      {
        date: "2026-04-10",
        event_type: "payment.authorized",
        currency: "usd",
        total_amount: 1500,
        count: 3,
      },
      {
        date: "2026-04-11",
        event_type: "payment.authorized",
        currency: "usd",
        total_amount: 500,
        count: 1,
      },
      {
        date: "2026-04-11",
        event_type: "bill.executed",
        currency: "eur",
        total_amount: 800,
        count: 2,
      },
    ];

    render(<ReportingCharts rows={rows} />);

    expect(
      screen.getByLabelText("Daily event count trend for usd"),
    ).toBeTruthy();
    expect(
      screen.getByLabelText("Daily event count trend for eur"),
    ).toBeTruthy();
    expect(screen.getAllByText("Top Event Types")).toHaveLength(2);
    expect(screen.getByText("payment.authorized")).toBeTruthy();
    expect(screen.getByText("bill.executed")).toBeTruthy();
  });
});
