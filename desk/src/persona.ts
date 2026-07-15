import { useAuthStore } from "@/stores/auth";
import { call } from "frappe-ui";

// localStorage mirrors the boot flag so a failed persist can't re-loop the
// wizard next session. Distinct from the `useOnboarding` step tracker.
export const PERSONA_DONE_KEY = "helpdesk_persona_captured";

// Both sources are already loaded (localStorage + the auth boot), so this stays
// synchronous — the guard decides without a settings round-trip or a flash.
export function isPersonaCaptured(): boolean {
  if (localStorage.getItem(PERSONA_DONE_KEY)) return true;
  return !!useAuthStore().personaCaptured;
}

// The questionnaire's answers only feed telemetry, so there's no point showing
// it when telemetry is disabled.
export async function telemetryEnabled(): Promise<boolean> {
  const config = await call("frappe.utils.telemetry.pulse.client.boot_config");
  return !!config?.enabled;
}

// The org name entered in the questionnaire becomes the HD Settings brand name.
export async function markPersonaCaptured(brandName?: string): Promise<void> {
  localStorage.setItem(PERSONA_DONE_KEY, "1");
  await call("helpdesk.api.onboarding.mark_persona_captured", {
    brand_name: brandName,
  });
}
