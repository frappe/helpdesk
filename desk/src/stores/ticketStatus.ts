import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";
import { HDTicketStatus } from "@/types/doctypes";
import { parseColor } from "@/utils";

export const useTicketStatusStore = defineStore("ticketStatus", () => {
  const options = ref(["Open", "Replied", "Resolved", "Closed"]);
  const statuses = createListResource({
    doctype: "HD Ticket Status",
    fields: [
      "label_agent",
      "label_customer",
      "order",
      "different_view",
      "category",
      "color",
    ],
    orderBy: "`tabHD Ticket Status`.order",
    pageLength: 1000,
    auto: true,
    transform: (data: HDTicketStatus[]) => {
      return data.map((d) => {
        if (!d.different_view) {
          d.label_customer = d.label_agent;
        }
        d["parsed_color"] = parseColor(d.color);
        return d;
      });
    },
  });

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
  function getStatus(label: string): HDTicketStatus | undefined {
    return statuses.data?.find(
      (s: HDTicketStatus) =>
        s.label_agent === label || s.label_customer === label
    );
  }

  return {
    colorMap,
    statuses,
    options,
    textColorMap,
    getStatus,
  };
});
