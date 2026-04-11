"use client";

import type { ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils/cn";

interface FilterBarRenderProps {
  getValue: (key: string) => string;
  setValue: (key: string, value: string | null | undefined) => void;
  setValues: (updates: Record<string, string | null | undefined>) => void;
  clearValues: (keys?: string[]) => void;
}

interface FilterBarProps {
  children: ReactNode | ((helpers: FilterBarRenderProps) => ReactNode);
  className?: string;
}

export function FilterBar({ children, className }: FilterBarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const replaceWith = (next: URLSearchParams) => {
    const query = next.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, {
      scroll: false,
    });
  };

  const getValue = (key: string): string => searchParams.get(key) ?? "";

  const setValues = (updates: Record<string, string | null | undefined>) => {
    const next = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(updates)) {
      if (!value) next.delete(key);
      else next.set(key, value);
    }
    replaceWith(next);
  };

  const setValue = (key: string, value: string | null | undefined) => {
    setValues({ [key]: value });
  };

  const clearValues = (keys?: string[]) => {
    const next = new URLSearchParams(searchParams.toString());
    if (!keys || keys.length === 0) {
      Array.from(next.keys()).forEach((key) => next.delete(key));
    } else {
      keys.forEach((key) => next.delete(key));
    }
    replaceWith(next);
  };

  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card p-3 sm:p-4",
        className,
      )}
    >
      {typeof children === "function"
        ? children({ getValue, setValue, setValues, clearValues })
        : children}
    </div>
  );
}
