import { cn } from "@/lib/utils/cn";
import { formatDateTime } from "@/lib/utils/format";
import type { StatusVariant } from "@/lib/utils/status";

interface TimelineItem {
  label: string;
  timestamp: string;
  variant?: StatusVariant;
}

interface TimelineProps {
  items: TimelineItem[];
  className?: string;
}

const DOT_CLASSNAMES: Record<StatusVariant, string> = {
  neutral: "border-border bg-card",
  info: "border-info-border bg-info",
  success: "border-success-border bg-success",
  warning: "border-warning-border bg-warning",
  danger: "border-danger-border bg-danger",
  muted: "border-muted-border bg-foreground-subtle",
};

export function Timeline({ items, className }: TimelineProps) {
  return (
    <ol
      className={cn("rounded-xl border border-border bg-card p-4", className)}
    >
      {items.map((item, index) => (
        <li key={`${item.label}-${item.timestamp}`} className="relative pl-6">
          {index < items.length - 1 ? (
            <span
              className="absolute left-[7px] top-4 h-[calc(100%-4px)] w-px bg-border"
              aria-hidden="true"
            />
          ) : null}
          <span
            className={cn(
              "absolute left-0 top-1.5 h-3.5 w-3.5 rounded-full border-2",
              DOT_CLASSNAMES[item.variant ?? "neutral"],
            )}
            aria-hidden="true"
          />
          <div className={cn("pb-4", index === items.length - 1 && "pb-0")}>
            <p className="text-sm font-medium text-foreground">{item.label}</p>
            <p className="text-xs text-foreground-muted">
              {formatDateTime(item.timestamp)}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
