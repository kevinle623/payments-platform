import { AlertTriangle } from "lucide-react";
import { ApiError } from "@/lib/api/client";
import { cn } from "@/lib/utils/cn";

interface ErrorStateProps {
  error: ApiError | Error;
  onRetry?: () => void;
  className?: string;
}

function getErrorHeadline(error: ApiError | Error): string {
  if (error instanceof ApiError) {
    return `Request failed (${error.status})`;
  }
  return "Something went wrong";
}

export function ErrorState({ error, onRetry, className }: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border border-danger-border bg-danger-bg px-6 py-10 text-center",
        className,
      )}
    >
      <div className="rounded-full border border-danger-border p-2.5">
        <AlertTriangle className="h-5 w-5 text-danger" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-semibold text-danger">
          {getErrorHeadline(error)}
        </p>
        <p className="text-sm text-foreground-muted">{error.message}</p>
      </div>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center rounded-md border border-danger-border px-3 py-1.5 text-sm font-medium text-danger transition-colors hover:bg-danger/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}
