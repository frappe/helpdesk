import { describe, expect, it } from "vitest";
import { shouldPoll } from "./polling";

describe("shouldPoll", () => {
  it("polls before a mailbox is connected, to notice an OAuth return", () => {
    expect(shouldPoll({ arrived: false, hidden: false })).toBe(true);
  });

  it("stops once the first ticket has arrived", () => {
    expect(shouldPoll({ arrived: true, hidden: false })).toBe(false);
  });

  it("pauses while the tab is hidden", () => {
    expect(shouldPoll({ arrived: false, hidden: true })).toBe(false);
  });
});
