"use client";

import Link from "next/link";
import { ChevronLeft, Play } from "lucide-react";
import { useParams } from "next/navigation";
import { AmountDisplay } from "@/components/common/amount-display";
import { CopyableId } from "@/components/common/copyable-id";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { KeyValueList } from "@/components/common/key-value-list";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { useToast } from "@/components/common/toast-provider";
import { useBill, useExecuteBill, useUpdateBill } from "@/lib/hooks/use-bills";
import { useCard } from "@/lib/hooks/use-cards";
import { usePayees } from "@/lib/hooks/use-payees";
import type { BillPayment } from "@/lib/api/types";
import { formatDateTime } from "@/lib/utils/format";
import { getFirstParamValue } from "@/lib/utils/params";
import { useState } from "react";

function getErrorMessage(value: unknown): string {
  if (value instanceof Error) return value.message;
  return "Request failed. Please try again.";
}

export function BillDetailScreen() {
  const params = useParams<{ id: string }>();
  const billId = getFirstParamValue(params.id);
  const { data, error, isLoading, mutate } = useBill(billId);
  const card = useCard(data?.bill.card_id);
  const executeBill = useExecuteBill();
  const updateBill = useUpdateBill();
  const { data: payees } = usePayees({ limit: 500, offset: 0 });
  const { pushToast } = useToast();
  const [actionError, setActionError] = useState<string | null>(null);

  const columns: DataTableColumn<BillPayment>[] = [
    {
      key: "id",
      header: "Execution ID",
      render: (row) => <CopyableId value={row.id} head={8} tail={6} />,
    },
    {
      key: "payment_id",
      header: "Payment",
      render: (row) =>
        row.payment_id ? (
          <Link
            href={`/payments/${row.payment_id}`}
            className="font-mono text-primary hover:text-primary-hover"
          >
            {row.payment_id}
          </Link>
        ) : (
          "-"
        ),
    },
    {
      key: "status",
      header: "Status",
      render: (row) => <StatusBadge domain="bill" status={row.status} />,
    },
    {
      key: "executed_at",
      header: "Executed",
      render: (row) => formatDateTime(row.executed_at),
    },
  ];

  if (isLoading) {
    return (
      <div className="space-y-4">
        <LoadingSkeleton variant="card" />
        <LoadingSkeleton variant="table" />
      </div>
    );
  }

  if (error) {
    return <ErrorState error={error} onRetry={() => void mutate()} />;
  }

  if (!data) {
    return (
      <EmptyState
        title="Bill not found"
        description="No bill data was returned for this ID."
      />
    );
  }

  const bill = data.bill;
  const payee = payees.find((entry) => entry.id === bill.payee_id);
  const canToggleStatus = bill.status === "active" || bill.status === "paused";
  const nextStatus = bill.status === "active" ? "paused" : "active";
  const nextStatusLabel = nextStatus === "paused" ? "Pause" : "Resume";

  const handleExecute = async () => {
    if (!billId) return;
    const confirmed = window.confirm("Execute this bill now?");
    if (!confirmed) return;

    try {
      setActionError(null);
      const response = await executeBill.execute(billId);
      await mutate(
        (current) =>
          current
            ? {
                bill: response.bill,
                payments: [response.bill_payment, ...current.payments],
              }
            : current,
        { revalidate: false },
      );
      pushToast({
        variant: "success",
        title: "Bill executed",
        description: "A new execution record was created.",
      });
    } catch (err) {
      const message = getErrorMessage(err);
      setActionError(message);
      pushToast({
        variant: "error",
        title: "Could not execute bill",
        description: message,
      });
    }
  };

  const handleStatusToggle = async () => {
    if (!billId) return;
    const action = nextStatus === "paused" ? "pause" : "resume";
    const confirmed = window.confirm(
      `Are you sure you want to ${action} this bill?`,
    );
    if (!confirmed) return;

    try {
      setActionError(null);
      await mutate(
        async (current) => {
          const updatedBill = await updateBill.update(billId, {
            status: nextStatus,
          });
          if (!current) return current;
          return {
            ...current,
            bill: updatedBill,
          };
        },
        {
          optimisticData: {
            ...data,
            bill: {
              ...data.bill,
              status: nextStatus,
              updated_at: new Date().toISOString(),
            },
          },
          rollbackOnError: true,
          revalidate: false,
        },
      );
      pushToast({
        variant: "success",
        title: `Bill ${action}d`,
        description: `Bill is now ${nextStatus}.`,
      });
    } catch (err) {
      const message = getErrorMessage(err);
      setActionError(message);
      pushToast({
        variant: "error",
        title: `Could not ${action} bill`,
        description: message,
      });
    }
  };

  return (
    <div className="space-y-5">
      <Link
        href="/bills"
        className="inline-flex items-center gap-1.5 text-sm text-foreground-muted transition-colors hover:text-foreground"
      >
        <ChevronLeft className="h-4 w-4" />
        Back to bills
      </Link>

      <div className="rounded-xl border border-border bg-card p-4">
        <PageHeader
          title={`Bill ${bill.id}`}
          description="Execution history and lifecycle controls"
          actions={
            <div className="flex items-center gap-2">
              <StatusBadge domain="bill" status={bill.status} />
              <button
                type="button"
                disabled={executeBill.isLoading}
                onClick={handleExecute}
                className="inline-flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm text-foreground hover:bg-card-hover disabled:opacity-50"
              >
                <Play className="h-4 w-4" />
                {executeBill.isLoading ? "Executing..." : "Execute now"}
              </button>
              {canToggleStatus ? (
                <button
                  type="button"
                  disabled={updateBill.isLoading}
                  onClick={handleStatusToggle}
                  className="rounded-md border border-border px-3 py-1.5 text-sm text-foreground hover:bg-card-hover disabled:opacity-50"
                >
                  {updateBill.isLoading ? "Saving..." : nextStatusLabel}
                </button>
              ) : null}
            </div>
          }
          className="border-none pb-0"
        />
        {actionError ? (
          <p className="mt-3 text-sm text-danger">{actionError}</p>
        ) : null}
      </div>

      <KeyValueList
        items={[
          {
            label: "Bill ID",
            value: <CopyableId value={bill.id} head={8} tail={6} />,
          },
          {
            label: "Payee",
            value: payee ? (
              <div className="space-y-0.5">
                <p>{payee.name}</p>
                <p className="text-xs text-foreground-subtle">
                  {payee.payee_type}
                </p>
              </div>
            ) : (
              <CopyableId value={bill.payee_id} head={8} tail={6} />
            ),
          },
          {
            label: "Card ID",
            value: bill.card_id ? (
              <Link
                href={`/cards/${bill.card_id}`}
                className="text-primary hover:text-primary-hover"
              >
                {card.data?.last_four
                  ? `•••• ${card.data.last_four}`
                  : bill.card_id.slice(0, 8)}
              </Link>
            ) : (
              "-"
            ),
          },
          {
            label: "Amount",
            value: (
              <AmountDisplay
                minorUnits={bill.amount}
                currency={bill.currency}
                showCurrencySuffix
              />
            ),
          },
          { label: "Frequency", value: bill.frequency },
          { label: "Next due", value: formatDateTime(bill.next_due_date) },
          { label: "Created at", value: formatDateTime(bill.created_at) },
          { label: "Updated at", value: formatDateTime(bill.updated_at) },
        ]}
      />

      <DataTable
        columns={columns}
        rows={data.payments}
        emptyTitle="No executions yet"
        emptyDescription="This bill has not been executed yet."
      />
    </div>
  );
}
