import type { Page } from "@playwright/test";
import type { Api } from "./api";
import { uid } from "./factories";

/** A contact with one primary email and no user. */
export async function createContact(api: Api, firstName: string) {
  const email = `e2e-${firstName.toLowerCase()}-${uid()}@example.com`;
  const contact = await api.insert("Contact", {
    first_name: firstName,
    email_ids: [{ email_id: email, is_primary: 1 }],
  });
  return { name: contact.name as string, email };
}

/** A contact linked to a website user, which a customer adds without an invite. */
export async function createContactWithUser(api: Api, firstName: string) {
  const contact = await createContact(api, firstName);
  await api.insert("User", { email: contact.email, first_name: firstName, send_welcome_email: 0 });
  await api.update("Contact", contact.name, { user: contact.email });
  return contact;
}

/** A customer whose members are the given contacts. */
export async function createCustomer(api: Api, contacts: { name: string; isManager?: boolean }[] = []) {
  const name = `E2E Customer ${uid()}`;
  await api.insert("HD Customer", {
    customer_name: name,
    contacts: contacts.map((c) => ({ contact_name: c.name, is_manager: c.isManager ? 1 : 0 })),
  });
  return name;
}

export function customerUrl(name: string) {
  return `/helpdesk/customers/${encodeURIComponent(name)}`;
}

export function contactUrl(name: string) {
  return `/helpdesk/contacts/${encodeURIComponent(name)}`;
}

/** The "more" menu beside a customer or contact page's Edit button. */
export function pageMenu(page: Page) {
  return page.getByRole("button", { name: "Edit" }).locator("..").getByRole("button").last();
}
