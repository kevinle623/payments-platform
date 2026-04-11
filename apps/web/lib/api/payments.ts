import { apiGet } from "@/lib/api/client";
import type {
  PaymentDetailResponse,
  PaymentRecord,
  PaymentStatus,
} from "@/lib/api/types";

interface ListPaymentsParams {
  [key: string]: string | number | boolean | null | undefined;
  status?: PaymentStatus;
  limit?: number;
  offset?: number;
}

export function listPayments(
  params: ListPaymentsParams = {},
): Promise<PaymentRecord[]> {
  return apiGet<PaymentRecord[]>("/payments", params);
}

export function getPayment(id: string): Promise<PaymentDetailResponse> {
  return apiGet<PaymentDetailResponse>(`/payments/${id}`);
}

export type { ListPaymentsParams };
