import { beforeEach, describe, expect, it, vi } from "vitest";
import useSWR from "swr";
import { getReportingSummary } from "@/lib/api/reporting";
import { useReportingSummary } from "@/lib/hooks/use-reporting";

vi.mock("swr", () => ({
  default: vi.fn(),
}));

vi.mock("@/lib/api/reporting", () => ({
  getReportingSummary: vi.fn(),
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

describe("useReportingSummary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("builds key and fetcher with optional date bounds", async () => {
    const mockedUseSWR = vi.mocked(useSWR);
    const mockedGetReportingSummary = vi.mocked(getReportingSummary);
    mockedUseSWR.mockReturnValue(makeSWRResult() as never);
    mockedGetReportingSummary.mockResolvedValueOnce([]);

    useReportingSummary({
      since: "2026-04-01T00:00:00.000Z",
      until: "2026-04-11T23:59:59.999Z",
    });

    const firstCall = mockedUseSWR.mock.calls[0];
    const key = firstCall[0] as readonly [
      "reporting-summary",
      Record<string, unknown>,
    ];
    const fetcher = firstCall[1] as (
      value: readonly ["reporting-summary", Record<string, unknown>],
    ) => Promise<unknown>;

    expect(key).toEqual([
      "reporting-summary",
      {
        since: "2026-04-01T00:00:00.000Z",
        until: "2026-04-11T23:59:59.999Z",
      },
    ]);

    await fetcher(key);
    expect(mockedGetReportingSummary).toHaveBeenCalledWith({
      since: "2026-04-01T00:00:00.000Z",
      until: "2026-04-11T23:59:59.999Z",
    });
  });

  it("returns empty array when SWR has no data", () => {
    const mockedUseSWR = vi.mocked(useSWR);
    mockedUseSWR.mockReturnValue(makeSWRResult({ data: undefined }) as never);

    const result = useReportingSummary();
    expect(result.data).toEqual([]);
  });
});
