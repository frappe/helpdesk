import type { DocumentResource, Resource, TicketContact } from "@/types";
import type { HDTicket } from "@/types/doctypes";
import {
  createDocumentResource,
  createListResource,
  createResource,
  toast,
} from "frappe-ui";
import { reactive } from "vue";

interface MapValue {
  ticket: DocumentResource<HDTicket>;
  assignees: Resource<Record<"name", string>[]>;
  contact: Resource<TicketContact>;
}

const ticketMap: Record<string, MapValue> = reactive({});

export const useTicket = (ticketId: string): MapValue => {
  if (!ticketMap[ticketId]) {
    ticketMap[ticketId] = {
      ticket: createDocumentResource<HDTicket>({
        doctype: "HD Ticket",
        name: ticketId,
        whitelistedMethods: {
          markSeen: "mark_seen",
        },
        setValue: {
          onSuccess: () => {
            toast.success(__("Ticket updated"));
          },
        },
      }),
      assignees: createListResource({
        doctype: "ToDo",
        auto: true,
        filters: {
          reference_type: "HD Ticket",
          reference_name: ticketId,
          status: ["not in", ["Cancelled", "Closed"]],
        },
        fields: ["allocated_to as name"],
      }),
      contact: createResource({
        url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_contact",
        params: { ticket: ticketId },
        auto: true,
      }),
    };
  }

  return ticketMap[ticketId];
};
