import { describe, expect, it } from "vitest";
import {
  PAYMENT_STATUSES,
  parsePaymentStatus,
} from "@/lib/utils/payment-filters";

describe("payment filters", () => {
  it("defines expected payment statuses", () => {
    expect(PAYMENT_STATUSES).toEqual([
      "pending",
      "succeeded",
      "failed",
      "refunded",
      "disputed",
    ]);
  });

  it("parses valid payment status", () => {
    expect(parsePaymentStatus("pending")).toBe("pending");
    expect(parsePaymentStatus("succeeded")).toBe("succeeded");
  });

  it("returns undefined for invalid status values", () => {
    expect(parsePaymentStatus("authorized")).toBeUndefined();
    expect(parsePaymentStatus(null)).toBeUndefined();
  });
});
