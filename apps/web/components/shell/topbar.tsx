"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";

const SEGMENT_LABELS: Record<string, string> = {
  payments: "Payments",
  cards: "Cards",
  cardholders: "Cardholders",
  bills: "Bills",
  payees: "Payees",
  fraud: "Fraud",
  reporting: "Reporting",
  reconciliation: "Reconciliation",
  new: "New",
};

function labelFor(segment: string): string {
  if (SEGMENT_LABELS[segment]) return SEGMENT_LABELS[segment];
  // UUIDs and IDs - keep them short
  if (segment.length > 12) return `${segment.slice(0, 6)}…${segment.slice(-4)}`;
  return segment;
}

export function TopBar() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  return (
    <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur">
      <nav className="flex items-center gap-1.5 text-sm">
        <Link
          href="/"
          className="flex items-center text-foreground-subtle transition-colors hover:text-foreground"
        >
          <Home className="h-3.5 w-3.5" />
        </Link>
        {segments.map((segment, index) => {
          const href = "/" + segments.slice(0, index + 1).join("/");
          const isLast = index === segments.length - 1;
          return (
            <div key={href} className="flex items-center gap-1.5">
              <ChevronRight className="h-3.5 w-3.5 text-foreground-subtle" />
              {isLast ? (
                <span className="font-medium text-foreground">
                  {labelFor(segment)}
                </span>
              ) : (
                <Link
                  href={href}
                  className="text-foreground-muted transition-colors hover:text-foreground"
                >
                  {labelFor(segment)}
                </Link>
              )}
            </div>
          );
        })}
      </nav>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 rounded-md border border-border bg-card px-2.5 py-1 text-xs">
          <div className="h-1.5 w-1.5 rounded-full bg-success" />
          <span className="font-medium text-foreground-muted">
            localhost:8000
          </span>
        </div>
      </div>
    </header>
  );
}
