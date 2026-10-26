import { markRaw } from "vue";
import OrganizationsIcon from "../OrganizationsIcon.vue";
import { __ } from "../translation";

// The desk's access icons; a function so labels translate once loaded.
export function categoryAccess(): Record<string, { icon: unknown; label: string }> {
  return {
    Public: { icon: "lucide-globe", label: __("Public") },
    Customers: { icon: markRaw(OrganizationsIcon), label: __("Customers") },
    Private: { icon: "lucide-lock", label: __("Private") },
    Mixed: { icon: "lucide-blend", label: __("Mixed") },
  };
}
