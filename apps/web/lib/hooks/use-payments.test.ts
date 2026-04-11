import { beforeEach, describe, expect, it, vi } from "vitest";
import useSWR from "swr";
import { getPayment, listPayments } from "@/lib/api/payments";
import { usePayment, usePayments } from "@/lib/hooks/use-payments";

vi.mock("swr", () => ({
  default: vi.fn(),
}));

vi.mock("@/lib/api/payments", () => ({
  listPayments: vi.fn(),
  getPayment: vi.fn(),
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

describe("usePayments", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("builds the expected SWR key and fetcher for list queries", async () => {
    const mockedUseSWR = vi.mocked(useSWR);
    const mockedListPayments = vi.mocked(listPayments);
    mockedUseSWR.mockReturnValue(makeSWRResult() as never);
    mockedListPayments.mockResolvedValueOnce([]);

    usePayments({ status: "pending", limit: 25, offset: 50 });

    expect(mockedUseSWR).toHaveBeenCalledTimes(1);
    const firstCall = mockedUseSWR.mock.calls[0];
    const key = firstCall[0] as readonly ["payments", Record<string, unknown>];
    const fetcher = firstCall[1] as (
      value: readonly ["payments", Record<string, unknown>],
    ) => Promise<unknown>;

    expect(key).toEqual([
      "payments",
      { status: "pending", limit: 25, offset: 50 },
    ]);

    await fetcher(key);
    expect(mockedListPayments).toHaveBeenCalledWith({
      status: "pending",
      limit: 25,
      offset: 50,
    });
  });

  it("returns empty data array when SWR data is undefined", () => {
    const mockedUseSWR = vi.mocked(useSWR);
    mockedUseSWR.mockReturnValue(makeSWRResult({ data: undefined }) as never);

    const result = usePayments();
    expect(result.data).toEqual([]);
  });
});

describe("usePayment", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("passes null key when id is not provided", () => {
    const mockedUseSWR = vi.mocked(useSWR);
    mockedUseSWR.mockReturnValue(makeSWRResult() as never);

    usePayment(null);

    expect(mockedUseSWR).toHaveBeenCalledTimes(1);
    const key = mockedUseSWR.mock.calls[0][0];
    expect(key).toBeNull();
  });

  it("builds detail key and fetcher when id is present", async () => {
    const mockedUseSWR = vi.mocked(useSWR);
    const mockedGetPayment = vi.mocked(getPayment);
    mockedUseSWR.mockReturnValue(makeSWRResult() as never);
    mockedGetPayment.mockResolvedValueOnce({
      payment: {
        id: "pay_1",
        processor_payment_id: "pi_1",
        status: "pending",
        amount: 5000,
        currency: "usd",
        idempotency_key: "idem_1",
        created_at: "2026-04-11T00:00:00Z",
        updated_at: "2026-04-11T00:00:00Z",
      },
      ledger_transactions: [],
      outbox_events: [],
      issuer_authorization: null,
    });

    usePayment("pay_1");

    const firstCall = mockedUseSWR.mock.calls[0];
    const key = firstCall[0] as readonly ["payment", string];
    const fetcher = firstCall[1] as (
      value: readonly ["payment", string],
    ) => Promise<unknown>;

    expect(key).toEqual(["payment", "pay_1"]);
    await fetcher(key);
    expect(mockedGetPayment).toHaveBeenCalledWith("pay_1");
  });
});
