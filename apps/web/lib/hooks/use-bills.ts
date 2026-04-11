import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useSWRConfig } from "swr";
import {
  createBill,
  executeBill,
  getBill,
  listBills,
  updateBill,
  type ListBillsParams,
} from "@/lib/api/bills";
import type { ApiError } from "@/lib/api/client";
import type {
  Bill,
  BillDetail,
  BillExecutionResponse,
  CreateBillInput,
  UpdateBillInput,
} from "@/lib/api/types";

type BillsKey = readonly ["bills", ListBillsParams];
type BillKey = readonly ["bill", string];

function billsFetcher([, params]: BillsKey): Promise<Bill[]> {
  return listBills(params);
}

function billFetcher([, id]: BillKey): Promise<BillDetail> {
  return getBill(id);
}

export function useBills(params: ListBillsParams = {}) {
  const key: BillsKey = [
    "bills",
    {
      status: params.status,
      limit: params.limit,
      offset: params.offset,
    },
  ];

  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    billsFetcher,
  );

  return {
    data: data ?? [],
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useBill(id: string | null | undefined) {
  const key = id ? (["bill", id] as const) : null;
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    key,
    billFetcher,
  );

  return {
    data,
    error: (error as ApiError | undefined) ?? undefined,
    isLoading,
    isValidating,
    mutate,
  };
}

async function createBillFetcher(
  _key: "create-bill",
  { arg }: { arg: CreateBillInput },
): Promise<Bill> {
  return createBill(arg);
}

async function updateBillFetcher(
  _key: "update-bill",
  { arg }: { arg: { id: string; input: UpdateBillInput } },
): Promise<Bill> {
  return updateBill(arg.id, arg.input);
}

async function executeBillFetcher(
  _key: "execute-bill",
  { arg }: { arg: { id: string } },
): Promise<BillExecutionResponse> {
  return executeBill(arg.id);
}

export function useCreateBill() {
  const { mutate } = useSWRConfig();
  const { trigger, data, error, isMutating } = useSWRMutation(
    "create-bill",
    createBillFetcher,
  );

  const create = async (input: CreateBillInput) => {
    const result = await trigger(input);
    await mutate((key) => Array.isArray(key) && key[0] === "bills");
    return result;
  };

  return {
    create,
    data,
    error: (error as ApiError | undefined) ?? undefined,
    isLoading: isMutating,
  };
}

export function useUpdateBill() {
  const { mutate } = useSWRConfig();
  const { trigger, data, error, isMutating } = useSWRMutation(
    "update-bill",
    updateBillFetcher,
  );

  const update = async (id: string, input: UpdateBillInput) => {
    const result = await trigger({ id, input });
    await mutate((key) => Array.isArray(key) && key[0] === "bills");
    await mutate(["bill", id]);
    return result;
  };

  return {
    update,
    data,
    error: (error as ApiError | undefined) ?? undefined,
    isLoading: isMutating,
  };
}

export function useExecuteBill() {
  const { mutate } = useSWRConfig();
  const { trigger, data, error, isMutating } = useSWRMutation(
    "execute-bill",
    executeBillFetcher,
  );

  const execute = async (id: string) => {
    const result = await trigger({ id });
    await mutate((key) => Array.isArray(key) && key[0] === "bills");
    await mutate(["bill", id]);
    await mutate((key) => Array.isArray(key) && key[0] === "payments");
    return result;
  };

  return {
    execute,
    data,
    error: (error as ApiError | undefined) ?? undefined,
    isLoading: isMutating,
  };
}
