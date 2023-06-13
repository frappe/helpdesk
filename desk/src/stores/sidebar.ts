import { onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { defineStore } from "pinia";

const MINIMISE_ON = ["DeskTicket", "Settings"];

export const useSidebarStore = defineStore("sidebar", () => {
  const route = useRoute();
  const isOpen = ref(true);
  const isExpanded = ref(true);

  function toggle(state?: boolean) {
    isOpen.value = state ?? !isOpen.value;
  }

  function toggleExpanded(state?: boolean) {
    isExpanded.value = state ?? !isExpanded.value;
  }

  function setMinimised() {
    toggleExpanded(
      !route.matched.find((r) => MINIMISE_ON.includes(r.name.toString()))
    );
  }

  onMounted(setMinimised);
  watch(route, setMinimised);

  return {
    isOpen,
    isExpanded,
    toggle,
    toggleExpanded,
  };
});
