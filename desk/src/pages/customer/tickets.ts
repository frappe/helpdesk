import type { ListResource } from "@/types";
import type { HDTicket } from "@/types/doctypes";
import { createListResource } from "frappe-ui";

export function getTicketListResource(): {
  ticketsListResource: ListResource<HDTicket>;
} {
  return {
    ticketsListResource: createListResource({
      doctype: "HD Ticket",
      pageLength: 20,
      fields: [
        "name",
        "subject",
        "status",
        "priority",
        "creation",
        "modified",
        "_assign",
        "response_by",
        "resolution_by",
      ],
      orderBy: "modified desc",
    }),
  };
}
