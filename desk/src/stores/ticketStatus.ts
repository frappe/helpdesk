import { HDTicketStatus } from "@/types/doctypes";
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
    Green: ["text-ink-green-6", "bg-surface-green-2"],
    Black: ["text-ink-gray-9", "bg-surface-gray-2"],
    Gray: ["text-ink-gray-7", "bg-surface-gray-2"],
    Blue: ["text-ink-blue-6", "bg-surface-blue-2"],
    Red: ["text-ink-red-6", "bg-surface-red-1"],
    Pink: ["text-ink-pink-1", "bg-surface-pink-1"],
    Orange: ["text-ink-orange-6", "bg-surface-orange-1"],
    Amber: ["text-ink-amber-6", "bg-surface-amber-2"],
    Yellow: ["text-ink-yellow-6", "bg-surface-amber-2"],
    Cyan: ["text-ink-cyan-6", "bg-surface-cyan-1"],
    Teal: ["text-ink-teal-6", "bg-surface-teal-1"],
    Violet: ["text-ink-violet-6", "bg-surface-violet-1"],
    Purple: ["text-ink-purple-6", "bg-surface-purple-1"],
    Default: ["text-ink-gray-9", "bg-surface-gray-2"],
  };

  return {
    statuses,
    colorMap,
    getStatus,
  };
});
// Spelt out so Tailwind's scanner sees every class. Keys mirror the
// HD Ticket Status "color" Select.
const dotColorMap: Record<string, string> = {
  Black: "!text-ink-gray-9",
  Gray: "!text-gray-500",
  Blue: "!text-blue-500",
  Green: "!text-green-500",
  Red: "!text-red-500",
  Pink: "!text-pink-500",
  Orange: "!text-orange-500",
  Amber: "!text-amber-500",
  Yellow: "!text-yellow-500",
  Cyan: "!text-cyan-500",
  Teal: "!text-teal-500",
  Violet: "!text-violet-500",
  Purple: "!text-purple-500",
};

export function parseColor(color: string): string {
  return dotColorMap[color] ?? dotColorMap.Gray;
}
