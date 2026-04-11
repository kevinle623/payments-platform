"use client";

import { useMemo, useRef, useState } from "react";
import type { KeyboardEvent, ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

interface TabItem {
  id: string;
  label: string;
  content: ReactNode;
}

interface TabsProps {
  tabs: TabItem[];
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  className?: string;
}

export function Tabs({
  tabs,
  value,
  defaultValue,
  onValueChange,
  className,
}: TabsProps) {
  const fallback = tabs[0]?.id ?? "";
  const [internalValue, setInternalValue] = useState(defaultValue ?? fallback);
  const activeId = value ?? internalValue;
  const activeTab = useMemo(
    () => tabs.find((tab) => tab.id === activeId) ?? tabs[0],
    [tabs, activeId],
  );

  const buttonRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  const setActive = (nextId: string) => {
    if (!value) setInternalValue(nextId);
    onValueChange?.(nextId);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (tabs.length === 0) return;
    const currentIndex = Math.max(
      0,
      tabs.findIndex((tab) => tab.id === activeTab?.id),
    );
    let targetIndex = currentIndex;

    if (event.key === "ArrowRight")
      targetIndex = (currentIndex + 1) % tabs.length;
    if (event.key === "ArrowLeft")
      targetIndex = (currentIndex - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") targetIndex = 0;
    if (event.key === "End") targetIndex = tabs.length - 1;

    if (targetIndex !== currentIndex || ["Home", "End"].includes(event.key)) {
      event.preventDefault();
      const nextTab = tabs[targetIndex];
      setActive(nextTab.id);
      buttonRefs.current[nextTab.id]?.focus();
    }
  };

  return (
    <div className={cn("space-y-3", className)}>
      <div
        role="tablist"
        aria-label="Tabs"
        className="flex flex-wrap items-center gap-1 rounded-lg border border-border bg-card p-1"
        onKeyDown={handleKeyDown}
      >
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab?.id;
          return (
            <button
              key={tab.id}
              ref={(element) => {
                buttonRefs.current[tab.id] = element;
              }}
              id={`tab-${tab.id}`}
              role="tab"
              type="button"
              aria-selected={isActive}
              aria-controls={`panel-${tab.id}`}
              tabIndex={isActive ? 0 : -1}
              onClick={() => setActive(tab.id)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                isActive
                  ? "bg-card-hover text-foreground"
                  : "text-foreground-muted hover:text-foreground",
              )}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab ? (
        <div
          id={`panel-${activeTab.id}`}
          role="tabpanel"
          aria-labelledby={`tab-${activeTab.id}`}
        >
          {activeTab.content}
        </div>
      ) : null}
    </div>
  );
}
