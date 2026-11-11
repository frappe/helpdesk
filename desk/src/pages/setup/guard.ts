import type { RouteLocationRaw } from "vue-router";

/** Sends a signed-in desk user whose site is still pending setup to the Setup page. */
export function setupRedirect(
  to: { name?: string | symbol | null; query: object },
  auth: { isLoggedIn: boolean; hasDeskAccess: boolean; setupPending: boolean }
): RouteLocationRaw | undefined {
  if (!auth.isLoggedIn || !auth.hasDeskAccess || !auth.setupPending) return;
  if (to.name === "Setup") return;
  // the query carries ?email_oauth back from the mail provider
  return { name: "Setup", query: to.query as Record<string, string> };
}

export const canViewSetup = (auth: {
  isAdmin: boolean;
  setupPending: boolean;
}) => auth.isAdmin && auth.setupPending;
