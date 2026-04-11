import { describe, expect, it } from "vitest";
import {
  isDigitsOnly,
  isValidLastFour,
  normalizeCurrencyCode,
  parseMajorAmountToMinor,
} from "@/lib/utils/forms";

describe("normalizeCurrencyCode", () => {
  it("normalizes whitespace and case", () => {
    expect(normalizeCurrencyCode(" USD ")).toBe("usd");
  });
});

describe("parseMajorAmountToMinor", () => {
  it("parses valid positive major amount values", () => {
    expect(parseMajorAmountToMinor("10")).toBe(1000);
    expect(parseMajorAmountToMinor("10.99")).toBe(1099);
  });

  it("rejects invalid and non-positive values by default", () => {
    expect(parseMajorAmountToMinor("0")).toBeNull();
    expect(parseMajorAmountToMinor("-1")).toBeNull();
    expect(parseMajorAmountToMinor("abc")).toBeNull();
  });

  it("allows zero when configured", () => {
    expect(parseMajorAmountToMinor("0", { allowZero: true })).toBe(0);
  });
});

describe("isDigitsOnly", () => {
  it("validates digit-only strings", () => {
    expect(isDigitsOnly("123456")).toBe(true);
    expect(isDigitsOnly("123a")).toBe(false);
  });
});

describe("isValidLastFour", () => {
  it("accepts empty or exactly four digits", () => {
    expect(isValidLastFour("")).toBe(true);
    expect(isValidLastFour("4242")).toBe(true);
  });

  it("rejects non-digit or wrong-length values", () => {
    expect(isValidLastFour("123")).toBe(false);
    expect(isValidLastFour("12a4")).toBe(false);
    expect(isValidLastFour("12345")).toBe(false);
  });
});
