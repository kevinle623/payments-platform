import { Tabs } from "@/components/common/tabs";
import { PaymentIssuerAuthPanel } from "@/components/payments/payment-issuer-auth-panel";
import { PaymentLedgerTable } from "@/components/payments/payment-ledger-table";
import { PaymentOutboxEvents } from "@/components/payments/payment-outbox-events";
import type { PaymentDetailResponse } from "@/lib/api/types";

interface PaymentDetailTabsProps {
  detail: PaymentDetailResponse;
}

export function PaymentDetailTabs({ detail }: PaymentDetailTabsProps) {
  return (
    <Tabs
      tabs={[
        {
          id: "ledger",
          label: "Ledger",
          content: (
            <PaymentLedgerTable transactions={detail.ledger_transactions} />
          ),
        },
        {
          id: "outbox",
          label: "Outbox events",
          content: <PaymentOutboxEvents events={detail.outbox_events} />,
        },
        {
          id: "issuer-auth",
          label: "Issuer auth",
          content: (
            <PaymentIssuerAuthPanel issuerAuth={detail.issuer_authorization} />
          ),
        },
      ]}
    />
  );
}
