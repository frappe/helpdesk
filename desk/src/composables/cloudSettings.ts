import { mobileSidebarOpened } from "@/composables/mobile";
import { userStorage } from "@/composables/userStorage";
import { __ } from "@/translation";
import {
  getBilling,
  openCloudSettings,
  type BillingTrial,
} from "@frappe/cloud-sdk";
import { toast } from "frappe-ui";
import { computed, ref } from "vue";

// Days left change once a day, and each fetch goes through Pilot and Central uncached
const CACHE_MS = 6 * 60 * 60 * 1000;
const DISMISS_MS = 24 * 60 * 60 * 1000;

/** Frappe enables it only for System Managers on a Frappe Cloud v2 site. */
export const isCloudSettingsAvailable = () =>
  window.cloud_settings?.enabled === true;

const cachedTrial = userStorage<{
  trial: BillingTrial | null;
  fetchedAt: number;
}>("helpdesk-trial-card", { trial: null, fetchedAt: 0 });
const dismissedAt = userStorage("helpdesk-trial-card-dismissed-at", 0);
const opening = ref(false);

// Overlapping callers share one request
let pending: Promise<void> | null = null;

function refreshTrial() {
  pending ??= getBilling()
    .then(({ trial }) => {
      cachedTrial.value = { trial: trial ?? null, fetchedAt: Date.now() };
    })
    // The card is a reminder: if billing can't be read, show nothing
    .catch(() => (cachedTrial.value = { trial: null, fetchedAt: 0 }))
    .finally(() => (pending = null));
  return pending;
}

async function openBilling() {
  if (opening.value) return;
  opening.value = true;
  // The mobile drawer traps focus, which would fight the dialog's inputs
  mobileSidebarOpened.value = false;
  try {
    await openCloudSettings({
      panels: ["billing", "marketplace", "domains", "advanced"],
      tab: "billing",
      theme: "auto",
      // Choosing a plan in the dialog ends the trial
      onClose: refreshTrial,
    });
  } catch (error) {
    toast.error(
      error instanceof Error
        ? error.message
        : __("Could not open Cloud Settings")
    );
  } finally {
    opening.value = false;
  }
}

export function useCloudSettings() {
  return { opening, openBilling };
}

export function useTrialCard() {
  const stale = Date.now() - cachedTrial.value.fetchedAt > CACHE_MS;
  if (isCloudSettingsAvailable() && stale) refreshTrial();

  const trial = computed(() => {
    const trial = isCloudSettingsAvailable() ? cachedTrial.value.trial : null;
    if (!trial) return null;
    // An ended trial cannot be dismissed
    const dismissed = Date.now() - dismissedAt.value < DISMISS_MS;
    return dismissed && trial.state !== "Ended" ? null : trial;
  });

  return { trial, dismiss: () => (dismissedAt.value = Date.now()) };
}
