import { FilterBar } from "@/components/common/filter-bar";
import type { PaymentStatus } from "@/lib/api/types";
import { PAYMENT_STATUSES } from "@/lib/utils/payment-filters";

interface PaymentsStatusFilterProps {
  status?: PaymentStatus;
  onStatusChange: (status?: PaymentStatus) => void;
}

export function PaymentsStatusFilter({
  status,
  onStatusChange,
}: PaymentsStatusFilterProps) {
  return (
    <FilterBar>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <label
          htmlFor="payment-status"
          className="text-xs font-medium uppercase tracking-wide text-foreground-subtle"
        >
          Status
        </label>
        <select
          id="payment-status"
          value={status ?? ""}
          onChange={(event) =>
            onStatusChange((event.target.value as PaymentStatus) || undefined)
          }
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:w-64"
        >
          <option value="">All statuses</option>
          {PAYMENT_STATUSES.map((entry) => (
            <option key={entry} value={entry}>
              {entry}
            </option>
          ))}
        </select>
      </div>
    </FilterBar>
  );
}
