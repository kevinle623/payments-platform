// @vitest-environment jsdom

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Tabs } from "@/components/common/tabs";

const TEST_TABS = [
  { id: "one", label: "One", content: <div>Panel One</div> },
  { id: "two", label: "Two", content: <div>Panel Two</div> },
  { id: "three", label: "Three", content: <div>Panel Three</div> },
];

describe("Tabs", () => {
  it("changes active tab with keyboard navigation", () => {
    render(<Tabs tabs={TEST_TABS} />);

    const tablist = screen.getByRole("tablist");
    const tabOne = screen.getByRole("tab", { name: "One" });
    const tabTwo = screen.getByRole("tab", { name: "Two" });
    const tabThree = screen.getByRole("tab", { name: "Three" });

    expect(tabOne.getAttribute("aria-selected")).toBe("true");
    expect(screen.getByText("Panel One")).toBeTruthy();

    fireEvent.keyDown(tablist, { key: "ArrowRight" });
    expect(tabTwo.getAttribute("aria-selected")).toBe("true");
    expect(document.activeElement).toBe(tabTwo);
    expect(screen.getByText("Panel Two")).toBeTruthy();

    fireEvent.keyDown(tablist, { key: "End" });
    expect(tabThree.getAttribute("aria-selected")).toBe("true");
    expect(document.activeElement).toBe(tabThree);
    expect(screen.getByText("Panel Three")).toBeTruthy();

    fireEvent.keyDown(tablist, { key: "Home" });
    expect(tabOne.getAttribute("aria-selected")).toBe("true");
    expect(document.activeElement).toBe(tabOne);
  });

  it("emits onValueChange when selecting tabs", () => {
    const onValueChange = vi.fn();
    render(<Tabs tabs={TEST_TABS} onValueChange={onValueChange} />);

    const tabTwo = screen.getByRole("tab", { name: "Two" });
    fireEvent.click(tabTwo);

    expect(onValueChange).toHaveBeenCalledWith("two");
  });
});
