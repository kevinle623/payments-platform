import type { ReactNode } from "react";
import type { ApiError } from "@/lib/api/client";
import { cn } from "@/lib/utils/cn";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";

type ColumnAlign = "left" | "center" | "right";

const ALIGN_CLASSNAMES: Record<ColumnAlign, string> = {
  left: "text-left",
  center: "text-center",
  right: "text-right",
};

export interface DataTableColumn<T> {
  key: keyof T | string;
  header: ReactNode;
  align?: ColumnAlign;
  render?: (row: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  loading?: boolean;
  error?: ApiError | Error | null;
  onRetry?: () => void;
  onRowClick?: (row: T) => void;
  getRowKey?: (row: T, index: number) => string;
  emptyTitle?: string;
  emptyDescription?: string;
  className?: string;
}

function defaultGetRowKey<T extends object>(row: T, index: number): string {
  const rowWithOptionalId = row as { id?: string };
  return rowWithOptionalId.id ?? `row-${index}`;
}

export function DataTable<T extends object>({
  columns,
  rows,
  loading = false,
  error = null,
  onRetry,
  onRowClick,
  getRowKey = defaultGetRowKey,
  emptyTitle = "No results",
  emptyDescription = "No data matched the current filters.",
  className,
}: DataTableProps<T>) {
  if (loading) {
    return <LoadingSkeleton variant="table" className={className} />;
  }

  if (error) {
    return <ErrorState error={error} onRetry={onRetry} className={className} />;
  }

  if (rows.length === 0) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        className={className}
      />
    );
  }

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-border bg-card",
        className,
      )}
    >
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-background">
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className={cn(
                    "px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-foreground-subtle",
                    ALIGN_CLASSNAMES[column.align ?? "left"],
                    column.className,
                  )}
                  scope="col"
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row, rowIndex) => {
              const rowKey = getRowKey(row, rowIndex);
              return (
                <tr
                  key={rowKey}
                  className={cn(
                    "transition-colors",
                    onRowClick
                      ? "cursor-pointer hover:bg-card-hover focus-within:bg-card-hover"
                      : "hover:bg-card-hover",
                  )}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                >
                  {columns.map((column) => {
                    const content = column.render
                      ? column.render(row)
                      : String(
                          (row as Record<string, unknown>)[
                            String(column.key)
                          ] ?? "",
                        );

                    return (
                      <td
                        key={`${rowKey}-${String(column.key)}`}
                        className={cn(
                          "px-4 py-3 text-sm text-foreground",
                          ALIGN_CLASSNAMES[column.align ?? "left"],
                          column.className,
                        )}
                      >
                        {content}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
