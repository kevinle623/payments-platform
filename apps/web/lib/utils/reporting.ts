import type { ReportingSummaryRow } from "@/lib/api/types";

export interface ReportingDailyPoint {
  date: string;
  totalAmount: number;
  count: number;
}

export interface ReportingCurrencySeries {
  currency: string;
  totalAmount: number;
  totalCount: number;
  points: ReportingDailyPoint[];
}

export interface ReportingEventTotal {
  currency: string;
  eventType: string;
  totalAmount: number;
  count: number;
}

export function buildReportingCurrencySeries(
  rows: ReportingSummaryRow[],
): ReportingCurrencySeries[] {
  const grouped = new Map<
    string,
    {
      totalAmount: number;
      totalCount: number;
      byDate: Map<string, ReportingDailyPoint>;
    }
  >();

  for (const row of rows) {
    const currency = row.currency.toLowerCase();
    const entry = grouped.get(currency) ?? {
      totalAmount: 0,
      totalCount: 0,
      byDate: new Map<string, ReportingDailyPoint>(),
    };

    const point = entry.byDate.get(row.date) ?? {
      date: row.date,
      totalAmount: 0,
      count: 0,
    };

    point.totalAmount += row.total_amount;
    point.count += row.count;
    entry.totalAmount += row.total_amount;
    entry.totalCount += row.count;

    entry.byDate.set(row.date, point);
    grouped.set(currency, entry);
  }

  return Array.from(grouped.entries())
    .map(([currency, value]) => ({
      currency,
      totalAmount: value.totalAmount,
      totalCount: value.totalCount,
      points: Array.from(value.byDate.values()).sort((a, b) =>
        a.date.localeCompare(b.date),
      ),
    }))
    .sort((a, b) => a.currency.localeCompare(b.currency));
}

export function buildReportingEventTotals(
  rows: ReportingSummaryRow[],
): ReportingEventTotal[] {
  const grouped = new Map<string, ReportingEventTotal>();

  for (const row of rows) {
    const currency = row.currency.toLowerCase();
    const key = `${currency}:${row.event_type}`;
    const entry = grouped.get(key) ?? {
      currency,
      eventType: row.event_type,
      totalAmount: 0,
      count: 0,
    };

    entry.totalAmount += row.total_amount;
    entry.count += row.count;

    grouped.set(key, entry);
  }

  return Array.from(grouped.values()).sort((a, b) => {
    if (a.currency !== b.currency) {
      return a.currency.localeCompare(b.currency);
    }
    return b.totalAmount - a.totalAmount;
  });
}
