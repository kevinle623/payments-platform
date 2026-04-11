import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

interface KeyValueItem {
  label: string;
  value: ReactNode;
}

interface KeyValueListProps {
  items: KeyValueItem[];
  className?: string;
}

export function KeyValueList({ items, className }: KeyValueListProps) {
  return (
    <dl
      className={cn(
        "grid grid-cols-1 gap-3 rounded-xl border border-border bg-card p-4 sm:grid-cols-[180px_1fr]",
        className,
      )}
    >
      {items.map((item) => (
        <div key={item.label} className="contents">
          <dt className="text-xs font-medium uppercase tracking-wide text-foreground-subtle">
            {item.label}
          </dt>
          <dd className="font-mono text-sm text-foreground">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
