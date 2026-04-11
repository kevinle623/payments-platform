"use client";

import { useState } from "react";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { PaginationBar } from "@/components/common/pagination-bar";
import { useCreatePayee, usePayees } from "@/lib/hooks/use-payees";
import type { Payee, PayeeType } from "@/lib/api/types";
import { formatDateTime, truncateId } from "@/lib/utils/format";
import { parseNonNegativeInt } from "@/lib/utils/params";
import { useSearchParams } from "next/navigation";

const PAYEE_TYPES: PayeeType[] = [
  "utility",
  "credit_card",
  "mortgage",
  "other",
];

const columns: DataTableColumn<Payee>[] = [
  {
    key: "name",
    header: "Name",
    render: (row) => <span className="font-medium">{row.name}</span>,
  },
  {
    key: "payee_type",
    header: "Type",
    render: (row) => (
      <span className="uppercase text-xs">{row.payee_type}</span>
    ),
  },
  {
    key: "account_number",
    header: "Account",
    render: (row) => (
      <span className="font-mono text-xs">
        {truncateId(row.account_number, 2, 4)}
      </span>
    ),
  },
  {
    key: "routing_number",
    header: "Routing",
    render: (row) => (
      <span className="font-mono text-xs">
        {truncateId(row.routing_number, 2, 4)}
      </span>
    ),
  },
  {
    key: "currency",
    header: "Currency",
    render: (row) => <span className="uppercase text-xs">{row.currency}</span>,
  },
  {
    key: "created_at",
    header: "Created",
    render: (row) => formatDateTime(row.created_at),
  },
];

export function PayeesScreen() {
  const searchParams = useSearchParams();
  const limit = Math.max(1, parseNonNegativeInt(searchParams.get("limit"), 25));
  const offset = parseNonNegativeInt(searchParams.get("offset"), 0);

  const { data, error, isLoading, mutate } = usePayees({ limit, offset });
  const createPayee = useCreatePayee();

  const [name, setName] = useState("");
  const [payeeType, setPayeeType] = useState<PayeeType>("utility");
  const [accountNumber, setAccountNumber] = useState("");
  const [routingNumber, setRoutingNumber] = useState("");
  const [currency, setCurrency] = useState("usd");

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    await createPayee.create({
      name,
      payee_type: payeeType,
      account_number: accountNumber,
      routing_number: routingNumber,
      currency,
    });
    setName("");
    setPayeeType("utility");
    setAccountNumber("");
    setRoutingNumber("");
    setCurrency("usd");
    await mutate();
  };

  return (
    <div className="space-y-5">
      <PageHeader
        title="Payees"
        description="Manage bill recipients and destination account details"
      />

      <form
        onSubmit={onSubmit}
        className="grid gap-3 rounded-xl border border-border bg-card p-4 md:grid-cols-6"
      >
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Payee name"
          required
          className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground md:col-span-2"
        />
        <select
          value={payeeType}
          onChange={(event) => setPayeeType(event.target.value as PayeeType)}
          className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
        >
          {PAYEE_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
        <input
          value={accountNumber}
          onChange={(event) => setAccountNumber(event.target.value)}
          placeholder="Account number"
          required
          className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
        />
        <input
          value={routingNumber}
          onChange={(event) => setRoutingNumber(event.target.value)}
          placeholder="Routing number"
          required
          className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
        />
        <div className="flex gap-2">
          <input
            value={currency}
            onChange={(event) => setCurrency(event.target.value)}
            placeholder="usd"
            required
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
          />
          <button
            type="submit"
            disabled={createPayee.isLoading}
            className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {createPayee.isLoading ? "Saving..." : "Create"}
          </button>
        </div>
      </form>

      <DataTable
        columns={columns}
        rows={data}
        loading={isLoading}
        error={error ?? null}
        onRetry={() => {
          void mutate();
        }}
        emptyTitle="No payees yet"
        emptyDescription="Create a payee to start scheduling bills."
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
