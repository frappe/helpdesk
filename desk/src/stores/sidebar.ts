import { ref } from 'vue';
import { defineStore } from 'pinia';

export const useSidebarStore = defineStore('sidebar', () => {
  const isOpen = ref(true);

  function toggle(state?: boolean) {
    isOpen.value = state ?? !isOpen.value;
  }

  return {
    isOpen,
    toggle,
  };
});
