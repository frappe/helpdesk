import { call } from "frappe-ui";
import type { RouteLocationNormalized, RouteLocationRaw } from "vue-router";

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
  try {
    if (localStorage.getItem(PERSONA_DONE_KEY)) return true;
  } catch {
    // storage blocked — fall through to the server flag
  }
  return !!auth.personaCaptured;
}

// window.telemetry is a boot value injected by www/helpdesk, so this is
// synchronous and guard-safe.
export function telemetryEnabled(): boolean {
  return !!window.telemetry?.enabled;
}

// Gate for the route's beforeEnter: only an uncaptured desk admin may view
// the wizard, even via URL.
export function canViewPersona(auth: PersonaAuth): boolean {
  return (
    auth.isLoggedIn &&
    auth.hasDeskAccess &&
    auth.isAdmin &&
    !isPersonaCaptured(auth)
  );
}

// Interrupt the first eligible admin navigation, once per session, only if
// telemetry is on. Returns where to redirect, or undefined to continue.
export function personaInterrupt(
  to: RouteLocationNormalized,
  auth: PersonaAuth
): RouteLocationRaw | undefined {
  if (to.name === "Persona" || personaChecked) return;
  if (!(auth.isLoggedIn && auth.hasDeskAccess && auth.isAdmin)) return;
  personaChecked = true;
  if (telemetryEnabled() && canViewPersona(auth)) return { name: "Persona" };
}

export async function markPersonaCaptured(brandName?: string): Promise<void> {
  localStorage.setItem(PERSONA_DONE_KEY, "1");
  await call("helpdesk.api.onboarding.mark_persona_captured", {
    brand_name: brandName,
  });
}
