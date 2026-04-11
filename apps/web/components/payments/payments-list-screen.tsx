"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/common/page-header";
import { PaginationBar } from "@/components/common/pagination-bar";
import { PaymentsListTable } from "@/components/payments/payments-list-table";
import { PaymentsStatusFilter } from "@/components/payments/payments-status-filter";
import { usePayments } from "@/lib/hooks/use-payments";
import { parseNonNegativeInt } from "@/lib/utils/params";
import { parsePaymentStatus } from "@/lib/utils/payment-filters";

export function PaymentsListScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const status = parsePaymentStatus(searchParams.get("status"));
  const rawLimit = parseNonNegativeInt(searchParams.get("limit"), 25);
  const limit = rawLimit > 0 ? rawLimit : 25;
  const offset = parseNonNegativeInt(searchParams.get("offset"), 0);

  const { data, error, isLoading, mutate } = usePayments({
    status,
    limit,
    offset,
  });

  const updateQuery = (updates: Record<string, string | null | undefined>) => {
    const next = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(updates)) {
      if (!value) next.delete(key);
      else next.set(key, value);
    }
    const query = next.toString();
    router.replace(query ? `/payments?${query}` : "/payments", {
      scroll: false,
    });
  };

  return (
    <div className="space-y-5">
      <PageHeader
        title="Payments"
        description="All payment records across processors"
      />

      <PaymentsStatusFilter
        status={status}
        onStatusChange={(nextStatus) =>
          updateQuery({
            status: nextStatus ?? null,
            offset: "0",
          })
        }
      />

      <PaymentsListTable
        rows={data}
        loading={isLoading}
        error={error}
        onRetry={() => {
          void mutate();
        }}
        onRowClick={(payment) => router.push(`/payments/${payment.id}`)}
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
