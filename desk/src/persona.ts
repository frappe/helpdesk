import { call } from "frappe-ui";
import type { RouteLocationNormalized, RouteLocationRaw } from "vue-router";

export const PERSONA_DONE_KEY = "helpdesk_persona_captured";

let personaChecked = false;

// Minimal auth contract, so this module doesn't import the auth store (cycle).
interface PersonaAuth {
  isLoggedIn: boolean;
  hasDeskAccess: boolean;
  isAdmin: boolean;
  personaCaptured: boolean;
}

function isPersonaCaptured(auth: PersonaAuth): boolean {
  if (localStorage.getItem(PERSONA_DONE_KEY)) return true;
  return !!auth.personaCaptured;
}

export async function telemetryEnabled(): Promise<boolean> {
  const config = await call("frappe.utils.telemetry.pulse.client.boot_config");
  return !!config?.enabled;
}

// `done` means the guard should stop and next(to).
export async function personaRedirect(
  to: RouteLocationNormalized,
  auth: PersonaAuth
): Promise<{ done: boolean; to?: RouteLocationRaw }> {
  const isDeskAdmin = auth.isLoggedIn && auth.hasDeskAccess && auth.isAdmin;

  if (to.name === "Persona") {
    try {
      const allow = isDeskAdmin && !isPersonaCaptured(auth);
      return { done: true, to: allow ? undefined : { name: "Home" } };
    } catch {
      return { done: true, to: { name: "Home" } };
    }
  }

  // Interrupt an eligible admin once per session, only if telemetry is on.
  if (isDeskAdmin && !personaChecked) {
    personaChecked = true;
    try {
      if (!isPersonaCaptured(auth) && (await telemetryEnabled())) {
        return { done: true, to: { name: "Persona" } };
      }
    } catch {
      // fail open
    }
  }

  return { done: false };
}

export async function markPersonaCaptured(brandName?: string): Promise<void> {
  localStorage.setItem(PERSONA_DONE_KEY, "1");
  await call("helpdesk.api.onboarding.mark_persona_captured", {
    brand_name: brandName,
  });
}
