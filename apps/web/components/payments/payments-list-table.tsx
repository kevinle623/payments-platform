import { ChevronRight } from "lucide-react";
import { useMemo } from "react";
import { AmountDisplay } from "@/components/common/amount-display";
import { CopyableId } from "@/components/common/copyable-id";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { StatusBadge } from "@/components/common/status-badge";
import type { ApiError } from "@/lib/api/client";
import type { PaymentRecord } from "@/lib/api/types";
import { formatDateTime, formatRelative, truncateId } from "@/lib/utils/format";

interface PaymentsListTableProps {
  rows: PaymentRecord[];
  loading?: boolean;
  error?: ApiError | Error;
  onRetry?: () => void;
  onRowClick: (payment: PaymentRecord) => void;
}

export function PaymentsListTable({
  rows,
  loading = false,
  error,
  onRetry,
  onRowClick,
}: PaymentsListTableProps) {
  const columns = useMemo<DataTableColumn<PaymentRecord>[]>(
    () => [
      {
        key: "id",
        header: "Payment ID",
        render: (payment) => <CopyableId value={payment.id} />,
      },
      {
        key: "amount",
        header: "Amount",
        render: (payment) => (
          <AmountDisplay
            minorUnits={payment.amount}
            currency={payment.currency}
            showCurrencySuffix
          />
        ),
      },
      {
        key: "currency",
        header: "Currency",
        render: (payment) => (
          <span className="text-xs uppercase tracking-wide text-foreground-muted">
            {payment.currency}
          </span>
        ),
      },
      {
        key: "status",
        header: "Status",
        render: (payment) => (
          <StatusBadge domain="payment" status={payment.status} />
        ),
      },
      {
        key: "processor_payment_id",
        header: "Processor ID",
        render: (payment) =>
          payment.processor_payment_id ? (
            <span className="font-mono text-xs text-foreground-muted">
              {truncateId(payment.processor_payment_id, 8, 6)}
            </span>
          ) : (
            <span className="text-foreground-subtle">-</span>
          ),
      },
      {
        key: "created_at",
        header: "Created",
        render: (payment) => (
          <span title={formatDateTime(payment.created_at)}>
            {formatRelative(payment.created_at)}
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
    ],
    [],
  );

  return (
    <DataTable
      columns={columns}
      rows={rows}
      loading={loading}
      error={error ?? null}
      onRetry={onRetry}
      onRowClick={onRowClick}
      emptyTitle="No payments found"
      emptyDescription="Try adjusting filters or create a new payment from checkout."
    />
  );
}
