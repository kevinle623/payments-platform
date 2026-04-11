import { AmountDisplay } from "@/components/common/amount-display";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import type { PaymentRecord } from "@/lib/api/types";

interface PaymentDetailHeaderProps {
  payment: PaymentRecord;
}

export function PaymentDetailHeader({ payment }: PaymentDetailHeaderProps) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4 sm:flex-row sm:items-start sm:justify-between">
      <PageHeader
        title={`Payment ${payment.id}`}
        description="Payment details, ledger impact, and event history"
        actions={<StatusBadge domain="payment" status={payment.status} />}
        className="w-full border-none pb-0"
      />
      <AmountDisplay
        minorUnits={payment.amount}
        currency={payment.currency}
        showCurrencySuffix
        className="text-xl font-semibold"
      />
    </div>
  );
}
