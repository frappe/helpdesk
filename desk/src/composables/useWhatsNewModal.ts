import type { WhatsNewRelease } from "@/composables/useBanners";
import { ref } from "vue";

const isOpen = ref(false);
// Kept here so the notes stay readable after the banner is gone
const releases = ref<WhatsNewRelease[]>([]);

export function useWhatsNewModal() {
  function show(notes: WhatsNewRelease[]) {
    releases.value = notes;
    isOpen.value = true;
  }

  return { isOpen, releases, show };
}
