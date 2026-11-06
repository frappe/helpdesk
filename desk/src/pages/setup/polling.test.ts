import { describe, expect, it } from "vitest";
import { MAX_POLLS, pollDelay } from "./polling";

describe("pollDelay", () => {
  it("polls quickly at first so a fresh ticket shows up fast", () => {
    expect(pollDelay(0)).toBe(5000);
    expect(pollDelay(5)).toBe(5000);
  });

  it("backs off as the wait drags on", () => {
    expect(pollDelay(6)).toBe(15000);
    expect(pollDelay(13)).toBe(15000);
    expect(pollDelay(14)).toBe(30000);
    expect(pollDelay(23)).toBe(30000);
  });

  it("gives up after a bounded number of polls", () => {
    expect(pollDelay(24)).toBeNull();
    expect(pollDelay(MAX_POLLS)).toBeNull();
    expect(pollDelay(MAX_POLLS - 1)).not.toBeNull();
  });
});
