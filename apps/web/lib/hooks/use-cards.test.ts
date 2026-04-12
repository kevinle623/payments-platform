import { beforeEach, describe, expect, it, vi } from "vitest";
import useSWR from "swr";
import { getCard, listCardAuthorizations, listCards } from "@/lib/api/cards";
import {
  useCard,
  useCardAuthorizations,
  useCards,
} from "@/lib/hooks/use-cards";

vi.mock("swr", () => ({
  default: vi.fn(),
}));

vi.mock("@/lib/api/cards", () => ({
  listCards: vi.fn(),
  getCard: vi.fn(),
  getCardBalance: vi.fn(),
  listCardAuthorizations: vi.fn(),
  createCard: vi.fn(),
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

describe("useCards", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("builds cards list key and fetcher", async () => {
    const mockedUseSWR = vi.mocked(useSWR);
    const mockedListCards = vi.mocked(listCards);
    mockedUseSWR.mockReturnValue(makeSWRResult() as never);
    mockedListCards.mockResolvedValueOnce([]);

    useCards({ limit: 25, offset: 50 });

    const firstCall = mockedUseSWR.mock.calls[0];
    const key = firstCall[0] as readonly ["cards", Record<string, unknown>];
    const fetcher = firstCall[1] as (
      value: readonly ["cards", Record<string, unknown>],
    ) => Promise<unknown>;

    expect(key).toEqual(["cards", { limit: 25, offset: 50 }]);
    await fetcher(key);
    expect(mockedListCards).toHaveBeenCalledWith({ limit: 25, offset: 50 });
  });
});

describe("useCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("passes null key when card id is missing", () => {
    const mockedUseSWR = vi.mocked(useSWR);
    mockedUseSWR.mockReturnValue(makeSWRResult() as never);

    useCard(undefined);

    expect(mockedUseSWR.mock.calls[0][0]).toBeNull();
  });

  it("builds detail key and fetcher when id is present", async () => {
    const mockedUseSWR = vi.mocked(useSWR);
    const mockedGetCard = vi.mocked(getCard);
    mockedUseSWR.mockReturnValue(makeSWRResult() as never);
    mockedGetCard.mockResolvedValueOnce({
      id: "card_1",
      cardholder_id: "cardholder_1",
      available_balance_account_id: "acct_1",
      pending_hold_account_id: "acct_2",
      last_four: "4242",
      credit_limit: 1000,
      currency: "usd",
      status: "active",
      created_at: "2026-04-11T00:00:00Z",
      updated_at: "2026-04-11T00:00:00Z",
    });

    useCard("card_1");

    const firstCall = mockedUseSWR.mock.calls[0];
    const key = firstCall[0] as readonly ["card", string];
    const fetcher = firstCall[1] as (
      value: readonly ["card", string],
    ) => Promise<unknown>;

    expect(key).toEqual(["card", "card_1"]);
    await fetcher(key);
    expect(mockedGetCard).toHaveBeenCalledWith("card_1");
  });
});

describe("useCardAuthorizations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("builds nested key and fetcher for card authorization list", async () => {
    const mockedUseSWR = vi.mocked(useSWR);
    const mockedListCardAuthorizations = vi.mocked(listCardAuthorizations);
    mockedUseSWR.mockReturnValue(makeSWRResult() as never);
    mockedListCardAuthorizations.mockResolvedValueOnce([]);

    useCardAuthorizations("card_1", { limit: 100, offset: 0 });

    const firstCall = mockedUseSWR.mock.calls[0];
    const key = firstCall[0] as readonly [
      "card-authorizations",
      string,
      Record<string, unknown>,
    ];
    const fetcher = firstCall[1] as (
      value: readonly ["card-authorizations", string, Record<string, unknown>],
    ) => Promise<unknown>;

    expect(key).toEqual([
      "card-authorizations",
      "card_1",
      { limit: 100, offset: 0 },
    ]);
    await fetcher(key);
    expect(mockedListCardAuthorizations).toHaveBeenCalledWith("card_1", {
      limit: 100,
      offset: 0,
    });
  });
});
