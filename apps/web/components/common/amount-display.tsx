import { cn } from "@/lib/utils/cn";
import { formatAmount } from "@/lib/utils/format";

interface AmountDisplayProps {
  minorUnits: number | string;
  currency: string;
  showCurrencySuffix?: boolean;
  mutedCurrencySuffix?: boolean;
  className?: string;
}

export function AmountDisplay({
  minorUnits,
  currency,
  showCurrencySuffix = false,
  mutedCurrencySuffix = true,
  className,
}: AmountDisplayProps) {
  return (
    <span className={cn("font-mono text-sm text-foreground", className)}>
      {formatAmount(minorUnits, currency)}
      {showCurrencySuffix ? (
        <span
          className={cn(
            "ml-1 text-xs uppercase",
            mutedCurrencySuffix ? "text-foreground-subtle" : "text-foreground",
          )}
        >
          {currency}
        </span>
      ) : null}
    </span>
  );
}
