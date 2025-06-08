import { createResource } from "frappe-ui";
import { defineStore } from "pinia";
import { computed } from "vue";

export const useTicketStatusStore = defineStore("ticketStatus", () => {
  const options = createResource({
    url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_statuses",
    auto: true,
    cache: ["ticket_statuses"],
  });
  const dropdown = computed(() =>
    options.data?.map((o) => ({
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

  return {
    colorMap,
    dropdown,
    options,
    stateActive,
    stateInactive,
    textColorMap,
  };
});
