import { call } from "frappe-ui";

// localStorage mirrors the server flag so a failed persist can't re-loop the
// wizard next session. Distinct from the `useOnboarding` step tracker.
export const PERSONA_DONE_KEY = "helpdesk_persona_captured";

export async function isPersonaCaptured(): Promise<boolean> {
  if (localStorage.getItem(PERSONA_DONE_KEY)) return true;
  const captured = await call("frappe.client.get_single_value", {
    doctype: "HD Settings",
    field: "persona_captured",
  });
  return !!captured;
}

// The questionnaire's answers only feed telemetry, so there's no point showing
// it when telemetry is disabled.
export async function telemetryEnabled(): Promise<boolean> {
  const config = await call("frappe.utils.telemetry.pulse.client.boot_config");
  return !!config?.enabled;
}

export async function markPersonaCaptured(): Promise<void> {
  localStorage.setItem(PERSONA_DONE_KEY, "1");
  await call("helpdesk.api.onboarding.mark_persona_captured");
}
