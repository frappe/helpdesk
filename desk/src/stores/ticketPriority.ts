import { HDTicketPriority } from "@/types/doctypes";
import { createListResource } from "frappe-ui";
import { defineStore } from "pinia";

/** Order priorities appear in dropdowns and lists: Low → Urgent. Custom
 *  priorities (absent here) fall to the end. */
export const PRIORITY_DISPLAY_ORDER: Record<string, number> = {
  Low: 0,
  Medium: 1,
  High: 2,
  Urgent: 3,
};

export const useTicketPriorityStore = defineStore("ticketPriority", () => {
  const priorities = createListResource({
    doctype: "HD Ticket Priority",
    cache: ["HD Ticket Priority", "list"],
    fields: ["name", "level", "description", "disabled"],
    pageLength: 1000,
    auto: true,
  });

  function getLevel(name: string): string {
    const priority = priorities.data?.find(
      (p: HDTicketPriority) => p.name === name
    );
    return priority?.level ?? "Medium";
  }

  return { priorities, getLevel };
});
