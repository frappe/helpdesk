import { describe, expect, it } from "vitest";
import { AGENT_SLOTS, rootPath } from "./previewPaths";

describe("rootPath", () => {
  it("ends on the agent it leads to", () => {
    for (const [x, y] of AGENT_SLOTS) {
      expect(rootPath(x, y).endsWith(`${x} ${y}`)).toBe(true);
    }
  });
});
