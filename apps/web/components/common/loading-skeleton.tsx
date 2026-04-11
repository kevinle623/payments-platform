import { cn } from "@/lib/utils/cn";

interface LoadingSkeletonProps {
  variant?: "table" | "card";
  rows?: number;
  className?: string;
}

export function LoadingSkeleton({
  variant = "card",
  rows = 5,
  className,
}: LoadingSkeletonProps) {
  if (variant === "table") {
    return (
      <div
        className={cn(
          "overflow-hidden rounded-xl border border-border bg-card",
          className,
        )}
      >
        <div className="grid grid-cols-4 gap-3 border-b border-border px-4 py-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={`header-${index}`}
              className="h-3 w-20 animate-pulse rounded bg-card-hover"
            />
          ))}
        </div>
        <div className="divide-y divide-border">
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <div
              key={`row-${rowIndex}`}
              className="grid grid-cols-4 gap-3 px-4 py-3"
            >
              {Array.from({ length: 4 }).map((__, colIndex) => (
                <div
                  key={`cell-${rowIndex}-${colIndex}`}
                  className="h-3 animate-pulse rounded bg-card-hover"
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "space-y-3 rounded-xl border border-border bg-card p-4",
        className,
      )}
    >
      <div className="h-5 w-40 animate-pulse rounded bg-card-hover" />
      <div className="h-4 w-64 animate-pulse rounded bg-card-hover" />
      <div className="h-px bg-border" />
      <div className="h-4 w-full animate-pulse rounded bg-card-hover" />
      <div className="h-4 w-5/6 animate-pulse rounded bg-card-hover" />
      <div className="h-4 w-3/4 animate-pulse rounded bg-card-hover" />
    </div>
  );
}
