import type { Recipient } from "@framework/ui/components/Composer/index.ts";
import { call, frappeRequest } from "frappe-ui";
import type { Ref } from "vue";

// Bare addresses and the `Name <email>` form the timeline hands over.
function toRecipient(address: string): Recipient {
  const match = address.match(/^\s*"?([^"<]*?)"?\s*<([^>]+)>\s*$/);
  if (!match) return { email: address.trim() };
  const label = match[1].trim();
  return { email: match[2].trim(), ...(label && { label }) };
}

export function toRecipientList(
  addresses: (string | undefined)[] = []
): Recipient[] {
  return addresses.filter((a): a is string => !!a).map(toRecipient);
}

// Seeds arrive as bare addresses; a Contact with that address names the chip.
// One indexed query covers every list at once; answers are kept per address
// for the session, misses included, so a reopen or a repeat reply is instant.
const contactByEmail = new Map<string, Recipient | null>();

export async function nameRecipients(...lists: Ref<Recipient[]>[]) {
  const bare = lists.flatMap((list) => list.value).filter((r) => !r.label);
  const unknown = [
    ...new Set(bare.map((r) => r.email).filter((e) => !contactByEmail.has(e))),
  ];
  if (unknown.length) {
    const contacts = await call<
      { email_id: string; full_name?: string; name: string; image?: string }[]
    >("frappe.client.get_list", {
      doctype: "Contact",
      fields: ["email_id", "full_name", "name", "image"],
      filters: { email_id: ["in", unknown] },
      limit_page_length: unknown.length,
    }).catch(() => []);
    for (const email of unknown) contactByEmail.set(email, null);
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
