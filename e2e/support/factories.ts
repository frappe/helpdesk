import type { Api } from "./api";
import { uid } from "./fixtures";

/** Raise a ticket the way the portal does, so the customer owns it. */
export async function raiseTicket(customer: Api, subject = `E2E ticket ${uid()}`) {
  return customer.call("helpdesk.helpdesk.doctype.hd_ticket.api.new", {
    doc: { subject, description: `<p>${subject} description</p>` },
  });
}
