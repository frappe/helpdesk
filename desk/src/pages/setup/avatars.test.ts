import { describe, expect, it } from "vitest";
import { avatarFor } from "./avatars";

describe("avatarFor", () => {
  it("returns an svg data uri", () => {
    expect(avatarFor("a@x.com")).toMatch(/^data:image\/svg\+xml/);
  });

  it("gives the same face for the same seed", () => {
    expect(avatarFor("a@x.com")).toBe(avatarFor("a@x.com"));
  });

  it("gives different faces for different seeds", () => {
    expect(avatarFor("a@x.com")).not.toBe(avatarFor("b@x.com"));
  });
});
