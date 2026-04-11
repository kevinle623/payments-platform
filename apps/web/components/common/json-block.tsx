import { cn } from "@/lib/utils/cn";

interface JsonBlockProps {
  value: unknown;
  className?: string;
}

export function JsonBlock({ value, className }: JsonBlockProps) {
  return (
    <pre
      className={cn(
        "max-h-96 overflow-auto rounded-lg border border-border bg-background p-3 font-mono text-xs leading-relaxed text-foreground-muted",
        className,
      )}
    >
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}
