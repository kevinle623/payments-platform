import { apiGet } from "@/lib/api/client";
import type {
  ReconciliationDiscrepancy,
  ReconciliationRun,
} from "@/lib/api/types";

interface ListReconciliationRunsParams {
  [key: string]: string | number | boolean | null | undefined;
  limit?: number;
  offset?: number;
}

interface ListDiscrepanciesParams {
  [key: string]: string | number | boolean | null | undefined;
  run_id?: string;
  limit?: number;
  offset?: number;
}

export function listReconciliationRuns(
  params: ListReconciliationRunsParams = {},
): Promise<ReconciliationRun[]> {
  return apiGet<ReconciliationRun[]>("/reconciliation/runs", params);
}

export function listReconciliationDiscrepancies(
  params: ListDiscrepanciesParams = {},
): Promise<ReconciliationDiscrepancy[]> {
  return apiGet<ReconciliationDiscrepancy[]>(
    "/reconciliation/discrepancies",
    params,
  );
}

export type { ListDiscrepanciesParams, ListReconciliationRunsParams };
