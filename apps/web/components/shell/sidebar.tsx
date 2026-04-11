"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CreditCard,
  ShieldAlert,
  Wallet,
  Users,
  Receipt,
  Building2,
  BarChart3,
  GitCompareArrows,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface NavItem {
  label: string;
  href: string;
  icon: typeof LayoutDashboard;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: "Dashboard",
    items: [{ label: "Overview", href: "/", icon: LayoutDashboard }],
  },
  {
    label: "Acquiring",
    items: [
      { label: "Payments", href: "/payments", icon: CreditCard },
      { label: "Fraud signals", href: "/fraud", icon: ShieldAlert },
    ],
  },
  {
    label: "Issuing",
    items: [
      { label: "Cards", href: "/cards", icon: Wallet },
      { label: "Cardholders", href: "/cardholders", icon: Users },
    ],
  },
  {
    label: "Bills",
    items: [
      { label: "Bills", href: "/bills", icon: Receipt },
      { label: "Payees", href: "/payees", icon: Building2 },
    ],
  },
  {
    label: "Observability",
    items: [
      { label: "Reporting", href: "/reporting", icon: BarChart3 },
      {
        label: "Reconciliation",
        href: "/reconciliation",
        icon: GitCompareArrows,
      },
    ],
  },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-border bg-background-elevated">
      <div className="flex h-14 items-center gap-2 border-b border-border px-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            className="h-4 w-4 text-primary-foreground"
            stroke="currentColor"
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold tracking-tight text-foreground">
            Payments
          </span>
          <span className="text-[10px] font-medium uppercase tracking-wider text-foreground-subtle">
            Platform
          </span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-4">
        {NAV_GROUPS.map((group) => (
          <div key={group.label} className="px-3 pb-5">
            <p className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-wider text-foreground-subtle">
              {group.label}
            </p>
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const active = isActive(pathname, item.href);
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        "group flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors",
                        active
                          ? "bg-card-hover text-foreground"
                          : "text-foreground-muted hover:bg-card-hover hover:text-foreground",
                      )}
                    >
                      <Icon
                        className={cn(
                          "h-4 w-4 transition-colors",
                          active
                            ? "text-foreground"
                            : "text-foreground-subtle group-hover:text-foreground-muted",
                        )}
                      />
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-border px-5 py-3">
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-success" />
          <span className="text-xs text-foreground-muted">Local dev</span>
        </div>
      </div>
    </aside>
  );
}
