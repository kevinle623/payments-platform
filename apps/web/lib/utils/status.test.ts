import { describe, expect, it } from "vitest";
import { getStatusMeta } from "@/lib/utils/status";

describe("getStatusMeta", () => {
  it("returns mapped status metadata for known values", () => {
    expect(getStatusMeta("payment", "succeeded")).toEqual({
      label: "Succeeded",
      variant: "success",
    });
    expect(getStatusMeta("outbox", "pending")).toEqual({
      label: "Pending",
      variant: "warning",
    });
  });

  it("falls back to neutral for unknown values", () => {
    expect(getStatusMeta("payment", "custom_status")).toEqual({
      label: "custom_status",
      variant: "neutral",
    });
  });

  it("falls back to unknown label when status is missing", () => {
    expect(getStatusMeta("payment", null)).toEqual({
      label: "Unknown",
      variant: "neutral",
    });
  });
});
