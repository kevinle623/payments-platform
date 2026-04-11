import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useSWRConfig } from "swr";
import {
  createCardholder,
  listCardholders,
  type ListCardholdersParams,
} from "@/lib/api/cardholders";
import type { ApiError } from "@/lib/api/client";
import type { Cardholder, CreateCardholderInput } from "@/lib/api/types";

type CardholdersKey = readonly ["cardholders", ListCardholdersParams];

function cardholdersFetcher([, params]: CardholdersKey): Promise<Cardholder[]> {
  return listCardholders(params);
}

export function useCardholders(params: ListCardholdersParams = {}) {
  const key: CardholdersKey = [
    "cardholders",
    {
      limit: params.limit,
      offset: params.offset,
    },
  ];
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    cardholdersFetcher,
  );

  return {
    data: data ?? [],
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}

async function createCardholderFetcher(
  _key: "create-cardholder",
  { arg }: { arg: CreateCardholderInput },
): Promise<Cardholder> {
  return createCardholder(arg);
}

export function useCreateCardholder() {
  const { mutate } = useSWRConfig();
  const { trigger, data, error, isMutating } = useSWRMutation(
    "create-cardholder",
    createCardholderFetcher,
  );

  const create = async (input: CreateCardholderInput) => {
    const result = await trigger(input);
    await mutate((key) => Array.isArray(key) && key[0] === "cardholders");
    return result;
  };

  return {
    create,
    data,
    error: (error as ApiError | undefined) ?? undefined,
    isLoading: isMutating,
  };
}
