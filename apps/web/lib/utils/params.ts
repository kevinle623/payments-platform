export function parseNonNegativeInt(
  value: string | null,
  fallback: number,
): number {
  if (!value) return fallback;
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
}

export function getFirstParamValue(
  value: string | string[] | undefined,
): string | null {
  if (!value) return null;
  return Array.isArray(value) ? value[0] : value;
}
