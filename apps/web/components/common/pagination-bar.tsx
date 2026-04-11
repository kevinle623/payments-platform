"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils/cn";

interface PaginationBarProps {
  limit: number;
  offset: number;
  currentCount: number;
  hasNextPage: boolean;
  pageSizeOptions?: number[];
  className?: string;
}

export function PaginationBar({
  limit,
  offset,
  currentCount,
  hasNextPage,
  pageSizeOptions = [25, 50, 100],
  className,
}: PaginationBarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const page = Math.floor(offset / Math.max(limit, 1)) + 1;
  const start = currentCount === 0 ? 0 : offset + 1;
  const end = offset + currentCount;
  const canGoPrev = offset > 0;
  const canGoNext = hasNextPage;

  const updateParams = (updates: Record<string, string | null>) => {
    const next = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(updates)) {
      if (!value) next.delete(key);
      else next.set(key, value);
    }
    const query = next.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, {
      scroll: false,
    });
  };

  const handlePrev = () => {
    if (!canGoPrev) return;
    updateParams({ offset: String(Math.max(0, offset - limit)) });
  };

  const handleNext = () => {
    if (!canGoNext) return;
    updateParams({ offset: String(offset + limit) });
  };

  const handleLimitChange = (value: number) => {
    updateParams({ limit: String(value), offset: "0" });
  };

  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-xl border border-border bg-card px-4 py-3 sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      <div className="text-sm text-foreground-muted">
        {currentCount > 0 ? (
          <>
            <span className="text-foreground">{start}</span>-
            <span className="text-foreground">{end}</span>
          </>
        ) : (
          "0"
        )}{" "}
        on page <span className="text-foreground">{page}</span>
      </div>

      <div className="flex items-center gap-2">
        <label htmlFor="page-size" className="text-xs text-foreground-subtle">
          Rows
        </label>
        <select
          id="page-size"
          value={limit}
          onChange={(event) => handleLimitChange(Number(event.target.value))}
          className="rounded-md border border-border bg-background px-2 py-1.5 text-sm text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {pageSizeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={handlePrev}
          disabled={!canGoPrev}
          className="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1.5 text-sm text-foreground transition-colors hover:bg-card-hover disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronLeft className="h-4 w-4" />
          Prev
        </button>

        <button
          type="button"
          onClick={handleNext}
          disabled={!canGoNext}
          className="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1.5 text-sm text-foreground transition-colors hover:bg-card-hover disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
