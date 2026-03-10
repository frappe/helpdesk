import { ListResource } from "@/types";
import { HDTicket } from "@/types/doctypes";
import { createListResource } from "frappe-ui";

export const ticketsListResource: ListResource<HDTicket> = createListResource({
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
});
