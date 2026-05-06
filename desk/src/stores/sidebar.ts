import { useStorage } from "@vueuse/core";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

export const useSidebarStore = defineStore("sidebar", () => {
  const isOpen = ref(true);
  const isExpanded = useStorage("sidebar_is_expanded", true);
  const width = computed(() => {
    return isExpanded.value ? "221px" : "50px";
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
