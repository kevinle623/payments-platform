"use client";

import { AmountDisplay } from "@/components/common/amount-display";
import { EmptyState } from "@/components/common/empty-state";
import type { ReportingSummaryRow } from "@/lib/api/types";
import { formatDate } from "@/lib/utils/format";
import {
  buildReportingCurrencySeries,
  buildReportingEventTotals,
} from "@/lib/utils/reporting";

function sparklinePath(
  values: number[],
  width: number,
  height: number,
): string {
  if (values.length === 0) return "";
  if (values.length === 1) {
    const y = height / 2;
    return `M 0 ${y} L ${width} ${y}`;
  }

  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = Math.max(1, max - min);
  const stepX = width / (values.length - 1);

  return values
    .map((value, index) => {
      const x = index * stepX;
      const normalized = (value - min) / range;
      const y = height - normalized * height;
      return `${index === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");
}

export function ReportingCharts({ rows }: { rows: ReportingSummaryRow[] }) {
  const currencySeries = buildReportingCurrencySeries(rows);
  const eventTotals = buildReportingEventTotals(rows);

  if (rows.length === 0) {
    return (
      <EmptyState
        title="No chart data"
        description="Reporting charts will appear when the selected range has data."
      />
    );
  }

  return (
    <section className="space-y-4">
      {currencySeries.map((series) => {
        const maxAmount = Math.max(
          ...series.points.map((point) => Math.abs(point.totalAmount)),
          1,
        );
        const sparkline = sparklinePath(
          series.points.map((point) => point.count),
          240,
          48,
        );
        const topEvents = eventTotals
          .filter((entry) => entry.currency === series.currency)
          .slice(0, 4);
        const maxEventAmount = Math.max(
          ...topEvents.map((entry) => Math.abs(entry.totalAmount)),
          1,
        );

        return (
          <div
            key={series.currency}
            className="rounded-xl border border-border bg-card p-4"
          >
            <div className="mb-3 flex flex-wrap items-end justify-between gap-3 border-b border-border pb-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-foreground-subtle">
                  Currency
                </p>
                <p className="text-lg font-semibold uppercase text-foreground">
                  {series.currency}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-xs text-foreground-subtle">Total amount</p>
                  <p className="text-sm font-semibold text-foreground">
                    <AmountDisplay
                      minorUnits={series.totalAmount}
                      currency={series.currency}
                      showCurrencySuffix
                    />
                  </p>
                </div>
                <div>
                  <p className="text-xs text-foreground-subtle">Total events</p>
                  <p className="text-sm font-semibold text-foreground">
                    {series.totalCount.toLocaleString()}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-[1.2fr,1fr]">
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-wide text-foreground-subtle">
                  Daily Amount
                </p>
                {series.points.map((point) => {
                  const widthPct = Math.max(
                    3,
                    (Math.abs(point.totalAmount) / maxAmount) * 100,
                  );
                  return (
                    <div
                      key={point.date}
                      className="grid grid-cols-[88px,1fr,auto] items-center gap-2"
                    >
                      <span className="text-xs text-foreground-muted">
                        {formatDate(point.date)}
                      </span>
                      <div className="h-2 overflow-hidden rounded-full bg-background">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${widthPct}%` }}
                        />
                      </div>
                      <span className="text-xs text-foreground">
                        <AmountDisplay
                          minorUnits={point.totalAmount}
                          currency={series.currency}
                          showCurrencySuffix
                        />
                      </span>
                    </div>
                  );
                })}
              </div>

              <div className="space-y-3">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-foreground-subtle">
                    Daily Count Trend
                  </p>
                  <div className="mt-2 rounded-lg border border-border bg-background px-2 py-2">
                    <svg
                      viewBox="0 0 240 48"
                      className="h-12 w-full"
                      preserveAspectRatio="none"
                      aria-label={`Daily event count trend for ${series.currency}`}
                    >
                      <path
                        d={sparkline}
                        stroke="var(--primary)"
                        strokeWidth="2"
                        fill="none"
                        strokeLinecap="round"
                      />
                    </svg>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-wide text-foreground-subtle">
                    Top Event Types
                  </p>
                  {topEvents.map((entry) => {
                    const widthPct = Math.max(
                      3,
                      (Math.abs(entry.totalAmount) / maxEventAmount) * 100,
                    );
                    return (
                      <div key={entry.eventType} className="space-y-1">
                        <div className="flex items-center justify-between gap-2 text-xs">
                          <span className="text-foreground">
                            {entry.eventType}
                          </span>
                          <span className="text-foreground-muted">
                            {entry.count.toLocaleString()} events
                          </span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-background">
                          <div
                            className="h-full rounded-full bg-info"
                            style={{ width: `${widthPct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </section>
  );
}
