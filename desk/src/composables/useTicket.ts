import { DocumentResource } from "@/types";
import { HDTicket } from "@/types/doctypes";
import { createDocumentResource, toast } from "frappe-ui";

const ticketMap: Record<string, DocumentResource<HDTicket>> = {};
const assigneeMap = {};

export const useTicket = (ticketId: string): DocumentResource<HDTicket> => {
  if (!ticketMap[ticketId]) {
    ticketMap[ticketId] = createDocumentResource<HDTicket>({
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
    });
  }
  return ticketMap[ticketId];
};
