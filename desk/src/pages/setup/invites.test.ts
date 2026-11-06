import { describe, expect, it } from "vitest";
import {
  groupUnsentByRole,
  normalizeEmail,
  previewInvitees,
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

describe("previewInvitees", () => {
  it("lists each valid address once, keeping the sent state", () => {
    expect(
      previewInvitees([
        row(1, "a@x.com", "Agent", true),
        row(2, "A@x.com"),
        row(3, "nope"),
        row(4, "b@x.com", "Agent Manager"),
      ])
    ).toEqual([
      { email: "a@x.com", role: "Agent", sent: true },
      { email: "b@x.com", role: "Agent Manager", sent: false },
    ]);
  });
});
