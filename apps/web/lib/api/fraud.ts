import { apiGet } from "@/lib/api/client";
import type { FraudSignal, RiskLevel } from "@/lib/api/types";

interface ListFraudSignalsParams {
  [key: string]: string | number | boolean | null | undefined;
  risk_level?: RiskLevel;
  limit?: number;
  offset?: number;
}

export function listFraudSignals(
  params: ListFraudSignalsParams = {},
): Promise<FraudSignal[]> {
  return apiGet<FraudSignal[]>("/fraud/signals", params);
}

export type { ListFraudSignalsParams };
