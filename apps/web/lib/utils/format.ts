import { format, formatDistanceToNow, parseISO } from "date-fns";

const ZERO_DECIMAL_CURRENCIES = new Set([
  "bif",
  "clp",
  "djf",
  "gnf",
  "jpy",
  "kmf",
  "krw",
  "mga",
  "pyg",
  "rwf",
  "ugx",
  "vnd",
  "vuv",
  "xaf",
  "xof",
  "xpf",
]);

export function formatAmount(
  minorUnits: number | string,
  currency: string,
): string {
  const code = currency.toLowerCase();
  const value =
    typeof minorUnits === "string" ? Number(minorUnits) : minorUnits;
  const isZeroDecimal = ZERO_DECIMAL_CURRENCIES.has(code);
  const major = isZeroDecimal ? value : value / 100;

  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency.toUpperCase(),
      minimumFractionDigits: isZeroDecimal ? 0 : 2,
      maximumFractionDigits: isZeroDecimal ? 0 : 2,
    }).format(major);
  } catch {
    return `${major.toFixed(isZeroDecimal ? 0 : 2)} ${currency.toUpperCase()}`;
  }
}

function toDate(value: string | Date): Date {
  return value instanceof Date ? value : parseISO(value);
}

export function formatDate(value: string | Date): string {
  return format(toDate(value), "MMM d, yyyy");
}

export function formatDateTime(value: string | Date): string {
  return format(toDate(value), "MMM d, yyyy HH:mm:ss");
}

export function formatRelative(value: string | Date): string {
  return formatDistanceToNow(toDate(value), { addSuffix: true });
}

export function truncateId(id: string, head = 6, tail = 4): string {
  if (id.length <= head + tail + 1) return id;
  return `${id.slice(0, head)}…${id.slice(-tail)}`;
}
