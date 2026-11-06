import { describe, expect, it } from "vitest";
import {
  countSendable,
  groupUnsentByRole,
  normalizeEmail,
  validateRows,
  type InviteRow,
} from "./invites";

const row = (
  id: number,
  email: string,
  role: InviteRow["role"] = "Agent",
  sent = false
): InviteRow => ({ id, email, role, sent });

describe("normalizeEmail", () => {
  it("trims and lowercases", () => {
    expect(normalizeEmail(" A@X.com ")).toBe("a@x.com");
  });
});

describe("validateRows", () => {
  it("ignores blank rows", () => {
    const { errors, duplicates } = validateRows([row(1, ""), row(2, "  ")]);
    expect(errors).toEqual({});
    expect(duplicates.size).toBe(0);
  });

  it("flags an address that is not an email", () => {
    const { errors } = validateRows([row(1, "nope")]);
    expect(Object.keys(errors)).toEqual(["1"]);
  });

  it("flags the later of two addresses that differ only by case", () => {
    const { errors, duplicates } = validateRows([
      row(1, "a@x.com"),
      row(2, "A@x.com"),
    ]);
    expect([...duplicates]).toEqual([2]);
    expect(Object.keys(errors)).toEqual(["2"]);
  });
});

describe("countSendable", () => {
  it("is zero for blank rows", () => {
    expect(countSendable([row(1, ""), row(2, " ")])).toBe(0);
  });

  it("is zero when the only address is invalid", () => {
    expect(countSendable([row(1, "nope")])).toBe(0);
  });

  it("counts valid unsent addresses and skips invalid, repeated and sent ones", () => {
    expect(
      countSendable([
        row(1, "a@x.com"),
        row(2, "A@x.com"),
        row(3, "nope"),
        row(4, "b@x.com", "Agent", true),
        row(5, "c@x.com"),
      ])
    ).toBe(2);
  });
});

describe("groupUnsentByRole", () => {
  it("groups normalized, unique addresses by role", () => {
    expect(
      groupUnsentByRole([
        row(1, "A@x.com"),
        row(2, "a@x.com"),
        row(3, "b@x.com", "Agent Manager"),
        row(4, ""),
      ])
    ).toEqual({ Agent: ["a@x.com"], "Agent Manager": ["b@x.com"] });
  });

  it("leaves out rows already sent, so a retry does not resend them", () => {
    expect(
      groupUnsentByRole([
        row(1, "sent@x.com", "Agent", true),
        row(2, "new@x.com", "Agent"),
      ])
    ).toEqual({ Agent: ["new@x.com"] });
  });

  it("skips an address already sent in another row", () => {
    expect(
      groupUnsentByRole([
        row(1, "a@x.com", "Agent", true),
        row(2, "A@x.com", "Agent Manager"),
      ])
    ).toEqual({});
  });
});
