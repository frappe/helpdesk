import { call } from "frappe-ui";
import type { RouteLocationRaw } from "vue-router";

const PERSONA_DONE_KEY = "helpdesk_persona_captured";

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

// Gate for the route's beforeEnter: only an uncaptured desk admin may view
// the wizard, even via URL. Fail safe — never break navigation.
export function canViewPersona(auth: PersonaAuth): boolean {
  try {
    return (
      auth.isLoggedIn &&
      auth.hasDeskAccess &&
      auth.isAdmin &&
      !isPersonaCaptured(auth)
    );
  } catch {
    return false;
  }
}

// Interrupt an eligible admin once per session, only if telemetry is on.
// Returns where to redirect, or undefined to continue the navigation.
export async function personaInterrupt(
  auth: PersonaAuth
): Promise<RouteLocationRaw | undefined> {
  const isDeskAdmin = auth.isLoggedIn && auth.hasDeskAccess && auth.isAdmin;
  if (!isDeskAdmin || personaChecked) return;
  personaChecked = true;
  try {
    if (!isPersonaCaptured(auth) && (await telemetryEnabled())) {
      return { name: "Persona" };
    }
  } catch {
    // fail open
  }
}

export async function markPersonaCaptured(brandName?: string): Promise<void> {
  localStorage.setItem(PERSONA_DONE_KEY, "1");
  await call("helpdesk.api.onboarding.mark_persona_captured", {
    brand_name: brandName,
  });
}
