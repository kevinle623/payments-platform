import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useSWRConfig } from "swr";
import {
  createPayee,
  listPayees,
  type ListPayeesParams,
} from "@/lib/api/payees";
import type { ApiError } from "@/lib/api/client";
import type { CreatePayeeInput, Payee } from "@/lib/api/types";

type PayeesKey = readonly ["payees", ListPayeesParams];

function payeesFetcher([, params]: PayeesKey): Promise<Payee[]> {
  return listPayees(params);
}

export function usePayees(params: ListPayeesParams = {}) {
  const key: PayeesKey = [
    "payees",
    {
      limit: params.limit,
      offset: params.offset,
    },
  ];

  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    payeesFetcher,
  );

  return {
    data: data ?? [],
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}

async function createPayeeFetcher(
  _key: "create-payee",
  { arg }: { arg: CreatePayeeInput },
): Promise<Payee> {
  return createPayee(arg);
}

export function useCreatePayee() {
  const { mutate } = useSWRConfig();
  const { trigger, data, error, isMutating } = useSWRMutation(
    "create-payee",
    createPayeeFetcher,
  );

  const create = async (input: CreatePayeeInput) => {
    const result = await trigger(input);
    await mutate((key) => Array.isArray(key) && key[0] === "payees");
    return result;
  };

  return {
    create,
    data,
    error: (error as ApiError | undefined) ?? undefined,
    isLoading: isMutating,
  };
}
