import type { Customizations, DocumentResource, Resource } from "@/types";
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
  assignees: Resource<string[]>;
  customizations: Resource<Customizations>;
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
        fields: ["allocated_to as assignedTo"],
        transform: (data: Record<"assignedTo", string>[]) => {
          const assignees = new Set(data.map((item) => item.assignedTo));
          return Array.from(assignees);
        },
      }),
      customizations: createResource({
        url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_customizations",
        auto: true,
      }),
    };
  }

  return ticketMap[ticketId];
};
