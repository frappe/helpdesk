import { mobileSidebarOpened } from "@/composables/mobile";
import { useBanners } from "@/composables/useBanners";
import { __ } from "@/translation";
import { openCloudSettings } from "@frappe/cloud-sdk";
import { toast } from "frappe-ui";
import { ref } from "vue";

/** Frappe enables it only for System Managers on a Frappe Cloud v2 site. */
export const isCloudSettingsAvailable = () =>
  window.cloud_settings?.enabled === true;

const opening = ref(false);

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
      onClose: () => useBanners().reload(),
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
