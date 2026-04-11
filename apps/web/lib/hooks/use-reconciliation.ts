import useSWR from "swr";
import {
  listReconciliationDiscrepancies,
  listReconciliationRuns,
  type ListDiscrepanciesParams,
  type ListReconciliationRunsParams,
} from "@/lib/api/reconciliation";
import type { ApiError } from "@/lib/api/client";
import type {
  ReconciliationDiscrepancy,
  ReconciliationRun,
} from "@/lib/api/types";

type ReconciliationRunsKey = readonly [
  "reconciliation-runs",
  ListReconciliationRunsParams,
];
type DiscrepanciesKey = readonly [
  "reconciliation-discrepancies",
  string,
  Omit<ListDiscrepanciesParams, "run_id">,
];

function runsFetcher([, params]: ReconciliationRunsKey): Promise<
  ReconciliationRun[]
> {
  return listReconciliationRuns(params);
}

function discrepanciesFetcher([, runId, params]: DiscrepanciesKey): Promise<
  ReconciliationDiscrepancy[]
> {
  return listReconciliationDiscrepancies({
    run_id: runId,
    ...params,
  });
}

export function useReconciliationRuns(
  params: ListReconciliationRunsParams = {},
) {
  const key: ReconciliationRunsKey = [
    "reconciliation-runs",
    {
      limit: params.limit,
      offset: params.offset,
    },
  ];
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    runsFetcher,
  );

  return {
    data: data ?? [],
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useDiscrepancies(
  runId: string | null | undefined,
  params: Omit<ListDiscrepanciesParams, "run_id"> = {},
  enabled = true,
) {
  const key =
    runId && enabled
      ? ([
          "reconciliation-discrepancies",
          runId,
          {
            limit: params.limit,
            offset: params.offset,
          },
        ] as const)
      : null;

  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    discrepanciesFetcher,
  );

  return {
    data: data ?? [],
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}
