import { apiGet } from "@/lib/api/client";
import type { ReportingSummaryRow } from "@/lib/api/types";

interface GetReportingSummaryParams {
  [key: string]: string | number | boolean | null | undefined;
  since?: string;
  until?: string;
}

export function getReportingSummary(
  params: GetReportingSummaryParams = {},
): Promise<ReportingSummaryRow[]> {
  return apiGet<ReportingSummaryRow[]>("/reporting/summary", params);
}

export type { GetReportingSummaryParams };
