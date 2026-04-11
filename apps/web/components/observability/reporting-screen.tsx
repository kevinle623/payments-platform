"use client";

import { useState } from "react";
import { AmountDisplay } from "@/components/common/amount-display";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { FilterBar } from "@/components/common/filter-bar";
import { PageHeader } from "@/components/common/page-header";
import { useReportingSummary } from "@/lib/hooks/use-reporting";
import type { ReportingSummaryRow } from "@/lib/api/types";
import { formatDate } from "@/lib/utils/format";

export function ReportingScreen() {
  const [since, setSince] = useState("");
  const [until, setUntil] = useState("");

  const { data, error, isLoading, mutate } = useReportingSummary({
    since: since ? new Date(`${since}T00:00:00.000Z`).toISOString() : undefined,
    until: until ? new Date(`${until}T23:59:59.999Z`).toISOString() : undefined,
  });

  const columns: DataTableColumn<ReportingSummaryRow>[] = [
    {
      key: "date",
      header: "Date",
      render: (row) => formatDate(row.date),
    },
    {
      key: "event_type",
      header: "Event type",
      render: (row) => row.event_type,
    },
    {
      key: "currency",
      header: "Currency",
      render: (row) => row.currency.toUpperCase(),
    },
    {
      key: "count",
      header: "Count",
      align: "right",
      render: (row) => row.count.toLocaleString(),
    },
    {
      key: "total_amount",
      header: "Total amount",
      align: "right",
      render: (row) => (
        <AmountDisplay
          minorUnits={row.total_amount}
          currency={row.currency}
          showCurrencySuffix
        />
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Reporting"
        description="Daily reporting summary by event type and currency"
      />

      <FilterBar>
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="space-y-1 text-sm">
            <span className="text-foreground-muted">Since</span>
            <input
              type="date"
              value={since}
              onChange={(event) => setSince(event.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-foreground"
            />
          </label>
          <label className="space-y-1 text-sm">
            <span className="text-foreground-muted">Until</span>
            <input
              type="date"
              value={until}
              onChange={(event) => setUntil(event.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-foreground"
            />
          </label>
          <div className="flex items-end">
            <button
              type="button"
              onClick={() => {
                setSince("");
                setUntil("");
              }}
              className="rounded-md border border-border px-3 py-2 text-sm text-foreground hover:bg-card-hover"
            >
              Clear dates
            </button>
          </div>
        </div>
      </FilterBar>

      <DataTable
        columns={columns}
        rows={data}
        loading={isLoading}
        error={error ?? null}
        onRetry={() => {
          void mutate();
        }}
        emptyTitle="No reporting rows"
        emptyDescription="No reporting records match the current date range."
      />
    </div>
  );
}
