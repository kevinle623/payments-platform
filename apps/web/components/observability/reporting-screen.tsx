"use client";

import { useSearchParams } from "next/navigation";
import { AmountDisplay } from "@/components/common/amount-display";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { FilterBar } from "@/components/common/filter-bar";
import { PageHeader } from "@/components/common/page-header";
import { ReportingCharts } from "@/components/observability/reporting-charts";
import { useReportingSummary } from "@/lib/hooks/use-reporting";
import type { ReportingSummaryRow } from "@/lib/api/types";
import { formatDate } from "@/lib/utils/format";

export function ReportingScreen() {
  const searchParams = useSearchParams();
  const since = searchParams.get("since") ?? "";
  const until = searchParams.get("until") ?? "";

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
        {({ getValue, setValues }) => (
          <div className="grid gap-3 sm:grid-cols-3">
            <label className="space-y-1 text-sm">
              <span className="ui-field-label">Since</span>
              <input
                type="date"
                value={getValue("since")}
                onChange={(event) =>
                  setValues({ since: event.target.value || null })
                }
                className="ui-input"
              />
            </label>
            <label className="space-y-1 text-sm">
              <span className="ui-field-label">Until</span>
              <input
                type="date"
                value={getValue("until")}
                onChange={(event) =>
                  setValues({ until: event.target.value || null })
                }
                className="ui-input"
              />
            </label>
            <div className="flex items-end">
              <button
                type="button"
                onClick={() => setValues({ since: null, until: null })}
                className="ui-button-secondary"
              >
                Clear dates
              </button>
            </div>
          </div>
        )}
      </FilterBar>

      {!isLoading && !error ? <ReportingCharts rows={data} /> : null}

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
