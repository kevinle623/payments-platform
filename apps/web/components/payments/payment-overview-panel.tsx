import { AmountDisplay } from "@/components/common/amount-display";
import { CopyableId } from "@/components/common/copyable-id";
import { KeyValueList } from "@/components/common/key-value-list";
import { StatusBadge } from "@/components/common/status-badge";
import type { PaymentRecord } from "@/lib/api/types";
import { formatDateTime } from "@/lib/utils/format";

interface PaymentOverviewPanelProps {
  payment: PaymentRecord;
}

export function PaymentOverviewPanel({ payment }: PaymentOverviewPanelProps) {
  return (
    <KeyValueList
      items={[
        {
          label: "ID",
          value: <CopyableId value={payment.id} head={8} tail={6} />,
        },
        {
          label: "Processor payment ID",
          value: payment.processor_payment_id ? (
            <CopyableId
              value={payment.processor_payment_id}
              head={8}
              tail={6}
            />
          ) : (
            "-"
          ),
        },
        {
          label: "Status",
          value: <StatusBadge domain="payment" status={payment.status} />,
        },
        {
          label: "Amount",
          value: (
            <AmountDisplay
              minorUnits={payment.amount}
              currency={payment.currency}
              showCurrencySuffix
            />
          ),
        },
        { label: "Currency", value: payment.currency.toUpperCase() },
        {
          label: "Idempotency key",
          value: (
            <CopyableId value={payment.idempotency_key} head={8} tail={6} />
          ),
        },
        { label: "Created at", value: formatDateTime(payment.created_at) },
        { label: "Updated at", value: formatDateTime(payment.updated_at) },
      ]}
    />
  );
}
