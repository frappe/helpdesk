import { describe, expect, it } from "vitest";
import { getInviteByEmailRoles, getInviteRoleOptions } from "./inviteRoles";

const values = (user: { isAdmin: boolean; isManager: boolean }) =>
  getInviteRoleOptions(user).map((option) => option.value);

describe("getInviteRoleOptions", () => {
  it("lets an admin grant every role", () => {
    expect(values({ isAdmin: true, isManager: true })).toEqual([
      "Agent",
      "Agent Manager",
      "System Manager",
    ]);
  });

  it("lets a manager grant Agent and Agent Manager", () => {
    expect(values({ isAdmin: false, isManager: true })).toEqual([
      "Agent",
      "Agent Manager",
    ]);
  });

  it("lets anyone else grant Agent only", () => {
    expect(values({ isAdmin: false, isManager: false })).toEqual(["Agent"]);
  });
});

describe("getInviteByEmailRoles", () => {
  it("adds the lower roles to a System Manager invite", () => {
    expect(getInviteByEmailRoles("System Manager")).toEqual([
      "Agent",
      "Agent Manager",
      "System Manager",
    ]);
  });

  it("sends just Agent for an Agent invite", () => {
    expect(getInviteByEmailRoles("Agent")).toEqual(["Agent"]);
  });
});
