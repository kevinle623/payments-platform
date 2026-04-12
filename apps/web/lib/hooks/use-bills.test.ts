import { beforeEach, describe, expect, it, vi } from "vitest";
import useSWR, { useSWRConfig } from "swr";
import useSWRMutation from "swr/mutation";
import { listBills } from "@/lib/api/bills";
import { useBills, useExecuteBill } from "@/lib/hooks/use-bills";

vi.mock("swr", () => ({
  default: vi.fn(),
  useSWRConfig: vi.fn(),
}));

vi.mock("swr/mutation", () => ({
  default: vi.fn(),
}));

vi.mock("@/lib/api/bills", () => ({
  listBills: vi.fn(),
  getBill: vi.fn(),
  createBill: vi.fn(),
  updateBill: vi.fn(),
  executeBill: vi.fn(),
}));

function makeSWRResult(overrides: Record<string, unknown> = {}) {
  return {
    data: undefined,
    error: undefined,
    isLoading: false,
    isValidating: false,
    mutate: vi.fn(),
    ...overrides,
  };
}

describe("useBills", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("builds the expected list key and fetcher", async () => {
    const mockedUseSWR = vi.mocked(useSWR);
    const mockedListBills = vi.mocked(listBills);
    mockedUseSWR.mockReturnValue(makeSWRResult() as never);
    mockedListBills.mockResolvedValueOnce([]);

    useBills({ status: "active", limit: 25, offset: 50 });

    const firstCall = mockedUseSWR.mock.calls[0];
    const key = firstCall[0] as readonly ["bills", Record<string, unknown>];
    const fetcher = firstCall[1] as (
      value: readonly ["bills", Record<string, unknown>],
    ) => Promise<unknown>;

    expect(key).toEqual(["bills", { status: "active", limit: 25, offset: 50 }]);

    await fetcher(key);
    expect(mockedListBills).toHaveBeenCalledWith({
      status: "active",
      limit: 25,
      offset: 50,
    });
  });
});

describe("useExecuteBill", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("executes and invalidates bill + payments cache keys", async () => {
    const mockedUseSWRMutation = vi.mocked(useSWRMutation);
    const mockedUseSWRConfig = vi.mocked(useSWRConfig);
    const trigger = vi.fn();
    const mutate = vi.fn().mockResolvedValue(undefined);
    const response = {
      bill: {
        id: "bill_1",
        payee_id: "payee_1",
        card_id: null,
        amount: 1000,
        currency: "usd",
        frequency: "monthly",
        next_due_date: "2026-04-11T00:00:00Z",
        status: "active",
        created_at: "2026-04-11T00:00:00Z",
        updated_at: "2026-04-11T00:00:00Z",
      },
      bill_payment: {
        id: "bp_1",
        bill_id: "bill_1",
        payment_id: "pay_1",
        status: "pending",
        executed_at: "2026-04-11T00:00:00Z",
      },
    };

    trigger.mockResolvedValueOnce(response);

    mockedUseSWRMutation.mockReturnValue({
      trigger,
      data: undefined,
      error: undefined,
      isMutating: false,
      reset: vi.fn(),
    } as never);

    mockedUseSWRConfig.mockReturnValue({
      mutate,
    } as never);

    const action = useExecuteBill();
    await action.execute("bill_1");

    expect(trigger).toHaveBeenCalledWith({ id: "bill_1" });
    expect(mutate).toHaveBeenCalledTimes(3);

    const billsMatcher = mutate.mock.calls[0][0] as (key: unknown) => boolean;
    const billKey = mutate.mock.calls[1][0];
    const paymentsMatcher = mutate.mock.calls[2][0] as (
      key: unknown,
    ) => boolean;

    expect(billsMatcher(["bills", { limit: 25 }])).toBe(true);
    expect(billsMatcher(["payments", { limit: 25 }])).toBe(false);
    expect(billKey).toEqual(["bill", "bill_1"]);
    expect(paymentsMatcher(["payments", { limit: 25 }])).toBe(true);
    expect(paymentsMatcher(["bills", { limit: 25 }])).toBe(false);
  });
});
