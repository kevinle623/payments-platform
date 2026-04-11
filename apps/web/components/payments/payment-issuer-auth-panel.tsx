import Link from "next/link";
import { AmountDisplay } from "@/components/common/amount-display";
import { CopyableId } from "@/components/common/copyable-id";
import { EmptyState } from "@/components/common/empty-state";
import { KeyValueList } from "@/components/common/key-value-list";
import { StatusBadge } from "@/components/common/status-badge";
import type { IssuerAuthorization } from "@/lib/api/types";
import { formatDateTime, truncateId } from "@/lib/utils/format";

interface PaymentIssuerAuthPanelProps {
  issuerAuth: IssuerAuthorization | null;
}

export function PaymentIssuerAuthPanel({
  issuerAuth,
}: PaymentIssuerAuthPanelProps) {
  if (!issuerAuth) {
    return (
      <EmptyState
        title="No issuer authorization"
        description="This payment has no linked issuer authorization."
      />
    );
  }

  return (
    <KeyValueList
      items={[
        {
          label: "Decision",
          value: <StatusBadge domain="auth" status={issuerAuth.decision} />,
        },
        { label: "Decline reason", value: issuerAuth.decline_reason ?? "-" },
        {
          label: "Card ID",
          value: issuerAuth.card_id ? (
            <div className="flex items-center gap-2">
              <Link
                href={`/cards/${issuerAuth.card_id}`}
                className="font-mono text-primary transition-colors hover:text-primary-hover"
              >
                {truncateId(issuerAuth.card_id, 8, 6)}
              </Link>
              <CopyableId value={issuerAuth.card_id} head={8} tail={6} />
            </div>
          ) : (
            "-"
          ),
        },
        {
          label: "Amount",
          value: (
            <AmountDisplay
              minorUnits={issuerAuth.amount}
              currency={issuerAuth.currency}
              showCurrencySuffix
            />
          ),
        },
        {
          label: "Idempotency key",
          value: (
            <CopyableId value={issuerAuth.idempotency_key} head={8} tail={6} />
          ),
        },
        {
          label: "Created at",
          value: formatDateTime(issuerAuth.created_at),
        },
      ]}
    />
  );
}
