import { describe, expect, it } from "vitest";
import { formatAmount, truncateId } from "@/lib/utils/format";

describe("formatAmount", () => {
  it("formats non-zero-decimal currencies from minor units", () => {
    expect(formatAmount(5000, "usd")).toBe("$50.00");
  });

  it("formats zero-decimal currencies without dividing by 100", () => {
    expect(formatAmount(5000, "jpy")).toBe("¥5,000");
  });
});

describe("truncateId", () => {
  it("truncates long identifiers", () => {
    expect(truncateId("1234567890abcdef", 6, 4)).toBe("123456…cdef");
  });

  it("keeps short identifiers unchanged", () => {
    expect(truncateId("12345", 6, 4)).toBe("12345");
  });
});
