"use client";

import { useEffect, useState } from "react";
import { Check, Copy } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { truncateId } from "@/lib/utils/format";

interface CopyableIdProps {
  value: string;
  head?: number;
  tail?: number;
  className?: string;
}

export function CopyableId({
  value,
  head = 6,
  tail = 4,
  className,
}: CopyableIdProps) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timeoutId = window.setTimeout(() => setCopied(false), 1200);
    return () => window.clearTimeout(timeoutId);
  }, [copied]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        void handleCopy();
      }}
      title={copied ? "Copied!" : value}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-1.5 py-0.5 font-mono text-xs text-foreground-muted transition-colors hover:bg-card-hover hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        className,
      )}
    >
      <span>{truncateId(value, head, tail)}</span>
      {copied ? (
        <Check className="h-3 w-3 text-success" aria-hidden="true" />
      ) : (
        <Copy className="h-3 w-3" aria-hidden="true" />
      )}
      <span className="sr-only">{copied ? "Copied" : "Copy ID"}</span>
    </button>
  );
}
