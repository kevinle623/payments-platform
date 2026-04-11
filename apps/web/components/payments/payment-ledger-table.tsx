import { useMemo } from "react";
import { AmountDisplay } from "@/components/common/amount-display";
import { CopyableId } from "@/components/common/copyable-id";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import type { LedgerTransaction } from "@/lib/api/types";
import { formatDateTime, formatRelative } from "@/lib/utils/format";
import { buildLedgerRows, type LedgerRow } from "@/lib/utils/payment-detail";

interface PaymentLedgerTableProps {
  transactions: LedgerTransaction[];
}

export function PaymentLedgerTable({ transactions }: PaymentLedgerTableProps) {
  const rows = useMemo(() => buildLedgerRows(transactions), [transactions]);

  const columns = useMemo<DataTableColumn<LedgerRow>[]>(
    () => [
      {
        key: "transaction_description",
        header: "Transaction",
        render: (row) => (
          <div>
            <p className="text-sm text-foreground">
              {row.transaction_description}
            </p>
            <p className="font-mono text-xs text-foreground-subtle">
              {row.transaction_id}
            </p>
          </div>
        ),
      },
      {
        key: "account_id",
        header: "Account",
        render: (row) => <CopyableId value={row.account_id} />,
      },
      {
        key: "debit",
        header: "Debit",
        align: "right",
        render: (row) =>
          row.amount > 0 ? (
            <AmountDisplay minorUnits={row.amount} currency={row.currency} />
          ) : (
            <span className="text-foreground-subtle">-</span>
          ),
      },
      {
        key: "credit",
        header: "Credit",
        align: "right",
        render: (row) =>
          row.amount < 0 ? (
            <AmountDisplay
              minorUnits={Math.abs(row.amount)}
              currency={row.currency}
            />
          ) : (
            <span className="text-foreground-subtle">-</span>
          ),
      },
      {
        key: "currency",
        header: "Currency",
        render: (row) => (
          <span className="text-xs uppercase tracking-wide text-foreground-muted">
            {row.currency}
          </span>
        ),
      },
      {
        key: "created_at",
        header: "Created",
        render: (row) => (
          <span title={formatDateTime(row.created_at)}>
            {formatRelative(row.created_at)}
          </span>
        ),
      },
    ],
    [],
  );

  return (
    <DataTable
      columns={columns}
      rows={rows}
      emptyTitle="No ledger transactions"
      emptyDescription="No ledger entries were recorded for this payment."
    />
  );
}
