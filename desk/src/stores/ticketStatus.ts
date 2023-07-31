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
  const colorMapAgent = {
    Open: "red",
    Replied: "orange",
    Resolved: "green",
    Closed: "blue",
  };
  const colorMapCustomer = {
    Open: "red",
    Replied: "orange",
    Resolved: "green",
    Closed: "blue",
  };
  const stateActive = ["Open", "Replied"];
  const stateInactive = ["Resolved", "Closed"];

  return {
    dropdown,
    options,
    colorMapAgent,
    colorMapCustomer,
    stateActive,
    stateInactive,
  };
});
