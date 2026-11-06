import { reactive, ref } from "vue";
import { describe, expect, it } from "vitest";
import { canAskForFeedback } from "./feedback";

// useTelemetry() returns a reactive object, so isEnabled is already unwrapped
describe("canAskForFeedback", () => {
  it("is true when telemetry is on", () => {
    expect(canAskForFeedback(reactive({ isEnabled: ref(true) }))).toBe(true);
  });

  it("is false when telemetry is off", () => {
    expect(canAskForFeedback(reactive({ isEnabled: ref(false) }))).toBe(false);
  });
});
