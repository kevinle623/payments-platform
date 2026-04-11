import { apiGet, apiPost } from "@/lib/api/client";
import type { Cardholder, CreateCardholderInput } from "@/lib/api/types";

interface ListCardholdersParams {
  [key: string]: string | number | boolean | null | undefined;
  limit?: number;
  offset?: number;
}

export function listCardholders(
  params: ListCardholdersParams = {},
): Promise<Cardholder[]> {
  return apiGet<Cardholder[]>("/issuer/cardholders", params);
}

export function createCardholder(
  input: CreateCardholderInput,
): Promise<Cardholder> {
  return apiPost<Cardholder>("/issuer/cardholders", input);
}

export type { ListCardholdersParams };
