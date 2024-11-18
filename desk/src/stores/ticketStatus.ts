import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { createResource } from "frappe-ui";

export const useTicketStatusStore = defineStore("ticketStatus", () => {


  const options = ref([]);

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

  const textColorMap = {
    Open: "!text-red-600",
    Replied: "!text-blue-600",
    "Awaiting Response": "!text-blue-600",
    Resolved: "!text-green-700",
    Closed: "!text-gray-700",
  };

  const stateActive = ["Open", "Replied"];
  const stateInactive = ["Resolved", "Closed"];

  const tickets = createResource({
    url: "helpdesk.api.doc.get_status_options",
    params: {
      doctype: "HD Ticket",
    },
    auto: true,
    onSuccess(Data) {
      options.value = Data.options;
    },
  });
  return {
    colorMap,
    dropdown,
    options,
    stateActive,
    stateInactive,
    textColorMap,
  };
});