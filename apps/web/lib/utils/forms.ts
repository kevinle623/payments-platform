export function normalizeCurrencyCode(value: string): string {
  return value.trim().toLowerCase();
}

export function parseMajorAmountToMinor(
  value: string,
  { allowZero = false }: { allowZero?: boolean } = {},
): number | null {
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed)) return null;
  if (allowZero ? parsed < 0 : parsed <= 0) return null;
  return Math.round(parsed * 100);
}

export function isDigitsOnly(value: string): boolean {
  return /^\d+$/.test(value);
}

export function isValidLastFour(value: string): boolean {
  return value === "" || /^\d{4}$/.test(value);
}
