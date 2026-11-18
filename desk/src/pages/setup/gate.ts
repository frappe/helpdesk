import { userStorage } from "@/composables/userStorage";
import { __ } from "@/translation";
import { call, toast } from "frappe-ui";

const setupDone = userStorage("helpdesk_setup_completed", false);

/** Boot flags setup for a System Manager on a v2 site; a local mark keeps a failed save from bringing it back. */
export function isSetupPending(): boolean {
  return !!window.setup_pending && !setupDone.value;
}

export function markSetupDoneLocally() {
  setupDone.value = true;
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
