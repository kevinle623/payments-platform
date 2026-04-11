import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useSWRConfig } from "swr";
import {
  createCard,
  getCard,
  getCardBalance,
  listCardAuthorizations,
  listCards,
  type ListCardAuthorizationsParams,
  type ListCardsParams,
} from "@/lib/api/cards";
import type { ApiError } from "@/lib/api/client";
import type {
  Card,
  CardAuthorization,
  CardBalance,
  CreateCardInput,
} from "@/lib/api/types";

type CardsKey = readonly ["cards", ListCardsParams];
type CardKey = readonly ["card", string];
type CardBalanceKey = readonly ["card-balance", string];
type CardAuthorizationsKey = readonly [
  "card-authorizations",
  string,
  ListCardAuthorizationsParams,
];

function cardsFetcher([, params]: CardsKey): Promise<Card[]> {
  return listCards(params);
}

function cardFetcher([, id]: CardKey): Promise<Card> {
  return getCard(id);
}

function cardBalanceFetcher([, id]: CardBalanceKey): Promise<CardBalance> {
  return getCardBalance(id);
}

function cardAuthorizationsFetcher([
  ,
  id,
  params,
]: CardAuthorizationsKey): Promise<CardAuthorization[]> {
  return listCardAuthorizations(id, params);
}

export function useCards(params: ListCardsParams = {}) {
  const key: CardsKey = [
    "cards",
    {
      limit: params.limit,
      offset: params.offset,
    },
  ];
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    cardsFetcher,
  );

  return {
    data: data ?? [],
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useCard(id: string | null | undefined) {
  const key = id ? (["card", id] as const) : null;
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    cardFetcher,
  );

  return {
    data,
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useCardBalance(id: string | null | undefined) {
  const key = id ? (["card-balance", id] as const) : null;
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    cardBalanceFetcher,
  );

  return {
    data,
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useCardAuthorizations(
  id: string | null | undefined,
  params: ListCardAuthorizationsParams = {},
) {
  const key = id
    ? ([
        "card-authorizations",
        id,
        {
          limit: params.limit,
          offset: params.offset,
        },
      ] as const)
    : null;
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    cardAuthorizationsFetcher,
  );

  return {
    data: data ?? [],
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}

async function createCardFetcher(
  _key: "create-card",
  { arg }: { arg: CreateCardInput },
): Promise<Card> {
  return createCard(arg);
}

export function useCreateCard() {
  const { mutate } = useSWRConfig();
  const { trigger, data, error, isMutating } = useSWRMutation(
    "create-card",
    createCardFetcher,
  );

  const create = async (input: CreateCardInput) => {
    const result = await trigger(input);
    await mutate((key) => Array.isArray(key) && key[0] === "cards");
    return result;
  };

  return {
    create,
    data,
    error: (error as ApiError | undefined) ?? undefined,
    isLoading: isMutating,
  };
}
