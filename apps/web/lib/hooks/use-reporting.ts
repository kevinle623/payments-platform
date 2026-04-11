import useSWR from "swr";
import {
  getReportingSummary,
  type GetReportingSummaryParams,
} from "@/lib/api/reporting";
import type { ApiError } from "@/lib/api/client";
import type { ReportingSummaryRow } from "@/lib/api/types";

type ReportingSummaryKey = readonly [
  "reporting-summary",
  GetReportingSummaryParams,
];

function reportingSummaryFetcher([, params]: ReportingSummaryKey): Promise<
  ReportingSummaryRow[]
> {
  return getReportingSummary(params);
}

export function useReportingSummary(params: GetReportingSummaryParams = {}) {
  const key: ReportingSummaryKey = [
    "reporting-summary",
    {
      since: params.since,
      until: params.until,
    },
  ];
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    reportingSummaryFetcher,
  );

  return {
    data: data ?? [],
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}
