import { computed, ref } from "vue";
import { defineStore } from "pinia";

export const useTicketStatusStore = defineStore("ticketStatus", () => {
  const options = ref(["Open", "Replied", "Resolved", "Closed"]);
  const dropdown = computed(() =>
    options.value.map((o) => ({
      label: o,
      value: o,
    }))
  );
  const colorMap = {
    Open: "red",
    Replied: "blue",
    Resolved: "green",
    Closed: "gray",
  };
  const stateActive = ["Open", "Replied"];
  const stateInactive = ["Resolved", "Closed"];

  return {
    colorMap,
    dropdown,
    options,
    stateActive,
    stateInactive,
  };
});
