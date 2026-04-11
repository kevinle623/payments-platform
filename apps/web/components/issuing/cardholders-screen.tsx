"use client";

import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { PaginationBar } from "@/components/common/pagination-bar";
import {
  useCardholders,
  useCreateCardholder,
} from "@/lib/hooks/use-cardholders";
import type { Cardholder } from "@/lib/api/types";
import { formatDateTime } from "@/lib/utils/format";
import { parseNonNegativeInt } from "@/lib/utils/params";
import { useSearchParams } from "next/navigation";
import { useState } from "react";

const columns: DataTableColumn<Cardholder>[] = [
  { key: "name", header: "Name", render: (row) => row.name },
  { key: "email", header: "Email", render: (row) => row.email },
  {
    key: "status",
    header: "Status",
    render: (row) => <span className="uppercase text-xs">{row.status}</span>,
  },
  {
    key: "created_at",
    header: "Created",
    render: (row) => formatDateTime(row.created_at),
  },
];

export function CardholdersScreen() {
  const searchParams = useSearchParams();
  const limit = Math.max(1, parseNonNegativeInt(searchParams.get("limit"), 25));
  const offset = parseNonNegativeInt(searchParams.get("offset"), 0);
  const { data, error, isLoading, mutate } = useCardholders({ limit, offset });
  const createCardholder = useCreateCardholder();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  return (
    <div className="space-y-5">
      <PageHeader
        title="Cardholders"
        description="People authorized to hold issued cards"
      />

      <form
        onSubmit={async (event) => {
          event.preventDefault();
          await createCardholder.create({ name, email });
          setName("");
          setEmail("");
          await mutate();
        }}
        className="grid gap-3 rounded-xl border border-border bg-card p-4 md:grid-cols-3"
      >
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
          placeholder="Full name"
          className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
        />
        <input
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          type="email"
          required
          placeholder="Email address"
          className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
        />
        <button
          type="submit"
          disabled={createCardholder.isLoading}
          className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
        >
          {createCardholder.isLoading ? "Creating..." : "Create cardholder"}
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
        emptyTitle="No cardholders found"
        emptyDescription="Create a cardholder to issue cards."
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
