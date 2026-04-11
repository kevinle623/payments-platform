import useSWR from "swr";
import {
  getPayment,
  listPayments,
  type ListPaymentsParams,
} from "@/lib/api/payments";
import type { PaymentDetailResponse, PaymentRecord } from "@/lib/api/types";
import type { ApiError } from "@/lib/api/client";

type PaymentsKey = readonly ["payments", ListPaymentsParams];
type PaymentKey = readonly ["payment", string];

function listPaymentsFetcher([, params]: PaymentsKey): Promise<
  PaymentRecord[]
> {
  return listPayments(params);
}

function paymentFetcher([, id]: PaymentKey): Promise<PaymentDetailResponse> {
  return getPayment(id);
}

export function usePayments(params: ListPaymentsParams = {}) {
  const key: PaymentsKey = [
    "payments",
    {
      status: params.status,
      limit: params.limit,
      offset: params.offset,
    },
  ];

  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    listPaymentsFetcher,
  );

  return {
    data: data ?? [],
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}

export function usePayment(id: string | null | undefined) {
  const key = id ? (["payment", id] as const) : null;
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    paymentFetcher,
  );

  return {
    data,
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}
