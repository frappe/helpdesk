import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { useStorage } from "@vueuse/core";

export const useSidebarStore = defineStore("sidebar", () => {
  const isOpen = ref(true);
  const isExpanded = useStorage("sidebar_is_expanded", true);
  // Match frappe-ui Sidebar's width/collapsedWidth props (15rem/3rem),
  // since the notifications panel anchors against this value.
  const width = computed(() => {
    return isExpanded.value ? "15rem" : "3rem";
  });

  function toggle(state?: boolean) {
    isOpen.value = state ?? !isOpen.value;
  }

  function toggleExpanded(state?: boolean) {
    isExpanded.value = state ?? !isExpanded.value;
  }

  return {
    isExpanded,
    isOpen,
    toggle,
    toggleExpanded,
    width,
  };
});
