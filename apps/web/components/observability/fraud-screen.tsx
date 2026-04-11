"use client";

import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { FilterBar } from "@/components/common/filter-bar";
import { PageHeader } from "@/components/common/page-header";
import { PaginationBar } from "@/components/common/pagination-bar";
import { StatusBadge } from "@/components/common/status-badge";
import { useFraudSignals } from "@/lib/hooks/use-fraud";
import type { FraudSignal, RiskLevel } from "@/lib/api/types";
import { AmountDisplay } from "@/components/common/amount-display";
import { formatDateTime, formatRelative } from "@/lib/utils/format";
import { parseNonNegativeInt } from "@/lib/utils/params";
import { useSearchParams } from "next/navigation";

const RISK_LEVELS: RiskLevel[] = ["low", "high"];

function parseRiskLevel(value: string | null): RiskLevel | undefined {
  if (!value) return undefined;
  return RISK_LEVELS.includes(value as RiskLevel)
    ? (value as RiskLevel)
    : undefined;
}

export function FraudScreen() {
  const searchParams = useSearchParams();
  const riskLevel = parseRiskLevel(searchParams.get("risk_level"));
  const limit = Math.max(1, parseNonNegativeInt(searchParams.get("limit"), 25));
  const offset = parseNonNegativeInt(searchParams.get("offset"), 0);

  const { data, error, isLoading, mutate } = useFraudSignals({
    risk_level: riskLevel,
    limit,
    offset,
  });

  const columns: DataTableColumn<FraudSignal>[] = [
    { key: "id", header: "Signal ID", render: (row) => row.id },
    {
      key: "payment_id",
      header: "Payment ID",
      render: (row) => row.payment_id,
    },
    {
      key: "risk_level",
      header: "Risk",
      render: (row) => <StatusBadge domain="fraud" status={row.risk_level} />,
    },
    {
      key: "amount",
      header: "Amount",
      render: (row) => (
        <AmountDisplay
          minorUnits={row.amount}
          currency={row.currency}
          showCurrencySuffix
        />
      ),
    },
    {
      key: "flagged_at",
      header: "Flagged",
      render: (row) => (
        <span title={formatDateTime(row.flagged_at)}>
          {formatRelative(row.flagged_at)}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Fraud Signals"
        description="Risk signals generated from payment events"
      />

      <FilterBar>
        {({ getValue, setValues }) => (
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <label
              htmlFor="risk-level"
              className="text-xs font-medium uppercase tracking-wide text-foreground-subtle"
            >
              Risk
            </label>
            <select
              id="risk-level"
              value={getValue("risk_level")}
              onChange={(event) =>
                setValues({
                  risk_level: event.target.value || null,
                  offset: "0",
                })
              }
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground sm:w-64"
            >
              <option value="">All levels</option>
              {RISK_LEVELS.map((entry) => (
                <option key={entry} value={entry}>
                  {entry}
                </option>
              ))}
            </select>
          </div>
        )}
      </FilterBar>

      <DataTable
        columns={columns}
        rows={data}
        loading={isLoading}
        error={error ?? null}
        onRetry={() => {
          void mutate();
        }}
        emptyTitle="No fraud signals"
        emptyDescription="No fraud signals matched the current filter."
      />

      <PaginationBar
        limit={limit}
        offset={offset}
        currentCount={data.length}
        hasNextPage={data.length === limit}
      />
    </div>
  );
}
