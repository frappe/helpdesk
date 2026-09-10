import type { Recipient } from "@framework/ui/components/Composer/index.ts";
import { call, frappeRequest } from "frappe-ui";
import type { Ref } from "vue";

// helpers to convert weird formatted mail addresses in the type Recipent
function toRecipient(address: string): Recipient {
  const match = address.match(/^\s*"?([^"<]*?)"?\s*<([^>]+)>\s*$/);
  if (!match) return { email: address.trim() };
  const label = match[1].trim();
  return { email: match[2].trim(), ...(label && { label }) };
}

// helper to prepare a list of recipients for mails recived ex. r@x.io becomes { email }, Riya Kapoor <r@x.io>  "Kapoor, Riya" <r@x.io> { "name", email}
// then export the formatted list
export function toRecipientList(
  addresses: (string | undefined)[] = []
): Recipient[] {
  return addresses.filter((a): a is string => !!a).map(toRecipient);
}


const contactByEmail = new Map<string, Recipient | null>();


// get contact list for and fill names from Contacts for chips that have none
export async function nameRecipients(...lists: Ref<Recipient[]>[]) {
  // get recipients which have missing labels
  const bare = lists.flatMap((list) => list.value).filter((r) => !r.label);
  const unknownContacts = [
    ...new Set(bare.map((r) => r.email).filter((e) => !contactByEmail.has(e))),
  ];
  if (unknownContacts.length) {
    const contacts = await call<
      { email_id: string; full_name?: string; name: string; image?: string }[]
    >("frappe.client.get_list", {
      doctype: "Contact",
      fields: ["email_id", "full_name", "name", "image"],
      filters: { email_id: ["in", unknownContacts] },
      limit_page_length: unknownContacts.length,
    }).catch(() => []);
    for (const email of unknownContacts) contactByEmail.set(email, null);
    for (const c of contacts) {
      contactByEmail.set(c.email_id, {
        email: c.email_id,
        label: c.full_name || c.name,
        image: c.image,
      });
    }
  }
  for (const list of lists) {
    list.value = list.value.map((r) =>
      r.label ? r : contactByEmail.get(r.email) ?? r
    );
  }
}

// Plain request, not createResource: RecipientSelect evaluates this inside a
// computedAsync, and touching a reactive resource there re-triggers evaluation
// forever.
export async function searchRecipients(query: string): Promise<Recipient[]> {
  const contacts = await frappeRequest<
    { full_name?: string; name: string; email_id: string }[]
  >({
    url: "/api/method/helpdesk.api.contact.search_contacts",
    method: "GET",
    params: { txt: query },
  });
  return (contacts ?? []).map((contact) => ({
    email: contact.email_id,
    label: contact.full_name || contact.name || contact.email_id,
  }));
}
