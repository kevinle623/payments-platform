"use client";

import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { useMemo } from "react";
import { useParams } from "next/navigation";
import { AmountDisplay } from "@/components/common/amount-display";
import { CopyableId } from "@/components/common/copyable-id";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { KeyValueList } from "@/components/common/key-value-list";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import {
  useCard,
  useCardAuthorizations,
  useCardBalance,
} from "@/lib/hooks/use-cards";
import type { CardAuthorization } from "@/lib/api/types";
import { formatDateTime } from "@/lib/utils/format";
import { getFirstParamValue } from "@/lib/utils/params";

export function CardDetailScreen() {
  const params = useParams<{ id: string }>();
  const cardId = getFirstParamValue(params.id);

  // Intentionally parallel, independent SWR requests.
  const card = useCard(cardId);
  const balance = useCardBalance(cardId);
  const authorizations = useCardAuthorizations(cardId, {
    limit: 100,
    offset: 0,
  });

  const authColumns = useMemo<DataTableColumn<CardAuthorization>[]>(
    () => [
      {
        key: "id",
        header: "Authorization",
        render: (row) => <CopyableId value={row.id} head={8} tail={6} />,
      },
      {
        key: "decision",
        header: "Decision",
        render: (row) => <StatusBadge domain="auth" status={row.decision} />,
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
        key: "decline_reason",
        header: "Decline reason",
        render: (row) => row.decline_reason ?? "-",
      },
      {
        key: "created_at",
        header: "Created",
        render: (row) => formatDateTime(row.created_at),
      },
    ],
    [],
  );

  return (
    <div className="space-y-5">
      <Link
        href="/cards"
        className="inline-flex items-center gap-1.5 text-sm text-foreground-muted transition-colors hover:text-foreground"
      >
        <ChevronLeft className="h-4 w-4" />
        Back to cards
      </Link>

      {card.isLoading ? (
        <LoadingSkeleton variant="card" />
      ) : card.error || !card.data ? (
        <div className="rounded-xl border border-danger-border bg-danger-bg p-4 text-sm text-danger">
          Unable to load card details.
        </div>
      ) : (
        <div className="space-y-4">
          <PageHeader
            title={`Card ${card.data.id}`}
            description="Card details and issuer activity"
          />
          <KeyValueList
            items={[
              {
                label: "Card ID",
                value: <CopyableId value={card.data.id} head={8} tail={6} />,
              },
              {
                label: "Cardholder ID",
                value: (
                  <CopyableId
                    value={card.data.cardholder_id}
                    head={8}
                    tail={6}
                  />
                ),
              },
              { label: "Status", value: card.data.status },
              {
                label: "Credit limit",
                value: (
                  <AmountDisplay
                    minorUnits={card.data.credit_limit}
                    currency={card.data.currency}
                    showCurrencySuffix
                  />
                ),
              },
              {
                label: "Available account",
                value: (
                  <CopyableId
                    value={card.data.available_balance_account_id}
                    head={8}
                    tail={6}
                  />
                ),
              },
              {
                label: "Pending holds account",
                value: (
                  <CopyableId
                    value={card.data.pending_hold_account_id}
                    head={8}
                    tail={6}
                  />
                ),
              },
              {
                label: "Created at",
                value: formatDateTime(card.data.created_at),
              },
              {
                label: "Updated at",
                value: formatDateTime(card.data.updated_at),
              },
            ]}
          />
        </div>
      )}

      {balance.isLoading ? (
        <LoadingSkeleton variant="card" />
      ) : balance.error || !balance.data ? (
        <div className="rounded-xl border border-danger-border bg-danger-bg p-4 text-sm text-danger">
          Unable to load card balance.
        </div>
      ) : (
        <KeyValueList
          items={[
            {
              label: "Credit limit",
              value: (
                <AmountDisplay
                  minorUnits={balance.data.credit_limit}
                  currency={balance.data.currency}
                  showCurrencySuffix
                />
              ),
            },
            {
              label: "Available credit",
              value: (
                <AmountDisplay
                  minorUnits={balance.data.available_credit}
                  currency={balance.data.currency}
                  showCurrencySuffix
                />
              ),
            },
            {
              label: "Pending holds",
              value: (
                <AmountDisplay
                  minorUnits={balance.data.pending_holds}
                  currency={balance.data.currency}
                  showCurrencySuffix
                />
              ),
            },
          ]}
        />
      )}

      <DataTable
        columns={authColumns}
        rows={authorizations.data}
        loading={authorizations.isLoading}
        error={authorizations.error ?? null}
        onRetry={() => {
          void authorizations.mutate();
        }}
        emptyTitle="No authorizations"
        emptyDescription="No issuer authorizations were found for this card."
      />
    </div>
  );
}
