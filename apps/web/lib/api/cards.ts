import { apiGet, apiPost } from "@/lib/api/client";
import type {
  Card,
  CardAuthorization,
  CardBalance,
  CreateCardInput,
} from "@/lib/api/types";

interface ListCardsParams {
  [key: string]: string | number | boolean | null | undefined;
  limit?: number;
  offset?: number;
}

interface ListCardAuthorizationsParams {
  [key: string]: string | number | boolean | null | undefined;
  limit?: number;
  offset?: number;
}

export function listCards(params: ListCardsParams = {}): Promise<Card[]> {
  return apiGet<Card[]>("/issuer/cards", params);
}

export function getCard(id: string): Promise<Card> {
  return apiGet<Card>(`/issuer/cards/${id}`);
}

export function createCard(input: CreateCardInput): Promise<Card> {
  return apiPost<Card>("/issuer/cards", input);
}

export function getCardBalance(id: string): Promise<CardBalance> {
  return apiGet<CardBalance>(`/issuer/cards/${id}/balance`);
}

export function listCardAuthorizations(
  id: string,
  params: ListCardAuthorizationsParams = {},
): Promise<CardAuthorization[]> {
  return apiGet<CardAuthorization[]>(
    `/issuer/cards/${id}/authorizations`,
    params,
  );
}

export type { ListCardAuthorizationsParams, ListCardsParams };
