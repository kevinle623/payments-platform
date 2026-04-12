"use client";

import { useState } from "react";
import {
  DataTable,
  type DataTableColumn,
} from "@/components/common/data-table";
import { PageHeader } from "@/components/common/page-header";
import { PaginationBar } from "@/components/common/pagination-bar";
import { useToast } from "@/components/common/toast-provider";
import { useCreatePayee, usePayees } from "@/lib/hooks/use-payees";
import type { Payee, PayeeType } from "@/lib/api/types";
import { isDigitsOnly, normalizeCurrencyCode } from "@/lib/utils/forms";
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
  const { pushToast } = useToast();

  const [name, setName] = useState("");
  const [payeeType, setPayeeType] = useState<PayeeType>("utility");
  const [accountNumber, setAccountNumber] = useState("");
  const [routingNumber, setRoutingNumber] = useState("");
  const [currency, setCurrency] = useState("usd");
  const [formError, setFormError] = useState<string | null>(null);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!isDigitsOnly(accountNumber) || !isDigitsOnly(routingNumber)) {
      setFormError("Account and routing numbers must contain digits only.");
      pushToast({
        variant: "error",
        title: "Invalid account details",
        description: "Account and routing numbers must be numeric.",
      });
      return;
    }
    try {
      setFormError(null);
      const payee = await createPayee.create({
        name,
        payee_type: payeeType,
        account_number: accountNumber,
        routing_number: routingNumber,
        currency: normalizeCurrencyCode(currency),
      });
      await mutate((current = []) => [payee, ...current], {
        revalidate: false,
      });
      setName("");
      setPayeeType("utility");
      setAccountNumber("");
      setRoutingNumber("");
      setCurrency("usd");
      setFormError(null);
      pushToast({
        variant: "success",
        title: "Payee created",
        description: `${payee.name} is now available for bill scheduling.`,
      });
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "Failed to create payee.";
      setFormError(message);
      pushToast({
        variant: "error",
        title: "Could not create payee",
        description: message,
      });
    }
  };

  return (
    <div className="space-y-5">
      <PageHeader
        title="Payees"
        description="Manage bill recipients and destination account details"
      />

      <form
        onSubmit={onSubmit}
        className="ui-form-card grid gap-3 md:grid-cols-6"
      >
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Payee name"
          required
          className="ui-input md:col-span-2"
        />
        <select
          value={payeeType}
          onChange={(event) => setPayeeType(event.target.value as PayeeType)}
          className="ui-select"
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
          inputMode="numeric"
          pattern="[0-9]+"
          required
          className="ui-input"
        />
        <input
          value={routingNumber}
          onChange={(event) => setRoutingNumber(event.target.value)}
          placeholder="Routing number"
          inputMode="numeric"
          pattern="[0-9]+"
          required
          className="ui-input"
        />
        <div className="flex gap-2">
          <input
            value={currency}
            onChange={(event) => setCurrency(event.target.value)}
            placeholder="usd"
            required
            className="ui-input"
          />
          <button
            type="submit"
            disabled={createPayee.isLoading}
            className="ui-button-primary"
          >
            {createPayee.isLoading ? "Saving..." : "Create"}
          </button>
        </div>
        {formError ? (
          <p className="ui-inline-error md:col-span-6">{formError}</p>
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
