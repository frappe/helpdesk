import { describe, expect, it } from "vitest";
import { canViewSetup, setupRedirect } from "./guard";

describe("setupRedirect", () => {
  it("sends a pending admin to Setup and keeps the query for the OAuth return", () => {
    expect(
      setupRedirect(
        { name: "Home", query: { email_oauth: "1" } },
        { isLoggedIn: true, hasDeskAccess: true, setupPending: true }
      )
    ).toEqual({ name: "Setup", query: { email_oauth: "1" } });
  });

  it("does not redirect when already on Setup", () => {
    expect(
      setupRedirect(
        { name: "Setup", query: {} },
        { isLoggedIn: true, hasDeskAccess: true, setupPending: true }
      )
    ).toBeUndefined();
  });

  it("does not redirect when setup is not pending", () => {
    expect(
      setupRedirect(
        { name: "Home", query: {} },
        { isLoggedIn: true, hasDeskAccess: true, setupPending: false }
      )
    ).toBeUndefined();
  });

  it("does not redirect someone who is logged out or has no desk access", () => {
    const to = { name: "Home", query: {} };
    expect(
      setupRedirect(to, {
        isLoggedIn: false,
        hasDeskAccess: false,
        setupPending: true,
      })
    ).toBeUndefined();
    expect(
      setupRedirect(to, {
        isLoggedIn: true,
        hasDeskAccess: false,
        setupPending: true,
      })
    ).toBeUndefined();
  });
});

describe("canViewSetup", () => {
  it("is open to an admin while setup is pending", () => {
    expect(canViewSetup({ isAdmin: true, setupPending: true })).toBe(true);
  });

  it("is closed to a non-admin", () => {
    expect(canViewSetup({ isAdmin: false, setupPending: true })).toBe(false);
  });

  it("is closed once setup is done", () => {
    expect(canViewSetup({ isAdmin: true, setupPending: false })).toBe(false);
  });
});
