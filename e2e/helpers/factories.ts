import type { Api } from "./api";

/** Raise a ticket the way the portal does, so the customer owns it. */
export async function raiseTicket(customer: Api, subject = `E2E ticket ${uid()}`) {
  return customer.call("helpdesk.helpdesk.doctype.hd_ticket.api.new", {
    doc: { subject, description: `<p>${subject} description</p>` },
  });
}

/** Short unique suffix so specs never collide with each other or old runs. */
export function uid() {
  return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}
