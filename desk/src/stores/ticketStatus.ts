import { HDTicketStatus } from "@/types/doctypes";
import { parseColor } from "@/utils";
import { createListResource } from "frappe-ui";
import { defineStore } from "pinia";

export const useTicketStatusStore = defineStore("ticketStatus", () => {
  const statuses = createListResource({
    doctype: "HD Ticket Status",
    cache: ["HD Ticket Status", "list"],
    fields: [
      "label_agent",
      "label_customer",
      "order",
      "different_view",
      "category",
      "color",
      "enabled",
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

  function getStatus(label: string): HDTicketStatus | undefined {
    return statuses.data?.find(
      (s: HDTicketStatus) =>
        s.label_agent === label || s.label_customer === label
    );
  }
  const colorMap = {
    Green: ["text-green-700", "bg-surface-green-2"],
    Black: ["text-black", "bg-surface-gray-2"],
    Gray: ["text-gray-700", "bg-surface-gray-2"],
    Blue: ["text-blue-700", "bg-surface-blue-2"],
    Red: ["text-red-500", "bg-surface-red-1"],
    Pink: ["text-pink-500", "bg-surface-pink-1"],
    Orange: ["text-orange-600", "bg-surface-orange-1"],
    Amber: ["text-amber-700", "bg-surface-amber-2"],
    Yellow: ["text-yellow-700", "bg-surface-amber-2"],
    Cyan: ["text-cyan-700", "bg-surface-cyan-1"],
    Teal: ["text-teal-700", "bg-teal-100"],
    Violet: ["text-violet-700", "bg-surface-violet-1"],
    Purple: ["text-purple-700", "bg-purple-100"],
    Default: ["text-ink-gray-9", "bg-surface-gray-2"],
  };

  return {
    statuses,
    colorMap,
    getStatus,
  };
});
function parseColor(color: string): string {
  color = color.toLowerCase();
  let textColor = `!text-${color}-600`;
  if (color == "black") {
    textColor = "!text-ink-gray-9";
  } else if (["gray", "green"].includes(color)) {
    textColor = `!text-${color}-700`;
  }

  return textColor;
}
