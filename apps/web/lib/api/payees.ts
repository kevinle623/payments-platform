import { apiGet, apiPost } from "@/lib/api/client";
import type { CreatePayeeInput, Payee } from "@/lib/api/types";

interface ListPayeesParams {
  [key: string]: string | number | boolean | null | undefined;
  limit?: number;
  offset?: number;
}

export function listPayees(params: ListPayeesParams = {}): Promise<Payee[]> {
  return apiGet<Payee[]>("/payees", params);
}

export function createPayee(input: CreatePayeeInput): Promise<Payee> {
  return apiPost<Payee>("/payees", input);
}

export type { ListPayeesParams };
