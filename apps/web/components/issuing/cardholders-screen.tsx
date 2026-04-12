"use client";

import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { PaginationBar } from "@/components/common/pagination-bar";
import { useToast } from "@/components/common/toast-provider";
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
  const { pushToast } = useToast();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  return (
    <div className="space-y-5">
      <PageHeader
        title="Cardholders"
        description="People authorized to hold issued cards"
      />

      <form
        onSubmit={async (event) => {
          event.preventDefault();
          try {
            setFormError(null);
            const cardholder = await createCardholder.create({
              name: name.trim(),
              email: email.trim(),
            });
            await mutate((current = []) => [cardholder, ...current], {
              revalidate: false,
            });
            setName("");
            setEmail("");
            setFormError(null);
            pushToast({
              variant: "success",
              title: "Cardholder created",
              description: `${cardholder.name} can now receive issued cards.`,
            });
          } catch (submitError) {
            const message =
              submitError instanceof Error
                ? submitError.message
                : "Failed to create cardholder.";
            setFormError(message);
            pushToast({
              variant: "error",
              title: "Could not create cardholder",
              description: message,
            });
          }
        }}
        className="ui-form-card grid gap-3 md:grid-cols-3"
      >
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
          placeholder="Full name"
          className="ui-input"
        />
        <input
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          type="email"
          required
          placeholder="Email address"
          className="ui-input"
        />
        <button
          type="submit"
          disabled={createCardholder.isLoading}
          className="ui-button-primary"
        >
          {createCardholder.isLoading ? "Creating..." : "Create cardholder"}
        </button>
        {formError ? (
          <p className="ui-inline-error md:col-span-3">{formError}</p>
        ) : null}
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
