import { userStorage } from "@/composables/userStorage";

const setupDone = userStorage("helpdesk_setup_completed", false);

/** Boot flags setup for a System Manager on a v2 site; a local mark keeps a failed save from bringing it back. */
export function isSetupPending(): boolean {
  return !!window.setup_pending && !setupDone.value;
}

export function markSetupDoneLocally() {
  setupDone.value = true;
}
