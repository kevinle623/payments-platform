import { cn } from "@/lib/utils/cn";
import { getStatusMeta, type StatusDomain } from "@/lib/utils/status";

interface StatusBadgeProps {
  domain: StatusDomain;
  status: string | null | undefined;
  className?: string;
}

const VARIANT_CLASSNAMES = {
  neutral: "border-border bg-card text-foreground-muted",
  info: "border-info-border bg-info-bg text-info",
  success: "border-success-border bg-success-bg text-success",
  warning: "border-warning-border bg-warning-bg text-warning",
  danger: "border-danger-border bg-danger-bg text-danger",
  muted: "border-muted-border bg-muted-bg text-foreground-muted",
} as const;

export function StatusBadge({ domain, status, className }: StatusBadgeProps) {
  const meta = getStatusMeta(domain, status);

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        VARIANT_CLASSNAMES[meta.variant],
        className,
      )}
    >
      {meta.label}
    </span>
  );
}
