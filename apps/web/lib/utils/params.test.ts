import { describe, expect, it } from "vitest";
import { getFirstParamValue, parseNonNegativeInt } from "@/lib/utils/params";

describe("parseNonNegativeInt", () => {
  it("returns parsed integer for valid non-negative input", () => {
    expect(parseNonNegativeInt("25", 10)).toBe(25);
    expect(parseNonNegativeInt("0", 10)).toBe(0);
  });

  it("returns fallback for negative, invalid, or null input", () => {
    expect(parseNonNegativeInt("-1", 10)).toBe(10);
    expect(parseNonNegativeInt("abc", 10)).toBe(10);
    expect(parseNonNegativeInt(null, 10)).toBe(10);
  });
});

describe("getFirstParamValue", () => {
  it("returns single string value directly", () => {
    expect(getFirstParamValue("abc")).toBe("abc");
  });

  it("returns first value for array input", () => {
    expect(getFirstParamValue(["abc", "def"])).toBe("abc");
  });

  it("returns null for undefined input", () => {
    expect(getFirstParamValue(undefined)).toBeNull();
  });
});
