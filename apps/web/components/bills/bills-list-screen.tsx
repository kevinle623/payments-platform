"use client";

import Link from "next/link";
import { ChevronRight, Plus } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { AmountDisplay } from "@/components/common/amount-display";
import { CopyableId } from "@/components/common/copyable-id";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { FilterBar } from "@/components/common/filter-bar";
import { PageHeader } from "@/components/common/page-header";
import { PaginationBar } from "@/components/common/pagination-bar";
import { StatusBadge } from "@/components/common/status-badge";
import { useBills } from "@/lib/hooks/use-bills";
import type { Bill, BillStatus } from "@/lib/api/types";
import { formatDateTime, formatRelative } from "@/lib/utils/format";
import { parseNonNegativeInt } from "@/lib/utils/params";

const BILL_STATUSES: BillStatus[] = ["active", "paused", "completed", "failed"];

function parseStatus(value: string | null): BillStatus | undefined {
  if (!value) return undefined;
  if (BILL_STATUSES.includes(value as BillStatus)) return value as BillStatus;
  return undefined;
}

export function BillsListScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const status = parseStatus(searchParams.get("status"));
  const limit = Math.max(1, parseNonNegativeInt(searchParams.get("limit"), 25));
  const offset = parseNonNegativeInt(searchParams.get("offset"), 0);

  const { data, error, isLoading, mutate } = useBills({
    status,
    limit,
    offset,
  });

  const columns: DataTableColumn<Bill>[] = [
    {
      key: "id",
      header: "Bill ID",
      render: (row) => <CopyableId value={row.id} />,
    },
    {
      key: "payee_id",
      header: "Payee",
      render: (row) => <CopyableId value={row.payee_id} head={8} tail={6} />,
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
      key: "frequency",
      header: "Frequency",
      render: (row) => (
        <span className="uppercase text-xs">{row.frequency}</span>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (row) => <StatusBadge domain="bill" status={row.status} />,
    },
    {
      key: "next_due_date",
      header: "Next due",
      render: (row) => (
        <span title={formatDateTime(row.next_due_date)}>
          {formatRelative(row.next_due_date)}
        </span>
      ),
    },
    {
      key: "chevron",
      header: "",
      align: "right",
      render: () => (
        <ChevronRight className="ml-auto h-4 w-4 text-foreground-subtle" />
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Bills"
        description="Scheduled and on-demand bill payments"
        actions={
          <Link
            href="/bills/new"
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground"
          >
            <Plus className="h-4 w-4" />
            New bill
          </Link>
        }
      />

      <FilterBar>
        {({ getValue, setValues }) => (
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <label
              htmlFor="bill-status"
              className="text-xs font-medium uppercase tracking-wide text-foreground-subtle"
            >
              Status
            </label>
            <select
              id="bill-status"
              value={getValue("status")}
              onChange={(event) => {
                const nextStatus = event.target.value || null;
                setValues({ status: nextStatus, offset: "0" });
              }}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground sm:w-64"
            >
              <option value="">All statuses</option>
              {BILL_STATUSES.map((entry) => (
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
        onRowClick={(row) => router.push(`/bills/${row.id}`)}
        emptyTitle="No bills found"
        emptyDescription="Create a bill to schedule recurring or one-time payments."
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
