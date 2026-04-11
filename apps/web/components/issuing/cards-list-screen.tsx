"use client";

import { ChevronRight } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { AmountDisplay } from "@/components/common/amount-display";
import { CopyableId } from "@/components/common/copyable-id";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { PaginationBar } from "@/components/common/pagination-bar";
import { useCards, useCreateCard } from "@/lib/hooks/use-cards";
import { useCardholders } from "@/lib/hooks/use-cardholders";
import type { Card } from "@/lib/api/types";
import { parseNonNegativeInt } from "@/lib/utils/params";
import { useState } from "react";

export function CardsListScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const limit = Math.max(1, parseNonNegativeInt(searchParams.get("limit"), 25));
  const offset = parseNonNegativeInt(searchParams.get("offset"), 0);

  const { data, error, isLoading, mutate } = useCards({ limit, offset });
  const { data: cardholders } = useCardholders({ limit: 200, offset: 0 });
  const createCard = useCreateCard();

  const [cardholderId, setCardholderId] = useState("");
  const [creditLimitMajor, setCreditLimitMajor] = useState("1000");
  const [currency, setCurrency] = useState("usd");
  const [lastFour, setLastFour] = useState("");

  const columns: DataTableColumn<Card>[] = [
    {
      key: "id",
      header: "Card ID",
      render: (row) => <CopyableId value={row.id} head={8} tail={6} />,
    },
    {
      key: "cardholder_id",
      header: "Cardholder",
      render: (row) => (
        <CopyableId value={row.cardholder_id} head={8} tail={6} />
      ),
    },
    {
      key: "last_four",
      header: "Last Four",
      render: (row) => (row.last_four ? `•••• ${row.last_four}` : "-"),
    },
    {
      key: "credit_limit",
      header: "Credit Limit",
      render: (row) => (
        <AmountDisplay
          minorUnits={row.credit_limit}
          currency={row.currency}
          showCurrencySuffix
        />
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (row) => <span className="uppercase text-xs">{row.status}</span>,
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
        title="Cards"
        description="Issued cards and available limits"
      />

      <form
        onSubmit={async (event) => {
          event.preventDefault();
          const creditLimit = Math.round(
            Number.parseFloat(creditLimitMajor) * 100,
          );
          await createCard.create({
            cardholder_id: cardholderId,
            credit_limit: creditLimit,
            currency,
            last_four: lastFour || null,
          });
          setCardholderId("");
          setCreditLimitMajor("1000");
          setCurrency("usd");
          setLastFour("");
          await mutate();
        }}
        className="grid gap-3 rounded-xl border border-border bg-card p-4 md:grid-cols-5"
      >
        <select
          value={cardholderId}
          onChange={(event) => setCardholderId(event.target.value)}
          required
          className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground md:col-span-2"
        >
          <option value="">Select cardholder</option>
          {cardholders.map((cardholder) => (
            <option key={cardholder.id} value={cardholder.id}>
              {cardholder.name} ({cardholder.email})
            </option>
          ))}
        </select>
        <input
          value={creditLimitMajor}
          onChange={(event) => setCreditLimitMajor(event.target.value)}
          type="number"
          step="0.01"
          min="0"
          required
          placeholder="Credit limit"
          className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
        />
        <input
          value={lastFour}
          onChange={(event) => setLastFour(event.target.value)}
          maxLength={4}
          placeholder="Last four (optional)"
          className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
        />
        <button
          type="submit"
          disabled={createCard.isLoading}
          className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
        >
          {createCard.isLoading ? "Issuing..." : "Issue card"}
        </button>
      </form>

      <DataTable
        columns={columns}
        rows={data}
        loading={isLoading}
        error={error ?? null}
        onRetry={() => {
          void mutate();
        }}
        onRowClick={(row) => router.push(`/cards/${row.id}`)}
        emptyTitle="No cards found"
        emptyDescription="Issue a card to start the issuer flow."
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
