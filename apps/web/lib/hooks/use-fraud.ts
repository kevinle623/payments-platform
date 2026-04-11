import useSWR from "swr";
import { listFraudSignals, type ListFraudSignalsParams } from "@/lib/api/fraud";
import type { ApiError } from "@/lib/api/client";
import type { FraudSignal } from "@/lib/api/types";

type FraudSignalsKey = readonly ["fraud-signals", ListFraudSignalsParams];

function fraudSignalsFetcher([, params]: FraudSignalsKey): Promise<
  FraudSignal[]
> {
  return listFraudSignals(params);
}

export function useFraudSignals(params: ListFraudSignalsParams = {}) {
  const key: FraudSignalsKey = [
    "fraud-signals",
    {
      risk_level: params.risk_level,
      limit: params.limit,
      offset: params.offset,
    },
  ];
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    fraudSignalsFetcher,
  );

  return {
    data: data ?? [],
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}
