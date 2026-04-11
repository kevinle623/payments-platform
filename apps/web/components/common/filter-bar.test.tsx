// @vitest-environment jsdom

import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FilterBar } from "@/components/common/filter-bar";

const navState = vi.hoisted(() => ({
  pathname: "/payments",
  search: "status=failed&limit=25",
  replace: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: navState.replace }),
  usePathname: () => navState.pathname,
  useSearchParams: () => new URLSearchParams(navState.search),
}));

function getQueryFromPath(pathWithQuery: string): URLSearchParams {
  const [, query = ""] = pathWithQuery.split("?");
  return new URLSearchParams(query);
}

function TestFilterBar() {
  return (
    <FilterBar>
      {({ getValue, setValue, setValues, clearValues }) => (
        <div>
          <span data-testid="status-value">{getValue("status")}</span>
          <button type="button" onClick={() => setValue("status", "succeeded")}>
            set-status
          </button>
          <button
            type="button"
            onClick={() => setValues({ status: "pending", offset: "0" })}
          >
            set-multiple
          </button>
          <button type="button" onClick={() => clearValues(["status"])}>
            clear-status
          </button>
          <button type="button" onClick={() => clearValues()}>
            clear-all
          </button>
        </div>
      )}
    </FilterBar>
  );
}

describe("FilterBar", () => {
  beforeEach(() => {
    navState.pathname = "/payments";
    navState.search = "status=failed&limit=25";
    navState.replace.mockClear();
  });

  it("reads value and updates a single query param", () => {
    render(<TestFilterBar />);
    expect(screen.getByTestId("status-value").textContent).toBe("failed");

    fireEvent.click(screen.getByRole("button", { name: "set-status" }));

    expect(navState.replace).toHaveBeenCalledTimes(1);
    const [path, options] = navState.replace.mock.calls[0] as [
      string,
      { scroll: boolean },
    ];

    expect(path.startsWith("/payments?")).toBe(true);
    const query = getQueryFromPath(path);
    expect(query.get("status")).toBe("succeeded");
    expect(query.get("limit")).toBe("25");
    expect(options).toEqual({ scroll: false });
  });

  it("supports multi-update and clear operations", () => {
    render(<TestFilterBar />);

    fireEvent.click(screen.getByRole("button", { name: "set-multiple" }));
    let [path] = navState.replace.mock.calls[0] as [string];
    let query = getQueryFromPath(path);
    expect(query.get("status")).toBe("pending");
    expect(query.get("offset")).toBe("0");
    expect(query.get("limit")).toBe("25");

    fireEvent.click(screen.getByRole("button", { name: "clear-status" }));
    [path] = navState.replace.mock.calls[1] as [string];
    query = getQueryFromPath(path);
    expect(query.get("status")).toBeNull();
    expect(query.get("limit")).toBe("25");

    fireEvent.click(screen.getByRole("button", { name: "clear-all" }));
    [path] = navState.replace.mock.calls[2] as [string];
    expect(path).toBe("/payments");
  });
});
