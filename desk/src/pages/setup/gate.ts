import { __ } from "@/translation";
import { call, toast } from "frappe-ui";

const DONE_KEY = "helpdesk_setup_completed";

/** Boot flags setup for a System Manager on a v2 site; a local mark keeps a failed save from bringing it back. */
export function isSetupPending(): boolean {
  if (!window.setup_pending) return false;
  try {
    return localStorage.getItem(DONE_KEY) !== "1";
  } catch {
    return true;
  }
}

export function markSetupDoneLocally() {
  try {
    localStorage.setItem(DONE_KEY, "1");
  } catch {}
}

/** Developer mode: `?reset_setup` on any desk page starts the first-run setup over, with this browser's storage cleared. */
export async function resetSetup() {
  try {
    await call("helpdesk.api.setup.reset_setup");
  } catch (e) {
    toast.error(e.messages?.join(" ") || __("Could not reset setup"));
    return false;
  }
  try {
    localStorage.clear();
    sessionStorage.clear();
  } catch {}
  window.location.replace("/helpdesk/setup");
  return true;
}
