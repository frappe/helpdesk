import { __ } from "@/translation";
import type {
  DocumentResource,
  RecentSimilarTicket,
  Resource,
  TicketActivities,
  TicketAssignee,
  TicketContact,
} from "@/types";
import type { HDTicket } from "@/types/doctypes";
import { createDocumentResource, createResource, toast } from "frappe-ui";
import { reactive } from "vue";

interface MapValue {
  ticket: DocumentResource<HDTicket>;
  assignees: Resource<TicketAssignee[]>;
  contact: Resource<TicketContact>;
  recentSimilarTickets: Resource<RecentSimilarTicket>;
  activities: Resource<TicketActivities>;
}

const ticketMap: Record<string, MapValue> = reactive({});

export const useTicket = (ticketId: string | number): MapValue => {
  const mapKey = String(ticketId);

  if (!ticketMap[mapKey]) {
    ticketMap[mapKey] = {
      ticket: createDocumentResource<HDTicket>({
        doctype: "HD Ticket",
        name: mapKey,
        whitelistedMethods: {
          markSeen: "mark_seen",
        },
        setValue: {
          onSuccess: () => {
            toast.success(__("Ticket updated successfully."));
          },
          onError: (error) => {
            let msg = error.message || "";
            if (
              msg.toLowerCase().includes("already in the following") || 
              msg.toLowerCase().includes("todo list")
            ) {
              return;
            }
            toast.error(msg.replace(/<br\s*\/?>/gi, "\n").trim());
          },
        },
      }),
      assignees: createResource({
        url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_assignees",
        params: { ticket: mapKey },
        auto: true,
        // Updates assignments via API safely and catches backend ToDo exceptions
        setValue: {
          onSuccess: () => {
            toast.success(__("Assignees updated successfully."));
            ticketMap[mapKey].assignees.reload(); 
          },
          onError: (error) => {
            let msg = error.message || "";
            if (
              msg.toLowerCase().includes("already in the following") || 
              msg.toLowerCase().includes("todo list")
            ) {
              return;
            }
            toast.error(msg.replace(/<br\s*\/?>/gi, "\n").trim());
          }
        }
        // Transform hook removed completely because backend already yields native TicketAssignee structures.
      }),
      contact: createResource({
        url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_contact",
        params: { ticket: mapKey },
        auto: true,
      }),
      recentSimilarTickets: createResource({
        url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_recent_similar_tickets",
        params: { ticket: mapKey },
        auto: true,
      }),
      activities: createResource({
        url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_activities",
        params: { ticket: mapKey },
        auto: true,
      }),
    };
  }

  return ticketMap[mapKey];
};

export function reloadTicket(ticketId: string | number) {
  const ticketData = ticketMap[String(ticketId)];
  if (!ticketData) return;
  ticketData.ticket.reload();
  ticketData.assignees.reload();
  ticketData.activities.reload();
}