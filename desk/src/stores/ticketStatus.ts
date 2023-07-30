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
  const statusColormapAgent = {
    Open: "red",
    Replied: "orange",
    Resolved: "green",
    Closed: "blue",
  };
  const statusColormapCustomer = {
    Open: "red",
    Replied: "orange",
    Resolved: "green",
    Closed: "blue",
  };

  return {
    dropdown,
    options,
    statusColormapAgent,
    statusColormapCustomer,
  };
});
