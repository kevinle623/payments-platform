import { apiGet, apiPatch, apiPost } from "@/lib/api/client";
import type {
  Bill,
  BillDetail,
  BillExecutionResponse,
  BillStatus,
  CreateBillInput,
  UpdateBillInput,
} from "@/lib/api/types";

interface ListBillsParams {
  [key: string]: string | number | boolean | null | undefined;
  status?: BillStatus;
  limit?: number;
  offset?: number;
}

export function listBills(params: ListBillsParams = {}): Promise<Bill[]> {
  return apiGet<Bill[]>("/bills", params);
}

export function getBill(id: string): Promise<BillDetail> {
  return apiGet<BillDetail>(`/bills/${id}`);
}

export function createBill(input: CreateBillInput): Promise<Bill> {
  return apiPost<Bill>("/bills", input);
}

export function updateBill(id: string, input: UpdateBillInput): Promise<Bill> {
  return apiPatch<Bill>(`/bills/${id}`, input);
}

export function executeBill(id: string): Promise<BillExecutionResponse> {
  return apiPost<BillExecutionResponse>(`/bills/${id}/execute`);
}

export type { ListBillsParams };
