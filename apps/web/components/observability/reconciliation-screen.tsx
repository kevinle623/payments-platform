"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { CopyableId } from "@/components/common/copyable-id";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { PaginationBar } from "@/components/common/pagination-bar";
import {
  useDiscrepancies,
  useReconciliationRuns,
} from "@/lib/hooks/use-reconciliation";
import type {
  ReconciliationDiscrepancy,
  ReconciliationRun,
} from "@/lib/api/types";
import { formatDateTime } from "@/lib/utils/format";
import { parseNonNegativeInt } from "@/lib/utils/params";
import { useSearchParams } from "next/navigation";

function DiscrepanciesList({
  runId,
  enabled,
}: {
  runId: string;
  enabled: boolean;
}) {
  const { data, error, isLoading, mutate } = useDiscrepancies(
    runId,
    { limit: 100, offset: 0 },
    enabled,
  );

  const columns: DataTableColumn<ReconciliationDiscrepancy>[] = [
    {
      key: "id",
      header: "Discrepancy ID",
      render: (row) => <CopyableId value={row.id} />,
    },
    {
      key: "payment_id",
      header: "Payment ID",
      render: (row) => <CopyableId value={row.payment_id} />,
    },
    {
      key: "processor_payment_id",
      header: "Processor ID",
      render: (row) => row.processor_payment_id,
    },
    {
      key: "our_status",
      header: "Our status",
      render: (row) => row.our_status,
    },
    {
      key: "stripe_status",
      header: "Processor status",
      render: (row) => row.stripe_status,
    },
    {
      key: "detected_at",
      header: "Detected",
      render: (row) => formatDateTime(row.detected_at),
    },
  ];

  return (
    <div className="mt-3">
      <DataTable
        columns={columns}
        rows={data}
        loading={isLoading}
        error={error ?? null}
        onRetry={() => {
          void mutate();
        }}
        emptyTitle="No discrepancies"
        emptyDescription="No mismatches were found for this run."
      />
    </div>
  );
}

export function ReconciliationScreen() {
  const searchParams = useSearchParams();
  const limit = Math.max(1, parseNonNegativeInt(searchParams.get("limit"), 25));
  const offset = parseNonNegativeInt(searchParams.get("offset"), 0);
  const [expandedRunIds, setExpandedRunIds] = useState<Record<string, boolean>>(
    {},
  );

  const { data, error, isLoading, mutate } = useReconciliationRuns({
    limit,
    offset,
  });

  const columns: DataTableColumn<ReconciliationRun>[] = [
    {
      key: "id",
      header: "Run ID",
      render: (row) => <CopyableId value={row.id} head={8} tail={6} />,
    },
    {
      key: "started_at",
      header: "Started",
      render: (row) => formatDateTime(row.started_at),
    },
    {
      key: "completed_at",
      header: "Completed",
      render: (row) =>
        row.completed_at ? formatDateTime(row.completed_at) : "-",
    },
    {
      key: "checked",
      header: "Checked",
      align: "right",
      render: (row) => row.checked.toLocaleString(),
    },
    {
      key: "mismatches",
      header: "Mismatches",
      align: "right",
      render: (row) => row.mismatches.toLocaleString(),
    },
  ];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Reconciliation"
        description="Run history and mismatch details"
      />

      <DataTable
        columns={columns}
        rows={data}
        loading={isLoading}
        error={error ?? null}
        onRetry={() => {
          void mutate();
        }}
        emptyTitle="No reconciliation runs"
        emptyDescription="No reconciliation runs are available yet."
      />

      {data.map((run) => {
        const expanded = Boolean(expandedRunIds[run.id]);
        return (
          <div
            key={run.id}
            className="rounded-xl border border-border bg-card p-3"
          >
            <button
              type="button"
              onClick={() =>
                setExpandedRunIds((prev) => ({ ...prev, [run.id]: !expanded }))
              }
              className="flex w-full items-center justify-between text-left text-sm text-foreground"
            >
              <span className="inline-flex items-center gap-2">
                {expanded ? (
                  <ChevronDown className="h-4 w-4 text-foreground-subtle" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-foreground-subtle" />
                )}
                Run {run.id}
              </span>
              <span className="text-foreground-muted">
                {run.mismatches} mismatches
              </span>
            </button>
            {expanded ? (
              <DiscrepanciesList runId={run.id} enabled={expanded} />
            ) : null}
          </div>
        );
      })}

      <PaginationBar
        limit={limit}
        offset={offset}
        currentCount={data.length}
        hasNextPage={data.length === limit}
      />
    </div>
  );
}
